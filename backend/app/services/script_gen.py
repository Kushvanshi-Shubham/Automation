"""Script generation for vertical video, 15s to 5 minutes.

Supports multiple creation styles plus a bring-your-own-script mode that
preserves the user's wording and only adds structure + visual prompts.
"""
import logging

from fastapi import HTTPException, status

from app.services.llm import generate_json

logger = logging.getLogger("kliptos.script_gen")

# A segment is 1-2 sentences (~25 words max) at ~2.5 words/second, so it lands
# a little under 10s. Used to turn a target duration into a segment count.
SECONDS_PER_SEGMENT = 8.5

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

_POETIC_RULES = """
Rules:
- Each segment is ONE line/couplet, complete in itself. Never split a couplet
  across segments and never merge two into one.
- No hook, no open loop, no call to action, no subscribe nudge. Poetry earns
  attention by being good, not by withholding.
- Imagery over explanation. Never state the emotion outright ("she was sad");
  show the thing that carries it.
- Pacing is slow and deliberate: duration_estimate at ~1.2 words/second, so
  each line is given room to land.
- Every segment includes a visual_prompt: a still, atmospheric, filmable image
  (rain on glass, a cooling cup of chai, an empty road at dusk). No text
  overlays, no brand names, no celebrity likenesses.
- The last line is the strongest. End on it.

Respond ONLY with JSON matching:
{
  "title": "video title, <=95 chars, evocative, no clickbait",
  "description": "2-3 sentence description with 3 relevant hashtags",
  "tags": ["8-12 SEO tags"],
  "segments": [
    {"text": "one line of verse", "visual_prompt": "filmable atmospheric image",
     "duration_estimate": 6.0}
  ]
}"""

# Injected when the script has NO source document — the trend route passes only
# a title and a hook, so the model has nothing to be faithful TO. Left alone it
# fills the gap: a rejected render invented an unannounced vehicle patch, a
# named nerf, a missile-cooldown change and a "Diamond Depot" heist from a
# stream title, and delivered them in a breaking-news format under a real
# streamer's handle. Unattended standing orders publish that on a schedule.
UNSOURCED_RULES = """
GROUNDING: you have a headline and nothing else — no article, no patch notes, no
source. So you must NOT state specific checkable facts as if reported. Banned:
invented statistics, dates, prices, version numbers, patch-note details, named
features or updates that you cannot know exist, and anything attributed as a
quote to a real person.
Write about what the topic IS and why people care, which needs no source. Where a
specific detail would be required, either leave it out or frame it as an open
question ("everyone is asking whether...") rather than as fact. A vaguer script
that is true beats a specific one that is invented — a viewer who checks and
finds it false is gone for good, and so is the channel's credibility.
"""

# Two trends, one script. Injected as creator instructions rather than a
# style, because a mash-up has to work in EVERY format — a shayari mash-up
# and a news mash-up are still shayari and news.
MASHUP_RULES = """
MASH-UP: this script covers TWO trends as ONE story, never one after the other.
- The connection between them IS the hook. Open on what they share, or on the
  collision between them.
- Never alternate topic by topic ("first this trend... now the other trend").
  One through-line, with both trends serving it.
- The first trend leads; the second is the twist, the comparison, or the
  consequence.
- Do NOT invent a causal link. If the two genuinely have nothing to do with
  each other, say so and make the mismatch the point — an honest "these two
  should never be in the same sentence" is far better than a made-up
  connection a viewer will call out in the comments.
"""

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
    "poetry": (
        "You are a shayar writing original Urdu-flavoured Hindi poetry in Devanagari. "
        "You write sher: couplets where the second line turns, deepens or subverts the first. "
        "Your register is intimate and restrained — chai, rain, roads, waiting, distance, debt, "
        "small domestic objects carrying large feeling. Never explain the poem and never moralise. "
        "Do not write in English."
        + _POETIC_RULES
    ),
    "lyrical": (
        "You are writing the on-screen lines for a music-led vertical video. Short, rhythmic, "
        "repeatable lines that read like lyrics rather than narration — the music carries the "
        "emotion and the words punctuate it. Fragments are fine; full sentences often are not."
        + _POETIC_RULES
    ),
    "motivational": (
        "You are a motivational speechwriter for vertical video. Second person, present tense, "
        "short declarative sentences that build. Ground every claim in something concrete a "
        "person actually does tomorrow morning — no abstractions, no hustle cliches, no "
        "'grind' or 'nobody believed in me'. Earn the last line."
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
    reference_text: str | None = None,
    mashup_with: str | None = None,
) -> dict:
    system = STYLE_PROMPTS.get(style, STYLE_PROMPTS[DEFAULT_STYLE])
    # Stating the target alone is not enough: a segment is capped at ~25 words
    # (~10s), so the model writes a Shorts-shaped 5-7 of them whatever length
    # was asked for, and a 2-minute request came back at 60s. Spelling out the
    # segment count is what actually scales the script.
    segments_wanted = max(3, round(duration_seconds / SECONDS_PER_SEGMENT))
    user_prompt = (
        f"Topic: {topic}\n"
        + (f"Second trend to weave in: {mashup_with}\n{MASHUP_RULES}" if mashup_with else "")
        + f"Tone: {tone}\n"
        f"Target duration: {duration_seconds} seconds\n"
        f"Write EXACTLY {segments_wanted} segments so the narration fills the full "
        f"{duration_seconds} seconds. Do not stop early.\n"
        + (f"Write ALL narration text in {language}. Keep visual_prompt, title, description and tags in English.\n" if language != "English" else "")
        + (f"Hook inspiration (improve on it): {hook_hint}\n" if hook_hint else "")
        + (
            "Source material — base the script on the FACTS in it (do not invent numbers "
            f"or claims beyond it):\n---\n{reference_text.strip()}\n---\n"
            if reference_text else ""
        )
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
    style: str = DEFAULT_STYLE,
    model: str = "auto",
    user_keys: dict[str, str] | None = None,
) -> dict:
    """Rewrite one segment. Honours the video's style and the creator's own
    API key — a BYO user's rewrites must not fall back to platform keys."""
    context = "\n".join(f"[{i}] {s.get('text', '')}" for i, s in enumerate(full_script))
    user_prompt = (
        f"Topic: {topic}\n"
        f"Current script segments:\n{context}\n\n"
        f"Rewrite ONLY segment [{segment_index}] applying this feedback: {feedback}\n"
        'Respond ONLY with JSON: {"text": "...", "visual_prompt": "...", "duration_estimate": 4.5}'
    )
    system = STYLE_PROMPTS.get(style, STYLE_PROMPTS[DEFAULT_STYLE])
    seg = await generate_json(system, user_prompt, temperature=0.9, model=model, user_keys=user_keys)

    if "text" not in seg:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Segment regeneration returned no text")
    seg.setdefault("visual_prompt", full_script[segment_index].get("visual_prompt", ""))
    seg.setdefault("duration_estimate", round(len(str(seg["text"]).split()) / 2.5, 1))
    return seg
