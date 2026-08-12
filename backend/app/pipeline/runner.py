"""Pipeline orchestration: script → voice → visuals → assembly → done.

Runs inside a Celery worker via asyncio.run (see tasks.py) but is plain async
code, so tests and manual runs can call it directly.
"""
import asyncio
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
from app.pipeline.assembler import ASPECT_RATIOS
from app.pipeline.visuals import pexels
from app.services import plans
from app.services.progress import publish_progress

logger = logging.getLogger("kliptos.runner")

MUSIC_DIR = Path(__file__).resolve().parent.parent.parent / "assets" / "music"


# Filename keywords per mood; a format's music_mood narrows the pick.
MOOD_KEYWORDS = {"calm": ("wallpaper", "calm", "ambient"), "energetic": ("carefree", "upbeat", "energetic")}


def _pick_music(mood: str | None = None) -> Path | None:
    if not MUSIC_DIR.is_dir():
        return None
    tracks = sorted(MUSIC_DIR.glob("*.mp3"))
    if mood in MOOD_KEYWORDS:
        matching = [t for t in tracks if any(k in t.stem.lower() for k in MOOD_KEYWORDS[mood])]
        tracks = matching or tracks
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


async def _store_media(local_path: Path, video_id, filename: str) -> str:
    """Where the browser fetches this file from: the local /media mount in
    dev, or the object-storage public URL in the cloud (API and worker run
    on different machines there — local disk doesn't travel)."""
    from app.services import storage

    if storage.enabled():
        return await asyncio.to_thread(storage.upload, local_path, f"renders/{video_id}/{filename}")
    return f"/media/{video_id}/{filename}"


async def _resolve_asset_source(path_or_key: str, workdir: Path) -> Path:
    """A local file for creator footage, whether Asset.path is a dev-disk
    path or a bucket key. Downloads land in workdir (cleaned after render)."""
    from app.services import storage

    return await asyncio.to_thread(storage.resolve_source, path_or_key, workdir)


async def _run_image_post(job_key: str, job_uuid, video, segments: list[dict], out_dir: Path) -> dict:
    """Image-post branch: one image per slide (stock photos or AI images)."""
    from app.services import image_gen
    from app.services.user_keys import get_user_keys

    engine = video.visual_engine or "stock_image"
    orientation = ASPECT_RATIOS.get(
        (video.script_data or {}).get("aspect_ratio") or "", ASPECT_RATIOS[assembler.DEFAULT_ASPECT]
    )["orientation"]
    slides = segments[:8]
    images: list[str] = []

    if engine == "ai_image":
        async with AsyncSessionLocal() as db:
            user_keys = await get_user_keys(db, video.user_id)

    async with httpx.AsyncClient(timeout=60) as client:
        used_ids: set[int] = set()
        for i, seg in enumerate(slides):
            out_path = out_dir / f"img_{i:02d}.jpg"
            prompt = seg.get("visual_prompt") or seg["text"]
            _publish(job_key, "running", "images", 10 + i / len(slides) * 80)
            if engine == "ai_image":
                await image_gen.generate_image(prompt, out_path, user_keys=user_keys)
            elif seg.get("media_id"):  # user pinned a specific photo
                await pexels.fetch_photo_by_id(client, int(seg["media_id"]), out_path)
                used_ids.add(int(seg["media_id"]))
            else:
                await pexels.fetch_photo(client, prompt, out_path, used_ids, orientation=orientation)
            images.append(await _store_media(out_path, video.id, out_path.name))

    async with AsyncSessionLocal() as db:
        job = await db.get(PipelineJob, job_uuid)
        video_row = await db.get(Video, job.video_id)
        video_row.status = "ready"
        video_row.thumbnail_url = images[0]
        video_row.script_data = {**(video_row.script_data or {}), "images": images}
        job.status = "completed"
        job.completed_at = datetime.now(timezone.utc)
        job.progress = {"stage": "completed", "percent": 100, "images": len(images)}
        await db.commit()

    _publish(job_key, "completed", "completed", 100)
    logger.info("image post complete: %d slides", len(images))
    return {"images": images}


async def _run_clip(job_key: str, job_uuid, video, out_dir: Path, workdir: Path) -> dict:
    """Creator-clip branch: cut a highlight straight from uploaded footage.
    Original audio is the soundtrack; captions come from the whisper words."""
    from app.models.asset import Asset
    from app.pipeline import transcribe

    cfg = (video.script_data or {}).get("clip") or {}
    start, end = float(cfg["start"]), float(cfg["end"])

    async with AsyncSessionLocal() as db:
        asset = await db.get(Asset, UUID(str(cfg["asset_id"])))
        if asset is None:
            raise RuntimeError("source upload no longer exists")
        path_ref = asset.path
        transcript = asset.transcript or {}
    # Local disk path in dev, bucket key in prod — either way ffmpeg gets an
    # absolute local file (its cwd becomes the ASS workdir).
    source = await _resolve_asset_source(path_ref, workdir)

    _publish(job_key, "running", "captions", 20)
    aspect = ASPECT_RATIOS.get((video.script_data or {}).get("aspect_ratio") or "", ASPECT_RATIOS[assembler.DEFAULT_ASPECT])
    tier = (video.script_data or {}).get("tier") or {}
    if tier.get("height"):
        aspect = {**aspect, **dict(zip(("w", "h"), plans.tier_dimensions(aspect["w"], aspect["h"], int(tier["height"]))))}
    caption_style = (video.script_data or {}).get("caption_style") or captions.DEFAULT_CAPTION_STYLE
    words = transcribe.words_in_range(transcript, start, end)
    ass_path = None
    if words or tier.get("watermark"):
        ass_path = captions.write_ass(
            captions.group_words(words) if words else [], workdir / "clip.ass",
            style=caption_style, play_res=(aspect["w"], aspect["h"]),
            watermark_seconds=(end - start + 0.2) if tier.get("watermark") else None,
        )

    _publish(job_key, "running", "assembly", 45)
    final_path = (out_dir / "final.mp4").resolve()  # ffmpeg cwd is the workdir
    assembler.render_clip(source, start, end, final_path, ass_path=ass_path,
                          width=aspect["w"], height=aspect["h"])
    duration = assembler.probe_duration(final_path)

    async with AsyncSessionLocal() as db:
        job = await db.get(PipelineJob, job_uuid)
        video_row = await db.get(Video, job.video_id)
        video_row.status = "ready"
        video_row.video_url = f"/media/{video_row.id}/final.mp4"
        job.status = "completed"
        job.completed_at = datetime.now(timezone.utc)
        job.progress = {"stage": "completed", "percent": 100, "duration": duration}
        await db.commit()

    _publish(job_key, "completed", "completed", 100)
    logger.info("clip render complete: %s (%.1fs from %s)", final_path, duration, asset.filename)
    return {"video_url": f"/media/{video.id}/final.mp4", "duration": duration}


async def _run_fake_text(job_key: str, job_uuid, video, segments: list[dict], out_dir: Path, workdir: Path, aspect: dict) -> dict:
    """Fake-text-conversation branch: chat bubbles with typing beats over one
    looped background clip; music is the only audio."""
    from app.pipeline import fake_text

    messages = fake_text.parse_messages(segments)
    if len(messages) < 2:
        raise RuntimeError("fake text conversation needs at least 2 messages")

    _publish(job_key, "running", "chat", 15)
    ass_path, duration = fake_text.write_chat_ass(
        messages, workdir / "chat.ass", play_res=(aspect["w"], aspect["h"]),
        watermark=bool(((video.script_data or {}).get("tier") or {}).get("watermark")),
    )

    _publish(job_key, "running", "visuals", 35)
    bg_query = (video.script_data or {}).get("background_query") or "aesthetic blurred city night bokeh"
    clip_path = workdir / "bg.mp4"
    async with httpx.AsyncClient(timeout=60) as client:
        await pexels.fetch_clip(client, bg_query, clip_path, set(),
                                orientation=aspect["orientation"],
                                target_w=aspect["w"], target_h=aspect["h"])

    _publish(job_key, "running", "assembly", 60)
    silent_path = workdir / "chat_silent.mp4"
    assembler.render_segment_silent(clip_path, duration, silent_path, ass_path=ass_path,
                                    width=aspect["w"], height=aspect["h"])

    final_path = (out_dir / "final.mp4").resolve()
    music = _pick_music((video.script_data or {}).get("music_mood"))
    attribution = None
    if music is not None:
        _publish(job_key, "running", "music", 85)
        # Quieter than visual shorts — the viewer is reading.
        assembler.add_music_track(silent_path, music, final_path, music_volume=0.55)
        attribution = _music_attribution(music)
    else:
        shutil.move(str(silent_path), str(final_path))
    duration = assembler.probe_duration(final_path)
    media_url = await _store_media(final_path, video.id, "final.mp4")

    async with AsyncSessionLocal() as db:
        job = await db.get(PipelineJob, job_uuid)
        video_row = await db.get(Video, job.video_id)
        video_row.status = "ready"
        video_row.video_url = media_url
        if attribution and attribution not in (video_row.description or ""):
            video_row.description = f"{video_row.description or ''}\n\n{attribution}".strip()
        job.status = "completed"
        job.completed_at = datetime.now(timezone.utc)
        job.progress = {"stage": "completed", "percent": 100, "duration": duration}
        await db.commit()

    _publish(job_key, "completed", "completed", 100)
    logger.info("fake text render complete: %s (%.1fs, %d messages)", final_path, duration, len(messages))
    return {"video_url": media_url, "duration": duration}


async def run(job_id: str) -> dict:
    job_uuid = UUID(str(job_id))
    async with AsyncSessionLocal() as db:
        job = await db.get(PipelineJob, job_uuid)
        if job is None:
            raise RuntimeError(f"pipeline job {job_id} not found")

        video = await db.get(Video, job.video_id)
        segments = (video.script_data or {}).get("segments") or []
        # Clip renders cut from an uploaded asset — they have no script segments.
        if not segments and (video.output_type or "narrated") != "clip":
            raise RuntimeError("video has no script segments")

        job.status = "running"
        job.started_at = datetime.now(timezone.utc)
        video.status = "rendering"
        await db.commit()

    job_key = str(job_id)
    output_type = video.output_type or "narrated"
    aspect = ASPECT_RATIOS.get((video.script_data or {}).get("aspect_ratio") or "", ASPECT_RATIOS[assembler.DEFAULT_ASPECT])
    # The plan's render tier is decided at start time (routers/pipeline.py)
    # and frozen into script_data — a plan change mid-render can't confuse it.
    tier = (video.script_data or {}).get("tier") or {}
    watermark = bool(tier.get("watermark"))
    if tier.get("height"):
        aspect = {**aspect, **dict(zip(("w", "h"), plans.tier_dimensions(aspect["w"], aspect["h"], int(tier["height"]))))}
    out_dir = Path(settings.OUTPUT_DIR) / str(video.id)
    out_dir.mkdir(parents=True, exist_ok=True)
    workdir = Path(tempfile.mkdtemp(prefix="kliptos_"))

    try:
        if output_type == "clip":
            return await _run_clip(job_key, job_uuid, video, out_dir, workdir)
        if output_type == "fake_text":
            return await _run_fake_text(job_key, job_uuid, video, segments, out_dir, workdir, aspect)
        if output_type == "image":
            return await _run_image_post(job_key, job_uuid, video, segments, out_dir)

        # Stage 1: voice (narrated only) — visual shorts have no narration
        if output_type == "visual":
            voiced = [
                {
                    "index": i,
                    "audio_path": None,
                    "words": [],
                    # on-screen text needs reading time: clamp the LLM estimate
                    "duration": min(10.0, max(2.2, float(seg.get("duration_estimate") or len(seg["text"].split()) / 2.0))),
                }
                for i, seg in enumerate(segments)
            ]
        else:
            _publish(job_key, "running", "voice", 10)
            data = video.script_data or {}
            voice = data.get("voice_id") or tts.DEFAULT_VOICE
            provider = data.get("voice_provider")  # None = free edge-tts
            user_keys = {}
            if provider:
                from app.services.user_keys import get_user_keys

                async with AsyncSessionLocal() as kdb:
                    user_keys = await get_user_keys(kdb, video.user_id)
            voiced = await tts.synth_script(
                segments, workdir, voice=voice, provider=provider,
                user_keys=user_keys, language=(data.get("language") or "en"),
            )

        # Stage 2: visuals
        _publish(job_key, "running", "visuals", 35)

        # Creator-footage pins (asset_id) resolve up front: ownership and the
        # file itself are checked once, before any stock is downloaded.
        asset_paths: dict[str, Path] = {}
        pinned_asset_ids = {str(s["asset_id"]) for s in segments if s.get("asset_id")}
        if pinned_asset_ids:
            from app.models.asset import Asset

            async with AsyncSessionLocal() as adb:
                for aid in pinned_asset_ids:
                    asset = await adb.get(Asset, UUID(aid))
                    if asset is None or asset.user_id != video.user_id or asset.kind != "video":
                        raise RuntimeError("pinned footage no longer exists — unpin that scene and retry")
                    asset_paths[aid] = await _resolve_asset_source(asset.path, workdir)

        # AI-illustrated video: every scene is a generated image with slow
        # pan/zoom instead of stock footage. The creator's own pinned
        # footage still wins per scene, so real UI can sit beside it.
        ai_visuals = (video.visual_engine or "") == "ai_image" and output_type != "image"
        gen_keys: dict[str, str] = {}
        if ai_visuals:
            from app.services.user_keys import get_user_keys

            async with AsyncSessionLocal() as gdb:
                gen_keys = await get_user_keys(gdb, video.user_id)

        used_ids: set[int] = set()
        clips = []
        async with httpx.AsyncClient(timeout=60) as client:
            for i, seg in enumerate(segments):
                clip_path = workdir / f"clip_{i:02d}.mp4"
                if seg.get("asset_id"):  # the creator's own footage beats stock
                    assembler.cut_source(
                        asset_paths[str(seg["asset_id"])],
                        float(seg.get("asset_start") or 0.0),
                        voiced[i]["duration"] + 0.5,
                        clip_path,
                    )
                elif ai_visuals:
                    from app.services import image_gen

                    still = workdir / f"scene_{i:02d}.jpg"
                    prompt = image_gen.scene_prompt(
                        seg.get("visual_prompt") or seg["text"],
                        aspect=(video.script_data or {}).get("aspect_ratio") or assembler.DEFAULT_ASPECT,
                        style=(video.script_data or {}).get("visual_style") or image_gen.DEFAULT_VISUAL_STYLE,
                    )
                    await image_gen.generate_image(prompt, still, user_keys=gen_keys)
                    assembler.image_to_clip(
                        still, voiced[i]["duration"] + 0.4, clip_path,
                        width=aspect["w"], height=aspect["h"], zoom_in=(i % 2 == 0),
                    )
                elif seg.get("media_id"):  # user pinned a specific clip in the studio
                    await pexels.fetch_clip_by_id(client, int(seg["media_id"]), clip_path,
                                                  orientation=aspect["orientation"],
                                                  target_w=aspect["w"], target_h=aspect["h"])
                    used_ids.add(int(seg["media_id"]))
                else:
                    # Formats like Reddit Story use ONE background theme for the
                    # whole video (used_ids still varies the actual clips).
                    bg_query = (video.script_data or {}).get("background_query")
                    query = bg_query or seg.get("visual_prompt") or seg["text"]
                    await pexels.fetch_clip(client, query, clip_path, used_ids,
                                            orientation=aspect["orientation"],
                                            target_w=aspect["w"], target_h=aspect["h"])
                clips.append(clip_path)
                _publish(job_key, "running", "visuals", 35 + (i + 1) / len(segments) * 25)

        # Stage 3: assembly (with burned-in captions)
        _publish(job_key, "running", "assembly", 65)
        caption_style = (video.script_data or {}).get("caption_style") or captions.DEFAULT_CAPTION_STYLE
        rendered = []
        for i, (seg_audio, clip) in enumerate(zip(voiced, clips)):
            seg_out = workdir / f"final_{i:02d}.mp4"
            ass_path = captions.build_segment_captions(
                words=seg_audio.get("words") or [],
                text=segments[i]["text"],
                duration=seg_audio["duration"],
                out_path=workdir / f"cap_{i:02d}.ass",
                style=caption_style,
                play_res=(aspect["w"], aspect["h"]),
                watermark=watermark,
            )
            if output_type == "visual":
                assembler.render_segment_silent(clip, seg_audio["duration"], seg_out, ass_path=ass_path,
                                                width=aspect["w"], height=aspect["h"])
            else:
                assembler.render_segment(
                    clip, Path(seg_audio["audio_path"]), seg_audio["duration"], seg_out, ass_path=ass_path,
                    width=aspect["w"], height=aspect["h"],
                )
            rendered.append(seg_out)
            _publish(job_key, "running", "assembly", 65 + (i + 1) / len(segments) * 20)

        concat_path = workdir / "concat_full.mp4"
        assembler.concat_segments(rendered, concat_path, workdir)

        # Stage 4: music — background bed for narrated, THE soundtrack for visual
        final_path = out_dir / "final.mp4"
        music = _pick_music((video.script_data or {}).get("music_mood"))
        attribution = None
        if music is not None:
            _publish(job_key, "running", "music", 90)
            if output_type == "visual":
                assembler.add_music_track(concat_path, music, final_path, music_volume=0.85)
            else:
                assembler.mix_music(concat_path, music, final_path)
            attribution = _music_attribution(music)
            logger.info("mixed music track: %s", music.name)
        else:
            shutil.move(str(concat_path), str(final_path))
        duration = assembler.probe_duration(final_path)
        media_url = await _store_media(final_path, video.id, "final.mp4")

        # Stage 5: persist
        async with AsyncSessionLocal() as db:
            job = await db.get(PipelineJob, job_uuid)
            video = await db.get(Video, job.video_id)
            video.status = "ready"
            video.video_url = media_url
            if attribution and attribution not in (video.description or ""):
                video.description = f"{video.description or ''}\n\n{attribution}".strip()
            job.status = "completed"
            job.completed_at = datetime.now(timezone.utc)
            job.progress = {"stage": "completed", "percent": 100, "duration": duration}
            await db.commit()

        _publish(job_key, "completed", "completed", 100)
        logger.info("render complete: %s (%.1fs)", final_path, duration)
        return {"video_url": media_url, "duration": duration}

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
