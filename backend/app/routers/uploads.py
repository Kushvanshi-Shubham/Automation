from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.channel import Channel
from app.models.ig_account import IgAccount
from app.models.publish import Publish
from app.models.user import User
from app.models.video import Video
from app.schemas.video import VideoResponse
from app.services import instagram
from app.services.youtube import YT_CATEGORIES

router = APIRouter(prefix="/uploads", tags=["Uploads"], dependencies=[Depends(get_current_user)])

ALLOWED_PRIVACY = {"public", "unlisted", "private"}


class PublishRequest(BaseModel):
    channel_id: UUID
    privacy: str = "unlisted"
    category_id: str = "24"


class ScheduleRequest(BaseModel):
    channel_id: UUID
    publish_at: datetime
    category_id: str = "24"


@router.get("/categories")
async def list_yt_categories():
    """Assignable YouTube categories for the publish form."""
    return {"items": [{"id": k, "label": v} for k, v in YT_CATEGORIES.items()]}


async def _validate(video_id: UUID, channel_id: UUID, db: AsyncSession, user: User) -> tuple[Video, Channel]:
    video = await db.get(Video, video_id)
    if video is None or video.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")
    if video.status not in ("ready", "upload_failed"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Video is not ready to publish (status: {video.status})",
        )
    if not (Path(settings.OUTPUT_DIR) / str(video.id) / "final.mp4").exists():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Rendered file missing")

    channel = await db.get(Channel, channel_id)
    if channel is None or channel.user_id != user.id or not channel.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channel not connected")
    if not channel.refresh_token:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Channel has no refresh token — reconnect it in Settings",
        )
    return video, channel


@router.post("/{video_id}/publish")
async def publish_video(
    video_id: UUID,
    req: PublishRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload to YouTube now."""
    if req.privacy not in ALLOWED_PRIVACY:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Invalid privacy value")
    if req.category_id not in YT_CATEGORIES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Invalid category")
    video, channel = await _validate(video_id, req.channel_id, db, current_user)

    from app.pipeline.upload_tasks import upload_video_task
    upload_video_task.delay(str(video.id), str(channel.id), req.privacy, None, req.category_id)
    return {"status": "publishing"}


@router.post("/{video_id}/schedule")
async def schedule_video(
    video_id: UUID,
    req: ScheduleRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload now as private with a YouTube-managed go-live time."""
    publish_at = req.publish_at
    if publish_at.tzinfo is None:
        publish_at = publish_at.replace(tzinfo=timezone.utc)
    if publish_at <= datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="publish_at must be in the future")
    if req.category_id not in YT_CATEGORIES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Invalid category")
    video, channel = await _validate(video_id, req.channel_id, db, current_user)

    from app.pipeline.upload_tasks import upload_video_task
    upload_video_task.delay(str(video.id), str(channel.id), "private", publish_at.isoformat(), req.category_id)
    return {"status": "scheduling"}


class IgPublishRequest(BaseModel):
    caption: str = ""


@router.post("/{video_id}/publish-instagram")
async def publish_instagram(
    video_id: UUID,
    req: IgPublishRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Publish a rendered short to Instagram as a Reel (official Graph API)."""
    if not instagram.enabled():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Instagram publishing is not configured yet",
        )
    video = await db.get(Video, video_id)
    if video is None or video.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")
    if video.status not in ("ready", "published", "scheduled"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Video is not rendered yet (status: {video.status})",
        )
    if not (Path(settings.OUTPUT_DIR) / str(video.id) / "final.mp4").exists():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Rendered file missing")

    account = (
        await db.execute(
            select(IgAccount).where(IgAccount.user_id == current_user.id, IgAccount.is_active == True)  # noqa: E712
        )
    ).scalars().first()
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No Instagram account connected")

    caption = req.caption.strip() or f"{video.title or ''}\n\n{video.description or ''}".strip()
    publish = Publish(video_id=video.id, user_id=current_user.id, platform="instagram",
                      status="publishing", caption=caption[:2200])
    db.add(publish)
    await db.flush()
    publish_id = publish.id
    await db.commit()

    from app.pipeline.ig_upload_tasks import ig_publish_task
    ig_publish_task.delay(str(publish_id))
    return {"status": "publishing", "publish_id": publish_id}


@router.get("/publishes/{video_id}")
async def list_publishes(
    video_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Multi-platform publish history for one video."""
    result = await db.execute(
        select(Publish).where(Publish.video_id == video_id, Publish.user_id == current_user.id)
        .order_by(Publish.created_at.desc())
    )
    return {
        "items": [
            {"id": p.id, "platform": p.platform, "status": p.status,
             "external_id": p.external_id, "error_message": p.error_message,
             "published_at": p.published_at}
            for p in result.scalars().all()
        ]
    }


@router.get("", response_model=list[VideoResponse])
async def list_uploads(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Videos in the publish lifecycle (publishing/scheduled/published/upload_failed)."""
    result = await db.execute(
        select(Video)
        .where(
            Video.user_id == current_user.id,
            Video.status.in_(["publishing", "scheduled", "published", "upload_failed"]),
        )
        .order_by(Video.updated_at.desc().nullslast(), Video.created_at.desc())
        .limit(100)
    )
    return result.scalars().all()
