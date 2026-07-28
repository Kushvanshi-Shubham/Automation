"""Pipeline orchestration: script → voice → visuals → assembly → done.

Runs inside a Celery worker via asyncio.run (see tasks.py) but is plain async
code, so tests and manual runs can call it directly.
"""
import logging
import random
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

import httpx

from app.config import settings
from app.database import AsyncSessionLocal
from app.models.credit import CreditLedger
from app.models.pipeline_job import PipelineJob
from app.models.user import User
from app.models.video import Video
from app.pipeline import assembler, captions, tts
from app.pipeline.visuals import pexels
from app.services.progress import publish_progress

logger = logging.getLogger("kliptos.runner")

MUSIC_DIR = Path(__file__).resolve().parent.parent.parent / "assets" / "music"


def _pick_music() -> Path | None:
    if not MUSIC_DIR.is_dir():
        return None
    tracks = sorted(MUSIC_DIR.glob("*.mp3"))
    return random.choice(tracks) if tracks else None


def _music_attribution(track: Path) -> str | None:
    """CC-BY tracks (naming convention <title>_kevin_macleod_ccby.mp3) must be credited."""
    stem = track.stem
    if stem.endswith("_kevin_macleod_ccby"):
        title = stem.removesuffix("_kevin_macleod_ccby").replace("_", " ").title()
        return (
            f'Music: "{title}" Kevin MacLeod (incompetech.com), '
            "Licensed under Creative Commons: By Attribution 4.0"
        )
    return None


def _publish(job_id: str, status: str, stage: str, percent: float, error: str | None = None):
    try:
        publish_progress(job_id, status=status, stage=stage, percent=percent, error=error)
    except Exception as exc:  # progress must never kill a render
        logger.warning("progress publish failed (%s): %s", stage, exc)


async def run(job_id: str) -> dict:
    job_uuid = UUID(str(job_id))
    async with AsyncSessionLocal() as db:
        job = await db.get(PipelineJob, job_uuid)
        if job is None:
            raise RuntimeError(f"pipeline job {job_id} not found")

        video = await db.get(Video, job.video_id)
        segments = (video.script_data or {}).get("segments") or []
        if not segments:
            raise RuntimeError("video has no script segments")

        job.status = "running"
        job.started_at = datetime.now(timezone.utc)
        video.status = "rendering"
        await db.commit()

    job_key = str(job_id)
    out_dir = Path(settings.OUTPUT_DIR) / str(video.id)
    out_dir.mkdir(parents=True, exist_ok=True)
    workdir = Path(tempfile.mkdtemp(prefix="kliptos_"))

    try:
        # Stage 1: voice
        _publish(job_key, "running", "voice", 10)
        voiced = await tts.synth_script(segments, workdir)

        # Stage 2: visuals
        _publish(job_key, "running", "visuals", 35)
        used_ids: set[int] = set()
        clips = []
        async with httpx.AsyncClient(timeout=60) as client:
            for i, seg in enumerate(segments):
                clip_path = workdir / f"clip_{i:02d}.mp4"
                query = seg.get("visual_prompt") or seg["text"]
                await pexels.fetch_clip(client, query, clip_path, used_ids)
                clips.append(clip_path)
                _publish(job_key, "running", "visuals", 35 + (i + 1) / len(segments) * 25)

        # Stage 3: assembly (with burned-in captions)
        _publish(job_key, "running", "assembly", 65)
        rendered = []
        for i, (seg_audio, clip) in enumerate(zip(voiced, clips)):
            seg_out = workdir / f"final_{i:02d}.mp4"
            ass_path = captions.build_segment_captions(
                words=seg_audio.get("words") or [],
                text=segments[i]["text"],
                duration=seg_audio["duration"],
                out_path=workdir / f"cap_{i:02d}.ass",
            )
            assembler.render_segment(
                clip, Path(seg_audio["audio_path"]), seg_audio["duration"], seg_out, ass_path=ass_path
            )
            rendered.append(seg_out)
            _publish(job_key, "running", "assembly", 65 + (i + 1) / len(segments) * 20)

        concat_path = workdir / "concat_full.mp4"
        assembler.concat_segments(rendered, concat_path, workdir)

        # Stage 4: background music (skipped when the library is empty)
        final_path = out_dir / "final.mp4"
        music = _pick_music()
        attribution = None
        if music is not None:
            _publish(job_key, "running", "music", 90)
            assembler.mix_music(concat_path, music, final_path)
            attribution = _music_attribution(music)
            logger.info("mixed music track: %s", music.name)
        else:
            shutil.move(str(concat_path), str(final_path))
        duration = assembler.probe_duration(final_path)

        # Stage 5: persist
        async with AsyncSessionLocal() as db:
            job = await db.get(PipelineJob, job_uuid)
            video = await db.get(Video, job.video_id)
            video.status = "ready"
            video.video_url = f"/media/{video.id}/final.mp4"
            if attribution and attribution not in (video.description or ""):
                video.description = f"{video.description or ''}\n\n{attribution}".strip()
            job.status = "completed"
            job.completed_at = datetime.now(timezone.utc)
            job.progress = {"stage": "completed", "percent": 100, "duration": duration}
            await db.commit()

        _publish(job_key, "completed", "completed", 100)
        logger.info("render complete: %s (%.1fs)", final_path, duration)
        return {"video_url": f"/media/{video.id}/final.mp4", "duration": duration}

    except Exception as exc:
        logger.exception("pipeline failed for job %s", job_key)
        async with AsyncSessionLocal() as db:
            job = await db.get(PipelineJob, job_uuid)
            video = await db.get(Video, job.video_id)
            user = await db.get(User, job.user_id)
            job.status = "failed"
            job.error_message = str(exc)[:2000]
            job.completed_at = datetime.now(timezone.utc)
            video.status = "failed"
            # Refund the render credit — failed renders must not cost the user.
            refund = video.credits_used or 1
            user.credit_balance += refund
            db.add(CreditLedger(user_id=user.id, amount=refund, type="refund",
                                description="Render failed — automatic refund", video_id=video.id))
            await db.commit()
        _publish(job_key, "failed", "failed", 0, error=str(exc)[:300])
        raise
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
