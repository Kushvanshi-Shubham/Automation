"""Proof render: see one scene before spending credits on the whole video.

The point is to make style decisions cheap. A creator picks a voice, a
caption look, an animation and a visual style, renders ONE scene for
free, watches it, adjusts, repeats — and only then commits to the full
film. Free is affordable because a single scene costs us a fraction of a
cent, and it removes the "I paid a credit to discover the captions were
ugly" problem entirely.

Deliberately NOT a pipeline job: no credit ledger, no Video status
change, and the output goes to a proofs/ prefix that never appears in the
library.
"""
import asyncio
import logging
import shutil
import tempfile
from pathlib import Path
from uuid import UUID

import httpx

from app.config import settings
from app.database import AsyncSessionLocal
from app.models.video import Video
from app.pipeline import assembler, captions, tts
from app.pipeline.assembler import ASPECT_RATIOS
from app.pipeline.celery_app import celery_app
from app.pipeline.visuals import pexels
from app.services import plans

logger = logging.getLogger("kliptos.proof")

# One scene is enough to judge voice + captions + visual style, and keeps
# the cost and the wait small.
MAX_PROOF_SECONDS = 12.0


async def _run(video_id: str, scene_index: int = 0) -> dict:
    from app.services.user_keys import get_user_keys

    async with AsyncSessionLocal() as db:
        video = await db.get(Video, UUID(str(video_id)))
        if video is None:
            raise RuntimeError("video not found")
        data = dict(video.script_data or {})
        segments = data.get("segments") or []
        user_keys = await get_user_keys(db, video.user_id)
        owner_id = video.user_id
        output_type = video.output_type or "narrated"
        engine = video.visual_engine or "pexels"

    if not segments:
        raise RuntimeError("nothing to preview — generate a script first")
    scene_index = max(0, min(scene_index, len(segments) - 1))
    seg = segments[scene_index]

    aspect = ASPECT_RATIOS.get(data.get("aspect_ratio") or "", ASPECT_RATIOS[assembler.DEFAULT_ASPECT])
    tier = data.get("tier") or {}
    if tier.get("height"):
        aspect = {**aspect, **dict(zip(("w", "h"), plans.tier_dimensions(aspect["w"], aspect["h"], int(tier["height"]))))}

    workdir = Path(tempfile.mkdtemp(prefix="kliptos_proof_"))
    out_dir = Path(settings.OUTPUT_DIR) / "proofs" / str(video_id)
    out_dir.mkdir(parents=True, exist_ok=True)
    final_path = (out_dir / "proof.mp4").resolve()

    try:
        # Voice (or a silent reading-time estimate for text-only formats)
        if output_type == "visual":
            duration = min(MAX_PROOF_SECONDS, max(2.2, float(seg.get("duration_estimate") or 4.0)))
            audio_path, words = None, []
        else:
            audio_path = workdir / "proof.mp3"
            provider = data.get("voice_provider")
            voice = data.get("voice_id") or tts.DEFAULT_VOICE
            if provider:
                from app.services import premium_voice

                duration, words = await premium_voice.synth_with_timings(
                    seg["text"], audio_path, voice, provider,
                    user_keys=user_keys, language=data.get("language") or "en",
                )
            else:
                duration, words = await tts.synth_segment(seg["text"], audio_path, voice)
            duration = min(duration, MAX_PROOF_SECONDS)

        # Visual for this one scene
        clip_path = workdir / "proof_clip.mp4"
        if engine == "ai_image" and output_type != "image":
            from app.services import image_gen

            still = workdir / "proof.jpg"
            aspect_ratio = data.get("aspect_ratio") or assembler.DEFAULT_ASPECT
            await image_gen.generate_image(
                image_gen.scene_prompt(
                    seg.get("visual_prompt") or seg["text"],
                    aspect=aspect_ratio,
                    style=data.get("visual_style") or image_gen.DEFAULT_VISUAL_STYLE,
                ),
                still, user_keys=user_keys, aspect=aspect_ratio,
            )
            assembler.image_to_clip(still, duration + 0.4, clip_path,
                                    width=aspect["w"], height=aspect["h"])
        elif seg.get("asset_id"):
            from app.models.asset import Asset
            from app.services import storage

            async with AsyncSessionLocal() as db:
                asset = await db.get(Asset, UUID(str(seg["asset_id"])))
                if asset is None or asset.user_id != owner_id:
                    raise RuntimeError("pinned footage is no longer available")
                path_ref = asset.path
            source = await asyncio.to_thread(storage.resolve_source, path_ref, workdir)
            assembler.cut_source(source, float(seg.get("asset_start") or 0.0), duration + 0.5, clip_path)
        else:
            async with httpx.AsyncClient(timeout=60) as client:
                query = data.get("background_query") or seg.get("visual_prompt") or seg["text"]
                if seg.get("media_id"):
                    await pexels.fetch_clip_by_id(client, int(seg["media_id"]), clip_path,
                                                 orientation=aspect["orientation"],
                                                 target_w=aspect["w"], target_h=aspect["h"])
                else:
                    await pexels.fetch_clip(client, query, clip_path, set(),
                                            orientation=aspect["orientation"],
                                            target_w=aspect["w"], target_h=aspect["h"])

        # Captions exactly as the full render would draw them
        ass_path = captions.build_segment_captions(
            words=words,
            text=seg["text"],
            duration=duration,
            out_path=workdir / "proof.ass",
            style=data.get("caption_style") or captions.DEFAULT_CAPTION_STYLE,
            play_res=(aspect["w"], aspect["h"]),
            watermark=bool(tier.get("watermark")),
            animation=data.get("caption_animation") or "none",
            font=data.get("caption_font"),
            color=data.get("caption_color"),
            headline=seg.get("headline"),
        )

        if audio_path is None:
            assembler.render_segment_silent(clip_path, duration, final_path, ass_path=ass_path,
                                            width=aspect["w"], height=aspect["h"])
        else:
            assembler.render_segment(clip_path, audio_path, duration, final_path, ass_path=ass_path,
                                     width=aspect["w"], height=aspect["h"])

        from app.services import storage

        if storage.enabled():
            url = await asyncio.to_thread(
                storage.upload, final_path, f"proofs/{video_id}/proof.mp4"
            )
        else:
            url = f"/media/proofs/{video_id}/proof.mp4"

        async with AsyncSessionLocal() as db:
            row = await db.get(Video, UUID(str(video_id)))
            row.script_data = {
                **(row.script_data or {}),
                "proof": {"url": url, "scene": scene_index, "duration": round(duration, 2)},
            }
            await db.commit()

        logger.info("proof render complete for %s scene %d", video_id, scene_index)
        return {"url": url, "scene": scene_index, "duration": round(duration, 2)}
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


@celery_app.task(bind=True, name="pipeline.proof")
def render_proof(self, video_id: str, scene_index: int = 0):
    from app.pipeline.tasks import _with_fresh_pool

    return asyncio.run(_with_fresh_pool(_run(video_id, scene_index)))
