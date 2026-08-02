from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.middleware.rate_limit import rate_limit
from app.models.channel import Channel
from app.models.series import Series
from app.models.user import User
from app.models.video import Video
from app.services.niches import VALID_CATEGORIES
from app.services.voices import VALID_VOICE_IDS

router = APIRouter(prefix="/series", tags=["Series"], dependencies=[Depends(get_current_user)])

VALID_INTERVALS = {24, 48, 168}  # daily, every 2 days, weekly
VALID_STYLES = {"viral_story", "news_update", "educational", "commentary"}
VALID_OUTPUT_TYPES = {"narrated", "visual"}
VALID_PRIVACY = {"public", "unlisted", "private"}
MAX_ACTIVE_SERIES = 3  # per user, until billing exists


def _valid_series_formats() -> set:
    """Formats a series can run on autopilot: video-producing only —
    image carousels can't be auto-published to YouTube."""
    from app.services.formats import FORMATS

    return {k for k, f in FORMATS.items()
            if f["available"] and f["output_type"] in ("narrated", "visual", "fake_text")}


class SeriesCreate(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    category: Optional[str] = None
    topic_prompt: Optional[str] = Field(default=None, max_length=300)
    # format = full pipeline recipe for every run; None = custom style/output_type
    format: Optional[str] = None
    style: str = "viral_story"
    output_type: str = "narrated"
    language: str = "English"
    voice_id: Optional[str] = None
    interval_hours: int = 24
    auto_publish: bool = False
    channel_id: Optional[UUID] = None
    publish_privacy: str = "unlisted"


class SeriesUpdate(BaseModel):
    is_active: Optional[bool] = None
    name: Optional[str] = Field(default=None, min_length=2, max_length=80)
    topic_prompt: Optional[str] = Field(default=None, max_length=300)
    interval_hours: Optional[int] = None
    auto_publish: Optional[bool] = None
    channel_id: Optional[UUID] = None
    publish_privacy: Optional[str] = None


class SeriesResponse(BaseModel):
    id: UUID
    name: str
    category: Optional[str]
    topic_prompt: Optional[str]
    format: Optional[str] = None
    style: str
    output_type: str
    language: str
    voice_id: Optional[str]
    interval_hours: int
    auto_publish: bool
    channel_id: Optional[UUID]
    publish_privacy: str
    is_active: bool
    last_run_at: Optional[datetime]
    next_run_at: Optional[datetime]
    last_error: Optional[str]
    video_count: int = 0
    model_config = ConfigDict(from_attributes=True)


def _validate(req: SeriesCreate):
    if req.category is not None and req.category not in VALID_CATEGORIES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Unknown category")
    if req.format is not None and req.format not in _valid_series_formats():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Unknown format, or this format can't run as a series",
        )
    if req.style not in VALID_STYLES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Unknown style")
    if req.output_type not in VALID_OUTPUT_TYPES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Series supports narrated or visual")
    if req.interval_hours not in VALID_INTERVALS:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Interval must be 24, 48 or 168 hours")
    if req.voice_id and req.voice_id not in VALID_VOICE_IDS:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Unknown voice")
    if req.publish_privacy not in VALID_PRIVACY:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Invalid privacy")


async def _with_counts(db: AsyncSession, items: list[Series]) -> list[SeriesResponse]:
    out = []
    for s in items:
        count = await db.scalar(select(func.count(Video.id)).where(Video.series_id == s.id))
        resp = SeriesResponse.model_validate(s)
        resp.video_count = count or 0
        out.append(resp)
    return out


@router.get("", response_model=list[SeriesResponse])
async def list_series(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items = (
        await db.execute(
            select(Series).where(Series.user_id == current_user.id).order_by(Series.created_at.desc())
        )
    ).scalars().all()
    return await _with_counts(db, items)


@router.post("", response_model=SeriesResponse, dependencies=[Depends(rate_limit("series_create"))])
async def create_series(
    req: SeriesCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _validate(req)
    active = await db.scalar(
        select(func.count(Series.id)).where(Series.user_id == current_user.id, Series.is_active == True)  # noqa: E712
    )
    if (active or 0) >= MAX_ACTIVE_SERIES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Maximum {MAX_ACTIVE_SERIES} active series for now — pause one first",
        )
    if req.auto_publish:
        if req.channel_id is None:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Auto-publish needs a channel")
        channel = await db.get(Channel, req.channel_id)
        if channel is None or channel.user_id != current_user.id or not channel.is_active:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channel not connected")

    series = Series(
        user_id=current_user.id,
        **req.model_dump(),
        next_run_at=datetime.now(timezone.utc),  # first video on the next tick (≤15 min)
    )
    db.add(series)
    await db.commit()
    await db.refresh(series)
    resp = SeriesResponse.model_validate(series)
    return resp


@router.patch("/{series_id}", response_model=SeriesResponse)
async def update_series(
    series_id: UUID,
    req: SeriesUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    series = await db.get(Series, series_id)
    if series is None or series.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Series not found")
    data = req.model_dump(exclude_unset=True)
    if "interval_hours" in data and data["interval_hours"] not in VALID_INTERVALS:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Interval must be 24, 48 or 168 hours")
    if "publish_privacy" in data and data["publish_privacy"] not in VALID_PRIVACY:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Invalid privacy")
    for k, v in data.items():
        setattr(series, k, v)
    if data.get("is_active") and series.next_run_at is None:
        series.next_run_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(series)
    return (await _with_counts(db, [series]))[0]


@router.delete("/{series_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_series(
    series_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    series = await db.get(Series, series_id)
    if series is None or series.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Series not found")
    # Videos keep existing; they just lose the series link on delete
    videos = (await db.execute(select(Video).where(Video.series_id == series.id))).scalars().all()
    for v in videos:
        v.series_id = None
    await db.delete(series)
    await db.commit()


@router.post("/{series_id}/run-now")
async def run_now(
    series_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger one series run (also used for testing)."""
    series = await db.get(Series, series_id)
    if series is None or series.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Series not found")
    from app.pipeline.series_tasks import run_series_once

    series.last_run_at = datetime.now(timezone.utc)
    await db.commit()
    run_series_once.delay(str(series.id))
    return {"status": "dispatched"}
