"""Celery task: process an uploaded creator asset (probe → transcribe → highlights)."""
import asyncio
import logging
from pathlib import Path
from uuid import UUID

from app.database import AsyncSessionLocal
from app.models.asset import Asset
from app.pipeline.celery_app import celery_app

logger = logging.getLogger("kliptos.asset")


async def _run(asset_id: str) -> dict:
    import tempfile

    from app.pipeline import transcribe
    from app.pipeline.assembler import probe_duration
    from app.services import storage
    from app.services.user_keys import get_user_keys

    async with AsyncSessionLocal() as db:
        asset = await db.get(Asset, UUID(asset_id))
        if asset is None:
            raise RuntimeError("asset not found")
        asset.status = "processing"
        await db.commit()
        path_ref = asset.path
        user_id = asset.user_id

    workdir = Path(tempfile.mkdtemp(prefix="kliptos_asset_"))
    try:
        # Local disk path in dev; bucket key in the cloud (API and worker
        # are separate machines there) — resolve to a local file either way.
        path = await asyncio.to_thread(storage.resolve_source, path_ref, workdir)
        duration = probe_duration(path)
        # Whisper is CPU-bound sync work — keep it off the event loop.
        transcript = await asyncio.to_thread(transcribe.transcribe, path)

        async with AsyncSessionLocal() as db:
            user_keys = await get_user_keys(db, user_id)
        highlights = await transcribe.suggest_highlights(transcript, user_keys=user_keys)

        async with AsyncSessionLocal() as db:
            asset = await db.get(Asset, UUID(asset_id))
            asset.duration = duration
            asset.transcript = transcript
            asset.highlights = highlights
            asset.status = "ready"
            asset.error_message = None
            await db.commit()
        logger.info("asset %s ready: %.0fs, %d highlights", asset_id, duration, len(highlights))
        return {"duration": duration, "highlights": len(highlights)}
    except Exception as exc:
        logger.exception("asset processing failed: %s", asset_id)
        async with AsyncSessionLocal() as db:
            asset = await db.get(Asset, UUID(asset_id))
            asset.status = "failed"
            asset.error_message = str(exc)[:2000]
            await db.commit()
        raise
    finally:
        import shutil

        shutil.rmtree(workdir, ignore_errors=True)


@celery_app.task(bind=True, name="asset.process")
def process_asset(self, asset_id: str):
    from app.pipeline.tasks import _with_fresh_pool

    return asyncio.run(_with_fresh_pool(_run(asset_id)))
