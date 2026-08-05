"""Stale-job reaper: never leave a creator with a spent credit and a
frozen progress bar.

A job can stall for reasons the API can't see — no worker connected, the
worker died mid-render, the queue was flushed. Every tick, jobs that have
been queued or running for longer than STALE_AFTER_MINUTES are failed,
the credit is refunded, and the video returns to script_ready so it can
simply be rendered again.
"""
import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import or_, select

from app.database import AsyncSessionLocal
from app.models.credit import CreditLedger
from app.models.pipeline_job import PipelineJob
from app.models.user import User
from app.models.video import Video
from app.pipeline.celery_app import celery_app
from app.services.progress import publish_progress

logger = logging.getLogger("kliptos.reaper")

# Generous: a long narrated render with slow stock downloads can take a
# few minutes, and a cold worker adds startup time.
STALE_AFTER_MINUTES = 30


async def _run() -> dict:
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=STALE_AFTER_MINUTES)
    reaped = 0

    async with AsyncSessionLocal() as db:
        rows = (
            await db.execute(
                select(PipelineJob)
                .join(Video, Video.id == PipelineJob.video_id)
                .where(
                    PipelineJob.status.in_(["queued", "running"]),
                    # started_at is set when a worker picks it up; a job that
                    # was never picked up is dated by its video instead.
                    or_(
                        PipelineJob.started_at < cutoff,
                        PipelineJob.started_at.is_(None) & (Video.created_at < cutoff),
                    ),
                )
                .limit(50)
            )
        ).scalars().all()

        for job in rows:
            video = await db.get(Video, job.video_id)
            user = await db.get(User, job.user_id)
            refund = (video.credits_used or 0) if video else 0

            job.status = "failed"
            job.error_message = (
                f"No worker finished this render within {STALE_AFTER_MINUTES} minutes — "
                "your credit was returned. Try rendering again."
            )
            job.completed_at = datetime.now(timezone.utc)
            job.progress = {"stage": "failed", "percent": 0}
            if video is not None and video.status == "rendering":
                video.status = "script_ready"
            if user is not None and refund:
                user.credit_balance += refund
                db.add(CreditLedger(
                    user_id=user.id, amount=refund, type="refund",
                    description="Render timed out — automatic refund", video_id=job.video_id,
                ))
                if video is not None:
                    video.credits_used = 0
            reaped += 1

            try:
                publish_progress(str(job.id), status="failed", stage="failed", percent=0,
                                 error=job.error_message)
            except Exception:
                pass

        if reaped:
            await db.commit()

    if reaped:
        logger.warning("reaped %d stale render job(s)", reaped)
    return {"reaped": reaped}


@celery_app.task(bind=True, name="pipeline.reap_stale")
def reap_stale_jobs(self):
    from app.pipeline.tasks import _with_fresh_pool

    return asyncio.run(_with_fresh_pool(_run()))
