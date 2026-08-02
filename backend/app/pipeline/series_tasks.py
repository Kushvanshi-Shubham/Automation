"""Series autopilot: the scheduler tick and per-series creation run.

series.tick fires from Celery beat every 15 minutes, finds due series, and
advances their next_run_at IMMEDIATELY (so a slow run can't double-fire).
series.run_one does one full creation: pick topic → script → deduct credit →
render (→ optionally chain a YouTube publish).
"""
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from celery import chain
from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.channel import Channel
from app.models.credit import CreditLedger
from app.models.pipeline_job import PipelineJob
from app.models.series import Series
from app.models.topic import Topic
from app.models.user import User
from app.models.video import Video
from app.pipeline.celery_app import celery_app

logger = logging.getLogger("kliptos.series")

SERIES_RENDER_COST = 1


async def _tick() -> int:
    """Dispatch every due series; returns how many were dispatched."""
    now = datetime.now(timezone.utc)
    async with AsyncSessionLocal() as db:
        due = (
            await db.execute(
                select(Series).where(
                    Series.is_active == True,  # noqa: E712
                    (Series.next_run_at == None) | (Series.next_run_at <= now),  # noqa: E711
                )
            )
        ).scalars().all()
        for s in due:
            s.last_run_at = now
            s.next_run_at = now + timedelta(hours=s.interval_hours)
        await db.commit()
        ids = [str(s.id) for s in due]

    for sid in ids:
        run_series_once.delay(sid)
    if ids:
        logger.info("series tick dispatched %d run(s)", len(ids))
    return len(ids)


async def _run_one(series_id: str) -> dict:
    from app.services import script_gen
    from app.services.user_keys import get_user_keys

    async with AsyncSessionLocal() as db:
        series = await db.get(Series, UUID(series_id))
        if series is None or not series.is_active:
            return {"skipped": "inactive"}
        user = await db.get(User, series.user_id)

        if user.credit_balance < SERIES_RENDER_COST:
            series.last_error = "Paused run: not enough credits"
            await db.commit()
            logger.info("series %s skipped: no credits", series.name)
            return {"skipped": "no_credits"}

        # Previous subjects in this series → variety guard
        prev_videos = (
            await db.execute(
                select(Video).where(Video.series_id == series.id).order_by(Video.created_at.desc()).limit(10)
            )
        ).scalars().all()
        prev_subjects = [
            (v.script_data or {}).get("subject") or (v.title or "") for v in prev_videos
        ]

        # Topic selection: explicit theme beats trend picking
        if series.topic_prompt:
            subject = series.topic_prompt
            hook_hint = None
        else:
            q = select(Topic).order_by(Topic.score.desc()).limit(30)
            if series.category:
                q = q.where(Topic.category == series.category)
            topics = (await db.execute(q)).scalars().all()
            fresh = [t for t in topics if t.title not in prev_subjects]
            if not fresh:
                series.last_error = "No fresh trending topics found — refresh topics or set a theme"
                await db.commit()
                return {"skipped": "no_topics"}
            subject = fresh[0].title
            hook_hint = fresh[0].hook_text

        user_keys = await get_user_keys(db, user.id)

    variety_note = (
        "This video is part of the ongoing series "
        f"'{series.name}'. Avoid repeating these previous videos: {'; '.join(s for s in prev_subjects if s)[:600]}"
        if prev_subjects else None
    )

    # A format is the run's full pipeline recipe — derived at RUN time so
    # recipe improvements apply to every future episode automatically.
    from app.services.formats import FORMATS, render_defaults

    fmt = FORMATS.get(series.format) if series.format else None
    style = fmt["style"] if fmt else series.style
    output_type = fmt["output_type"] if fmt else series.output_type
    language = series.language
    if fmt and fmt.get("language") and language == "English":
        language = fmt["language"]

    instructions = [variety_note] if variety_note else []
    if output_type == "visual":
        from app.routers.scripts import VISUAL_TYPE_NOTE

        instructions.insert(0, VISUAL_TYPE_NOTE)
    if fmt and fmt.get("script_recipe"):
        instructions.insert(0, fmt["script_recipe"])

    script = await script_gen.generate_script(
        topic=subject,
        hook_hint=hook_hint,
        style=style,
        language=language,
        custom_instructions="\n".join(instructions) or None,
        user_keys=user_keys,
    )

    async with AsyncSessionLocal() as db:
        series = await db.get(Series, UUID(series_id))
        user = await db.get(User, series.user_id)

        script_data = {
            "subject": subject,
            "style": style,
            "segments": script["segments"],
            "total_duration": script["total_duration"],
        }
        if fmt is not None:
            script_data["format"] = series.format
            script_data.update(render_defaults(fmt))
        # An explicit series voice beats the format's default.
        if series.voice_id:
            script_data["voice_id"] = series.voice_id

        video = Video(
            user_id=user.id,
            series_id=series.id,
            status="script_ready",
            output_type=output_type,
            title=script.get("title"),
            description=script.get("description"),
            tags=script.get("tags"),
            visual_engine="pexels",
            credits_used=SERIES_RENDER_COST,
            script_data=script_data,
        )
        db.add(video)
        await db.flush()

        user.credit_balance -= SERIES_RENDER_COST
        db.add(CreditLedger(user_id=user.id, amount=-SERIES_RENDER_COST, type="video_debit",
                            description=f"Series render: {series.name}", video_id=video.id))

        job = PipelineJob(video_id=video.id, user_id=user.id, status="queued",
                          progress={"stage": "queued", "percent": 0})
        db.add(job)
        await db.flush()

        series.last_error = None
        video_id, job_id = str(video.id), str(job.id)

        # Auto-publish only with a healthy channel
        publish_channel = None
        if series.auto_publish and series.channel_id:
            channel = await db.get(Channel, series.channel_id)
            if channel is not None and channel.is_active and channel.refresh_token:
                publish_channel = str(channel.id)
            else:
                series.last_error = "Auto-publish skipped: channel not connected"

        await db.commit()

    from app.pipeline.tasks import run_pipeline
    if publish_channel:
        from app.pipeline.upload_tasks import upload_video_task

        chain(
            run_pipeline.si(job_id),
            upload_video_task.si(video_id, publish_channel, series.publish_privacy, None, "24"),
        ).delay()
    else:
        run_pipeline.delay(job_id)

    logger.info("series '%s' created video %s (%s)", series.name, video_id,
                "auto-publish" if publish_channel else "review")
    return {"video_id": video_id, "auto_publish": bool(publish_channel)}


@celery_app.task(name="series.tick")
def series_tick():
    from app.pipeline.tasks import _with_fresh_pool

    return asyncio.run(_with_fresh_pool(_tick()))


@celery_app.task(bind=True, name="series.run_one")
def run_series_once(self, series_id: str):
    from app.pipeline.tasks import _with_fresh_pool

    return asyncio.run(_with_fresh_pool(_run_one(series_id)))
