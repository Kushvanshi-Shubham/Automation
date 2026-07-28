"""Script generation for 60-second vertical shorts (Gemini free-tier first, GPT-4o fallback)."""
import logging

from fastapi import HTTPException, status

from app.services.llm import generate_json

logger = logging.getLogger("kliptos.script_gen")

SYSTEM_PROMPT = """You are a viral YouTube Shorts scriptwriter. You write tight, hook-driven,
fact-checked scripts for 9:16 vertical videos narrated by a single voice.

Rules:
- The first segment is the HOOK: it must create an open loop in under 3 seconds of speech.
- Each segment is 1-2 spoken sentences (max ~25 words) with ONE clear idea.
- Every segment includes a visual_prompt: a concrete, filmable description for stock-footage
  search or AI video generation (no text overlays, no brand names, no celebrity likenesses).
- End with a payoff + subtle rewatch/subscribe nudge (no begging).
- Total spoken duration must fit the requested length at ~2.5 words/second.

Respond ONLY with JSON matching:
{
  "title": "video title, <=95 chars, curiosity-driven, no clickbait lies",
  "description": "2-3 sentence YouTube description with 3 relevant hashtags",
  "tags": ["8-12 SEO tags"],
  "segments": [
    {"text": "spoken narration", "visual_prompt": "filmable visual description",
     "duration_estimate": 4.5}
  ]
}"""


async def generate_script(
    topic: str,
    hook_hint: str | None = None,
    tone: str = "engaging and curious",
    duration_seconds: int = 60,
) -> dict:
    user_prompt = (
        f"Topic: {topic}\n"
        f"Tone: {tone}\n"
        f"Target duration: {duration_seconds} seconds\n"
        + (f"Hook inspiration (improve on it): {hook_hint}\n" if hook_hint else "")
        + "Write the script now."
    )
    data = await generate_json(SYSTEM_PROMPT, user_prompt, temperature=0.8)

    segments = data.get("segments") or []
    if not segments:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Script generation returned no segments")
    for seg in segments:
        seg.setdefault("duration_estimate", round(len(str(seg.get("text", "")).split()) / 2.5, 1))
    data["total_duration"] = round(sum(float(s["duration_estimate"]) for s in segments), 1)
    return data


async def regenerate_segment(
    topic: str,
    full_script: list[dict],
    segment_index: int,
    feedback: str,
) -> dict:
    context = "\n".join(f"[{i}] {s.get('text', '')}" for i, s in enumerate(full_script))
    user_prompt = (
        f"Topic: {topic}\n"
        f"Current script segments:\n{context}\n\n"
        f"Rewrite ONLY segment [{segment_index}] applying this feedback: {feedback}\n"
        'Respond ONLY with JSON: {"text": "...", "visual_prompt": "...", "duration_estimate": 4.5}'
    )
    seg = await generate_json(SYSTEM_PROMPT, user_prompt, temperature=0.9)

    if "text" not in seg:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Segment regeneration returned no text")
    seg.setdefault("visual_prompt", full_script[segment_index].get("visual_prompt", ""))
    seg.setdefault("duration_estimate", round(len(str(seg["text"]).split()) / 2.5, 1))
    return seg
