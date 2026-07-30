"""Celery task: publish a rendered video to Instagram as a Reel."""
import asyncio
import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.ig_account import IgAccount
from app.models.publish import Publish
from app.models.video import Video
from app.pipeline.celery_app import celery_app
from app.services import instagram

logger = logging.getLogger("kliptos.ig_upload")


async def _run(publish_id: str) -> dict:
    async with AsyncSessionLocal() as db:
        publish = await db.get(Publish, UUID(publish_id))
        if publish is None:
            raise RuntimeError("publish record not found")
        video = await db.get(Video, publish.video_id)
        account = (
            await db.execute(
                select(IgAccount).where(
                    IgAccount.user_id == publish.user_id, IgAccount.is_active == True  # noqa: E712
                )
            )
        ).scalars().first()
        if account is None:
            raise RuntimeError("no active Instagram account")
        caption = publish.caption or ""
        video_url = f"{instagram.media_public_base()}{video.video_url}"

    try:
        media_id = await asyncio.to_thread(instagram.publish_reel, account, video_url, caption)
    except Exception as exc:
        async with AsyncSessionLocal() as db:
            publish = await db.get(Publish, UUID(publish_id))
            publish.status = "failed"
            publish.error_message = str(exc)[:2000]
            await db.commit()
        raise

    async with AsyncSessionLocal() as db:
        publish = await db.get(Publish, UUID(publish_id))
        publish.status = "published"
        publish.external_id = media_id
        publish.published_at = datetime.now(timezone.utc)
        await db.commit()
    return {"ig_media_id": media_id}


@celery_app.task(bind=True, name="instagram.publish")
def ig_publish_task(self, publish_id: str):
    from app.pipeline.tasks import _with_fresh_pool

    return asyncio.run(_with_fresh_pool(_run(publish_id)))
