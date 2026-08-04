"""Celery task: learn a personal style from the creator's reference reels.

Each source asset already carries a Whisper transcript (asset.process); this
task distills pace, hooks, and wording into a reusable script recipe via one
LLM call, then flips the UserFormat to "ready".
"""
import asyncio
import logging
from uuid import UUID

from app.database import AsyncSessionLocal
from app.models.asset import Asset
from app.models.user_format import UserFormat
from app.pipeline.celery_app import celery_app

logger = logging.getLogger("kliptos.style")

HOOK_SECONDS = 3.5
MAX_REEL_TEXT_CHARS = 1500
MAX_RECIPE_CHARS = 1200
ALLOWED_CAPTION_STYLES = {"classic", "neon", "impact", "minimal", "karaoke"}
ALLOWED_MUSIC_MOODS = {"calm", "energetic"}

SYSTEM_PROMPT = (
    "You are a short-form video style analyst. You are given transcripts and stats "
    "from several reels made by ONE creator. Reverse-engineer the creator's style: "
    "how they hook viewers, their sentence rhythm, vocabulary, structure, and how "
    "they close (CTA habits). Reply with JSON ONLY, exactly this shape:\n"
    '{"tone": "<3-6 word tone description>", '
    '"caption_style": "<one of: classic|neon|impact|minimal|karaoke>", '
    '"music_mood": "<calm|energetic>", '
    '"recipe": "<imperative script-writing instructions capturing the style: hook pattern, '
    'sentence rhythm, vocabulary, structure, CTA habit — max 1200 chars>", '
    '"summary": "<2-sentence human-readable description of the learned style>"}'
)


def _reel_stats(asset: Asset) -> dict | None:
    """Per-reel analysis: duration, word count, pace, the hook, transcript text."""
    segments = (asset.transcript or {}).get("segments") or []
    if not segments:
        return None
    text = " ".join((seg.get("text") or "").strip() for seg in segments).strip()
    word_count = len(text.split())
    duration = float(asset.duration or 0) or float(segments[-1].get("end") or 0)
    wps = round(word_count / duration, 2) if duration > 0 else 0.0
    # The hook: everything said in the first HOOK_SECONDS (word-level timings).
    hook = " ".join(
        (w.get("word") or "").strip()
        for seg in segments
        for w in (seg.get("words") or [])
        if float(w.get("start") or 0) < HOOK_SECONDS
    ).strip()
    return {
        "duration": duration,
        "words": word_count,
        "wps": wps,
        "hook": hook,
        "text": text[:MAX_REEL_TEXT_CHARS],
    }


async def _run(user_format_id: str) -> dict:
    from app.services.llm import generate_json
    from app.services.user_keys import get_user_keys

    async with AsyncSessionLocal() as db:
        uf = await db.get(UserFormat, UUID(user_format_id))
        if uf is None:
            raise RuntimeError("user format not found")
        uf.status = "learning"
        await db.commit()
        user_id = uf.user_id
        asset_ids = [UUID(a) for a in (uf.source_asset_ids or [])]

    try:
        async with AsyncSessionLocal() as db:
            user_keys = await get_user_keys(db, user_id)
            reels = []
            for asset_id in asset_ids:
                asset = await db.get(Asset, asset_id)
                if asset is None or not asset.transcript:
                    continue  # deleted or never transcribed — learn from the rest
                stats = _reel_stats(asset)
                if stats:
                    reels.append(stats)

        if not reels:
            raise RuntimeError("none of the source reels have a usable transcript")

        avg_wps = round(sum(r["wps"] for r in reels) / len(reels), 2)
        blocks = []
        for i, r in enumerate(reels, 1):
            blocks.append(
                f"REEL {i}: {r['duration']:.0f}s, {r['words']} words, {r['wps']} words/sec\n"
                f"HOOK (first {HOOK_SECONDS}s): {r['hook'] or '(silent open)'}\n"
                f"TRANSCRIPT: {r['text']}"
            )
        user_prompt = (
            "\n\n".join(blocks)
            + f"\n\nAverage pace: {avg_wps} words/sec across {len(reels)} reels."
        )

        result = await generate_json(SYSTEM_PROMPT, user_prompt, temperature=0.4, user_keys=user_keys)

        caption_style = result.get("caption_style")
        if caption_style not in ALLOWED_CAPTION_STYLES:
            caption_style = "classic"
        music_mood = result.get("music_mood")
        if music_mood not in ALLOWED_MUSIC_MOODS:
            music_mood = "calm"
        recipe = str(result.get("recipe") or "").strip()[:MAX_RECIPE_CHARS]
        tone = str(result.get("tone") or "").strip() or None
        summary = str(result.get("summary") or "").strip()

        async with AsyncSessionLocal() as db:
            uf = await db.get(UserFormat, UUID(user_format_id))
            uf.profile = {
                "summary": summary,
                "reels": len(reels),
                "avg_wps": avg_wps,
                "hooks": [r["hook"] for r in reels[:3]],
            }
            uf.script_recipe = recipe
            uf.caption_style = caption_style
            uf.music_mood = music_mood
            uf.tone = tone
            uf.status = "ready"
            uf.error_message = None
            await db.commit()
        logger.info("style %s ready: %d reels, %.2f wps", user_format_id, len(reels), avg_wps)
        return {"reels": len(reels), "avg_wps": avg_wps}
    except Exception as exc:
        logger.exception("style learning failed: %s", user_format_id)
        async with AsyncSessionLocal() as db:
            uf = await db.get(UserFormat, UUID(user_format_id))
            uf.status = "failed"
            uf.error_message = str(exc)[:2000]
            await db.commit()
        raise


@celery_app.task(bind=True, name="style.learn")
def learn_style(self, user_format_id: str):
    from app.pipeline.tasks import _with_fresh_pool

    return asyncio.run(_with_fresh_pool(_run(user_format_id)))
