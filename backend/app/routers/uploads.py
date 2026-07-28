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
from app.models.user import User
from app.models.video import Video
from app.schemas.video import VideoResponse

router = APIRouter(prefix="/uploads", tags=["Uploads"], dependencies=[Depends(get_current_user)])

ALLOWED_PRIVACY = {"public", "unlisted", "private"}


class PublishRequest(BaseModel):
    channel_id: UUID
    privacy: str = "unlisted"


class ScheduleRequest(BaseModel):
    channel_id: UUID
    publish_at: datetime


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
    video, channel = await _validate(video_id, req.channel_id, db, current_user)

    from app.pipeline.upload_tasks import upload_video_task
    upload_video_task.delay(str(video.id), str(channel.id), req.privacy, None)
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
    video, channel = await _validate(video_id, req.channel_id, db, current_user)

    from app.pipeline.upload_tasks import upload_video_task
    upload_video_task.delay(str(video.id), str(channel.id), "private", publish_at.isoformat())
    return {"status": "scheduling"}


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
