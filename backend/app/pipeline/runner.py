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

# Instagram carousels top out at 10 images; every other surface we post to
# allows at least that many.
MAX_CAROUSEL_SLIDES = 10

MUSIC_DIR = Path(__file__).resolve().parent.parent.parent / "assets" / "music"


# Filename keywords per mood; a format's music_mood narrows the pick.
MOOD_KEYWORDS = {
    "calm": ("calm", "ambient", "wallpaper"),
    "energetic": ("energetic", "upbeat", "carefree"),
    "melancholy": ("melancholy", "sad", "anguish"),
    "tender": ("tender", "bittersweet", "sweeter"),
    "uplifting": ("uplifting", "inspired", "hopeful"),
}


def _pick_music(mood: str | None = None) -> Path | None:
    if not MUSIC_DIR.is_dir():
        return None
    tracks = sorted(MUSIC_DIR.glob("*.mp3"))
    if mood in MOOD_KEYWORDS:
        matching = [t for t in tracks if any(k in t.stem.lower() for k in MOOD_KEYWORDS[mood])]
        if not matching:
            # Falling back to "any track" is why every video sounded the same.
            # It is still the right behaviour, but it should not be silent.
            logger.warning(
                "no music matches mood %r — falling back to the whole library "
                "(run scripts/seed_music.py to populate it)", mood,
            )
        tracks = matching or tracks
    elif mood:
        logger.warning("unknown music mood %r — using the whole library", mood)
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


async def _visual_for_scene(
    client, i: int, seg: dict, clip_path: Path, narration_seconds: float,
    *, video, aspect: dict, asset_paths: dict, ai_visuals: bool,
    gen_keys: dict, used_ids: set,
) -> None:
    """Produce one scene's visual, in priority order.

    The creator's own choices come first — their uploaded footage, then a clip
    they pinned in the studio — because a pin that is silently ignored is worse
    than no pin at all. That ordering was wrong until now: `media_id` sat BELOW
    the AI branch, so on the ai_image engine a creator could hand-pick a clip
    for every scene, see seven green "Visual pinned" confirmations, pay, and
    receive byte-identical generated stills.
    """
    from app.services import image_gen

    if seg.get("asset_id"):  # the creator's own footage beats everything
        assembler.cut_source(
            asset_paths[str(seg["asset_id"])],
            float(seg.get("asset_start") or 0.0),
            narration_seconds + 0.5,
            clip_path,
        )
        return

    if seg.get("media_id"):  # a clip they pinned in the studio
        await pexels.fetch_clip_by_id(client, int(seg["media_id"]), clip_path,
                                      orientation=aspect["orientation"],
                                      target_w=aspect["w"], target_h=aspect["h"])
        used_ids.add(int(seg["media_id"]))
        return

    data = video.script_data or {}
    if ai_visuals:
        still = clip_path.parent / f"scene_{i:02d}.jpg"
        aspect_ratio = data.get("aspect_ratio") or assembler.DEFAULT_ASPECT
        prompt = image_gen.scene_prompt(
            seg.get("visual_prompt") or seg["text"],
            aspect=aspect_ratio,
            style=data.get("visual_style") or image_gen.DEFAULT_VISUAL_STYLE,
            # The narration is the ground truth for what this scene is about.
            # Passing it means a thin or generic visual_prompt still carries the
            # line's subject into the image.
            says=seg.get("text"),
        )
        await image_gen.generate_image(prompt, still, user_keys=gen_keys, aspect=aspect_ratio)
        assembler.image_to_clip(
            still, narration_seconds + 0.4, clip_path,
            width=aspect["w"], height=aspect["h"], zoom_in=(i % 2 == 0),
            motion=_editing(data)["motion"],
        )
        return

    # Formats like Reddit Story use ONE background theme for the whole video
    # (used_ids still varies the actual clips).
    query = data.get("background_query") or seg.get("visual_prompt") or seg["text"]
    await pexels.fetch_clip(client, query, clip_path, used_ids,
                            orientation=aspect["orientation"],
                            target_w=aspect["w"], target_h=aspect["h"])


def _editing(data: dict | None) -> dict:
    """The format's editing grammar, as stored on the video at generation time.

    Older videos predate the field and simply get the defaults, which are
    byte-for-byte the behaviour they were rendered with.
    """
    from app.services.formats import EDITING_DEFAULT

    out = dict(EDITING_DEFAULT)
    out.update((data or {}).get("editing") or {})
    return out


def _assemble_segment(
    *, index: int, seg: dict, seg_audio: dict, clip: Path, out_path: Path,
    workdir: Path, data: dict, aspect: dict, watermark: bool, silent: bool,
) -> Path:
    """Burn one segment's captions and render it to a file.

    Extracted from run() so the wiring is testable. Every previous version of
    this code assembled the caption and render arguments inline, which is how
    a format's settings could be computed correctly and then never reach the
    call — the bug this whole editing layer would otherwise repeat.
    """
    edit = _editing(data)
    ass_path = captions.build_segment_captions(
        words=seg_audio.get("words") or [],
        text=seg["text"],
        duration=seg_audio["duration"],
        out_path=workdir / f"cap_{index:02d}.ass",
        style=data.get("caption_style") or captions.DEFAULT_CAPTION_STYLE,
        play_res=(aspect["w"], aspect["h"]),
        watermark=watermark,
        animation=data.get("caption_animation") or "none",
        font=data.get("caption_font"),
        color=data.get("caption_color"),
        headline=seg.get("headline"),
        words_per_cue=edit["words_per_cue"],
    )
    # A hard cut is fade=0, which _fade_filter turns into no filter at all —
    # so "cut" formats render through the identical filtergraph as before.
    fade = edit["fade"] if edit["transition"] == "soft" else 0.0
    if silent:
        assembler.render_segment_silent(
            clip, seg_audio["duration"], out_path, ass_path=ass_path,
            width=aspect["w"], height=aspect["h"], fade=fade,
        )
    else:
        assembler.render_segment(
            clip, Path(seg_audio["audio_path"]), seg_audio["duration"], out_path,
            ass_path=ass_path, width=aspect["w"], height=aspect["h"], fade=fade,
        )
    return out_path


async def _fallback_visual(
    client, i: int, seg: dict, clip_path: Path, narration_seconds: float,
    *, video, aspect: dict, used_ids: set,
) -> None:
    """Last resort when a scene's preferred visual could not be produced.

    Tried in widening order, because the usual cause is a query too specific
    for a stock library to answer — so each step gives up some specificity
    rather than some quality. Raises only if even the house query fails, which
    means the render genuinely cannot continue.
    """
    data = video.script_data or {}
    attempts = [
        # The format's own background theme, if it has one.
        data.get("background_query"),
        # The first few words of the line: a noun phrase stock can answer.
        " ".join(str(seg.get("text") or "").split()[:4]) or None,
        # A neutral house query that always returns something.
        "abstract soft gradient background motion",
    ]
    last: Exception | None = None
    for query in [a for a in attempts if a]:
        try:
            await pexels.fetch_clip(client, query, clip_path, used_ids,
                                    orientation=aspect["orientation"],
                                    target_w=aspect["w"], target_h=aspect["h"])
            logger.info("scene %d fell back to %r", i, query)
            return
        except Exception as exc:
            last = exc
            continue
    raise RuntimeError(f"scene {i + 1}: no visual could be sourced") from last


async def _run_image_post(job_key: str, job_uuid, video, segments: list[dict], out_dir: Path) -> dict:
    """Image-post branch: one image per slide (stock photos or AI images)."""
    from app.services import image_gen
    from app.services.user_keys import get_user_keys

    engine = video.visual_engine or "stock_image"
    aspect = (video.script_data or {}).get("aspect_ratio") or assembler.DEFAULT_ASPECT
    orientation = ASPECT_RATIOS.get(aspect, ASPECT_RATIOS[assembler.DEFAULT_ASPECT])["orientation"]
    # A carousel is slides, not seconds: the creator picks how many, the script
    # is generated with that many segments, and we use all of them. The cap is
    # the platform ceiling (Instagram allows 10), not a magic number - and we
    # say so when it bites instead of dropping segments in silence.
    slides = segments[:MAX_CAROUSEL_SLIDES]
    if len(segments) > MAX_CAROUSEL_SLIDES:
        logger.warning(
            "image post: script had %d segments, keeping the first %d (platform cap)",
            len(segments), MAX_CAROUSEL_SLIDES,
        )
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
                # Through scene_prompt like the video path, so slides get the
                # format's look and the same no-text ban. This path used to
                # send a raw prompt and rely on STYLE_SUFFIX for both.
                styled = image_gen.scene_prompt(
                    prompt, aspect=aspect,
                    style=(video.script_data or {}).get("visual_style") or image_gen.DEFAULT_VISUAL_STYLE,
                    says=seg.get("text"),
                )
                await image_gen.generate_image(styled, out_path, user_keys=user_keys, aspect=aspect)
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
    # MUST go through _store_media. In the cloud the API and the worker are
    # separate containers with no shared volume, so a bare /media/ path is a
    # file only the worker can see — this branch 404'd in production while
    # passing every test, because the tests never assert the URL is reachable.
    media_url = await _store_media(final_path, video.id, "final.mp4")

    async with AsyncSessionLocal() as db:
        job = await db.get(PipelineJob, job_uuid)
        video_row = await db.get(Video, job.video_id)
        video_row.status = "ready"
        video_row.video_url = media_url
        job.status = "completed"
        job.completed_at = datetime.now(timezone.utc)
        job.progress = {"stage": "completed", "percent": 100, "duration": duration}
        await db.commit()

    _publish(job_key, "completed", "completed", 100)
    logger.info("clip render complete: %s (%.1fs from %s)", final_path, duration, asset.filename)
    return {"video_url": f"/media/{video.id}/final.mp4", "duration": duration}


async def _run_montage(job_key: str, job_uuid, video, out_dir: Path, workdir: Path) -> dict:
    """Montage branch: several highlights from one upload, cut back to back.

    A clip render is one moment; this is the reel. The original audio is
    kept — in gameplay that IS the content — with an optional music bed
    ducked underneath, which is why it uses mix_music rather than replacing
    the soundtrack.

    Cuts are not beat-synced yet: each piece keeps the length the creator
    chose. Snapping them to the music's beat grid is the next step, and
    saying so here is cheaper than someone inferring it already happens.
    """
    from app.models.asset import Asset
    from app.pipeline import transcribe

    cfg = (video.script_data or {}).get("montage") or {}
    ranges = cfg.get("ranges") or []
    if len(ranges) < 2:
        raise RuntimeError("a montage needs at least 2 clips")

    async with AsyncSessionLocal() as db:
        asset = await db.get(Asset, UUID(str(cfg["asset_id"])))
        if asset is None:
            raise RuntimeError("source upload no longer exists")
        path_ref = asset.path
        transcript = asset.transcript or {}
        filename = asset.filename
        asset_duration = float(asset.duration or 0.0)
    source = await _resolve_asset_source(path_ref, workdir)

    data = video.script_data or {}
    aspect = ASPECT_RATIOS.get(data.get("aspect_ratio") or "", ASPECT_RATIOS[assembler.DEFAULT_ASPECT])
    tier = data.get("tier") or {}
    if tier.get("height"):
        aspect = {**aspect, **dict(zip(("w", "h"), plans.tier_dimensions(aspect["w"], aspect["h"], int(tier["height"]))))}
    caption_style = data.get("caption_style") or captions.DEFAULT_CAPTION_STYLE

    # Music is chosen before the clips are cut, because if there IS a bed the
    # clip lengths get snapped to its beat grid — mix_music loops the track
    # from its own start, so music t=0 is montage t=0 and the grid lines up.
    music = _pick_music(data.get("music_mood")) if data.get("music_mood") else None
    beat_info = None
    if music is not None:
        from app.services import beats

        try:
            beat_info = await asyncio.to_thread(beats.detect, music)
        except beats.NoBeatError as exc:
            # An ambient bed with no pulse is a fine soundtrack; there is
            # just nothing to snap to. Cuts keep the creator's lengths.
            logger.info("no beat grid in %s (%s) — cuts stay as chosen", music.name, exc)
        except Exception:
            logger.warning("beat detection failed for %s", music.name, exc_info=True)

    if beat_info:
        from app.services import beats

        wanted = [float(r["end"]) - float(r["start"]) for r in ranges]
        snapped = beats.snap_durations(
            wanted, beat_info["period"], beat_info["phase"], min_seconds=5.0
        )
        adjusted = []
        for rng, length in zip(ranges, snapped):
            start = float(rng["start"])
            end = start + length
            # A snap that runs off the end of the source loses the alignment
            # for that one clip rather than reading past the file.
            if asset_duration and end > asset_duration:
                end = asset_duration
            adjusted.append({"start": start, "end": round(end, 3)})
        ranges = adjusted
        logger.info("montage snapped to %.1f bpm (phase %.2fs): %s -> %s",
                    beat_info["bpm"], beat_info["phase"],
                    [round(w, 2) for w in wanted], [round(s, 2) for s in snapped])

    pieces: list[Path] = []
    for i, rng in enumerate(ranges):
        start, end = float(rng["start"]), float(rng["end"])
        # Captions per piece, with word times rebased to that piece's own
        # zero — a montage's third clip starts at 0 in the output even
        # though it started minutes into the source.
        words = transcribe.words_in_range(transcript, start, end)
        ass_path = None
        if words:
            ass_path = captions.write_ass(
                captions.group_words(words), workdir / f"montage_{i:02d}.ass",
                style=caption_style, play_res=(aspect["w"], aspect["h"]),
            )
        piece = workdir / f"piece_{i:02d}.mp4"
        assembler.render_clip(source, start, end, piece, ass_path=ass_path,
                              width=aspect["w"], height=aspect["h"])
        pieces.append(piece)
        _publish(job_key, "running", "clips", 15 + (i + 1) / len(ranges) * 45)

    _publish(job_key, "running", "assembly", 70)
    joined = workdir / "joined.mp4"
    # Every piece went through render_clip with the same size and codec
    # settings, so this is a stream copy rather than a re-encode.
    assembler.concat_segments(pieces, joined, workdir)

    final_path = (out_dir / "final.mp4").resolve()
    if music is not None:
        _publish(job_key, "running", "music", 85)
        # Ducked under the gameplay audio, not over it.
        assembler.mix_music(joined, music, final_path)
    else:
        shutil.copyfile(joined, final_path)
    duration = assembler.probe_duration(final_path)
    # MUST go through _store_media. In the cloud the API and the worker are
    # separate containers with no shared volume, so a bare /media/ path is a
    # file only the worker can see — this branch 404'd in production while
    # passing every test, because the tests never assert the URL is reachable.
    media_url = await _store_media(final_path, video.id, "final.mp4")

    async with AsyncSessionLocal() as db:
        job = await db.get(PipelineJob, job_uuid)
        video_row = await db.get(Video, job.video_id)
        video_row.status = "ready"
        video_row.video_url = media_url
        job.status = "completed"
        job.completed_at = datetime.now(timezone.utc)
        job.progress = {"stage": "completed", "percent": 100, "duration": duration}
        await db.commit()

    _publish(job_key, "completed", "completed", 100)
    logger.info("montage complete: %s (%d clips, %.1fs from %s)",
                final_path, len(pieces), duration, filename)
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
        # Clips and montages are cut from an uploaded asset, so they have no
        # script segments — their ranges live in script_data instead.
        if not segments and (video.output_type or "narrated") not in ("clip", "montage"):
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
        if output_type == "montage":
            return await _run_montage(job_key, job_uuid, video, out_dir, workdir)
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
                words_per_second=data.get("words_per_second"),
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
        degraded: list[int] = []
        async with httpx.AsyncClient(timeout=60) as client:
            for i, seg in enumerate(segments):
                clip_path = workdir / f"clip_{i:02d}.mp4"
                try:
                    await _visual_for_scene(
                        client, i, seg, clip_path, voiced[i]["duration"],
                        video=video, aspect=aspect, asset_paths=asset_paths,
                        ai_visuals=ai_visuals, gen_keys=gen_keys, used_ids=used_ids,
                    )
                except Exception as exc:
                    # One scene failing must not cost a whole render. Pexels
                    # raises on zero results and the image model raises on a
                    # policy refusal — both are likelier the MORE specific a
                    # visual prompt is, which is exactly the direction we want
                    # prompts to move. So a scene degrades and says so, rather
                    # than failing the video and refunding.
                    logger.warning("scene %d visual failed (%s: %s) — falling back",
                                   i, type(exc).__name__, exc)
                    await _fallback_visual(client, i, seg, clip_path, voiced[i]["duration"],
                                           video=video, aspect=aspect, used_ids=used_ids)
                    degraded.append(i + 1)
                clips.append(clip_path)
                _publish(job_key, "running", "visuals", 35 + (i + 1) / len(segments) * 25)
        if degraded:
            # Named, not silent: a creator who can see which scene degraded can
            # pin a clip there and re-render. A silent fallback is how a
            # recoverable render becomes lost trust.
            logger.warning("video %s: %d scene(s) used a fallback visual: %s",
                           video.id, len(degraded), degraded)

        # Stage 3: assembly (with burned-in captions)
        _publish(job_key, "running", "assembly", 65)
        rendered = []
        for i, (seg_audio, clip) in enumerate(zip(voiced, clips)):
            seg_out = workdir / f"final_{i:02d}.mp4"
            _assemble_segment(
                index=i, seg=segments[i], seg_audio=seg_audio, clip=clip, out_path=seg_out,
                workdir=workdir, data=video.script_data or {}, aspect=aspect,
                watermark=watermark, silent=(output_type == "visual"),
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
            # `or 1` here MINTED credits: a free restyle is charged 0, so a
            # failing restyle handed back a credit that was never taken. Refund
            # exactly what was charged, and zero it so a retry cannot refund
            # the same credit twice.
            refund = video.credits_used or 0
            if refund:
                user.credit_balance += refund
                db.add(CreditLedger(user_id=user.id, amount=refund, type="refund",
                                    description="Render failed — automatic refund", video_id=video.id))
                video.credits_used = 0
            await db.commit()
        _publish(job_key, "failed", "failed", 0, error=str(exc)[:300])
        raise
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
