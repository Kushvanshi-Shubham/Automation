"""Celery task: upload a rendered video to YouTube."""
import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from app.config import settings
from app.database import AsyncSessionLocal
from app.models.channel import Channel
from app.models.video import Video
from app.pipeline.celery_app import celery_app
from app.services import youtube

logger = logging.getLogger("kliptos.upload")


async def _run(video_id: str, channel_id: str, privacy: str, publish_at: str | None) -> dict:
    async with AsyncSessionLocal() as db:
        video = await db.get(Video, UUID(video_id))
        channel = await db.get(Channel, UUID(channel_id))
        if video is None or channel is None:
            raise RuntimeError("video or channel not found")
        video.status = "publishing"
        await db.commit()

    file_path = Path(settings.OUTPUT_DIR) / video_id / "final.mp4"

    try:
        yt_id = await asyncio.to_thread(
            youtube.upload_video_file,
            channel,
            file_path,
            video.title or "Untitled Short",
            video.description or "",
            video.tags,
            privacy,
            publish_at,
        )
    except Exception as exc:
        logger.exception("upload failed for video %s", video_id)
        async with AsyncSessionLocal() as db:
            video = await db.get(Video, UUID(video_id))
            video.status = "upload_failed"
            await db.commit()
        raise

    async with AsyncSessionLocal() as db:
        video = await db.get(Video, UUID(video_id))
        video.youtube_video_id = yt_id
        video.channel_id = UUID(channel_id)
        if publish_at:
            video.status = "scheduled"
            video.scheduled_at = datetime.fromisoformat(publish_at.replace("Z", "+00:00"))
        else:
            video.status = "published"
            video.published_at = datetime.now(timezone.utc)
        await db.commit()

    return {"youtube_video_id": yt_id}


@celery_app.task(bind=True, name="youtube.upload")
def upload_video_task(self, video_id: str, channel_id: str, privacy: str = "unlisted", publish_at: str | None = None):
    from app.pipeline.tasks import _with_fresh_pool

    return asyncio.run(_with_fresh_pool(_run(video_id, channel_id, privacy, publish_at)))
