"""Script generation for 60-second vertical shorts (Gemini free-tier first, GPT-4o fallback).

Supports multiple creation styles plus a bring-your-own-script mode that
preserves the user's wording and only adds structure + visual prompts.
"""
import logging

from fastapi import HTTPException, status

from app.services.llm import generate_json

logger = logging.getLogger("kliptos.script_gen")

_BASE_RULES = """
Rules:
- The first segment is the HOOK: it must grab attention in under 3 seconds of speech.
- Each segment is 1-2 spoken sentences (max ~25 words) with ONE clear idea.
- Every segment includes a visual_prompt: a concrete, filmable description for stock-footage
  search or AI video generation (no text overlays, no brand names, no celebrity likenesses).
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

STYLE_PROMPTS = {
    "viral_story": (
        "You are a viral YouTube Shorts scriptwriter. You write tight, hook-driven, "
        "fact-checked storytelling scripts for 9:16 vertical videos narrated by a single voice. "
        "Create an open loop in the hook and end with a payoff + subtle rewatch/subscribe nudge (no begging)."
        + _BASE_RULES
    ),
    "news_update": (
        "You are a fast-paced news/update narrator for YouTube Shorts (think patch notes, game "
        "updates, tech releases, sports results). Lead with the single most important change, then "
        "the 2-4 key details, then what it means for the viewer. ONLY state facts you are confident "
        "in; if a detail is uncertain, phrase it as reported/rumored. No opinions."
        + _BASE_RULES
    ),
    "educational": (
        "You are an educational explainer scriptwriter for YouTube Shorts. Teach exactly ONE "
        "concept clearly: hook with a surprising question or misconception, explain with a concrete "
        "everyday analogy, end with the one-sentence takeaway the viewer should remember."
        + _BASE_RULES
    ),
    "commentary": (
        "You are a sharp, opinionated commentary scriptwriter for YouTube Shorts. Take a clear "
        "stance on the topic in first person, back it with 2-3 concrete reasons or examples, "
        "acknowledge the strongest counterpoint in one line, and end with a question that invites "
        "comments. Confident but never insulting."
        + _BASE_RULES
    ),
}

DEFAULT_STYLE = "viral_story"

CUSTOM_SCRIPT_PROMPT = """You are a video production assistant. The user wrote their OWN script.
Your job is ONLY to structure it — you must NOT rewrite, improve, shorten, or change their wording.

- Split the script into segments of 1-2 sentences exactly as written (fix nothing, not even typos).
- Add a visual_prompt per segment: concrete, filmable stock-footage description matching that line.
- Derive title/description/tags from the content.
- duration_estimate per segment at ~2.5 words/second.

Respond ONLY with JSON matching:
{
  "title": "...", "description": "...", "tags": ["..."],
  "segments": [{"text": "user's exact words", "visual_prompt": "...", "duration_estimate": 4.5}]
}"""


def _finalize(data: dict) -> dict:
    segments = data.get("segments") or []
    if not segments:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Script generation returned no segments")
    for seg in segments:
        seg.setdefault("duration_estimate", round(len(str(seg.get("text", "")).split()) / 2.5, 1))
    data["total_duration"] = round(sum(float(s["duration_estimate"]) for s in segments), 1)
    return data


async def generate_script(
    topic: str,
    hook_hint: str | None = None,
    tone: str = "engaging and curious",
    duration_seconds: int = 60,
    style: str = DEFAULT_STYLE,
    custom_instructions: str | None = None,
    model: str = "auto",
    user_keys: dict[str, str] | None = None,
    language: str = "English",
) -> dict:
    system = STYLE_PROMPTS.get(style, STYLE_PROMPTS[DEFAULT_STYLE])
    user_prompt = (
        f"Topic: {topic}\n"
        f"Tone: {tone}\n"
        f"Target duration: {duration_seconds} seconds\n"
        + (f"Write ALL narration text in {language}. Keep visual_prompt, title, description and tags in English.\n" if language != "English" else "")
        + (f"Hook inspiration (improve on it): {hook_hint}\n" if hook_hint else "")
        + (
            f"Additional creator instructions (follow them as long as they don't break the JSON format):\n{custom_instructions.strip()}\n"
            if custom_instructions else ""
        )
        + "Write the script now."
    )
    return _finalize(await generate_json(system, user_prompt, temperature=0.8, model=model, user_keys=user_keys))


async def format_custom_script(script_text: str, model: str = "auto", user_keys: dict[str, str] | None = None) -> dict:
    """Structure a user-written script without changing its wording."""
    user_prompt = f"User's script:\n---\n{script_text.strip()}\n---\nStructure it now."
    data = _finalize(
        await generate_json(CUSTOM_SCRIPT_PROMPT, user_prompt, temperature=0.2, model=model, user_keys=user_keys)
    )
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
    seg = await generate_json(STYLE_PROMPTS[DEFAULT_STYLE], user_prompt, temperature=0.9)

    if "text" not in seg:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Segment regeneration returned no text")
    seg.setdefault("visual_prompt", full_script[segment_index].get("visual_prompt", ""))
    seg.setdefault("duration_estimate", round(len(str(seg["text"]).split()) / 2.5, 1))
    return seg
