"""Studio-grade narration (Cartesia, ElevenLabs) — the Pro voice lane.

edge-tts is free and fine; these are the voices that make a faceless
short sound like a person. Both providers are BYO-key friendly: the
creator's own key is used when they have one, otherwise the platform key
and the render costs extra credits.

Word timings: neither provider returns them from the plain audio
endpoint, so we transcribe the generated speech with the Whisper model
we already ship. That is provider-agnostic and, unlike the TTS engine's
own guess, matches what was actually spoken.
"""
import asyncio
import logging
from pathlib import Path

import httpx

from app.config import settings

logger = logging.getLogger("kliptos.premium_voice")

CARTESIA = "cartesia"
ELEVENLABS = "elevenlabs"
PROVIDERS = (CARTESIA, ELEVENLABS)

CARTESIA_BASE = "https://api.cartesia.ai"
CARTESIA_VERSION = "2024-06-10"
CARTESIA_MODEL = "sonic-2"
ELEVEN_BASE = "https://api.elevenlabs.io/v1"
ELEVEN_MODEL = "eleven_multilingual_v2"

# Keep the catalogue small enough to choose from; the creator's own cloned
# voices always come first (see list_voices).
MAX_VOICES = 60


class VoiceError(Exception):
    """User-facing narration failure; message is safe to show."""


def platform_key(provider: str) -> str | None:
    return {
        CARTESIA: settings.CARTESIA_API_KEY,
        ELEVENLABS: settings.ELEVENLABS_API_KEY,
    }.get(provider)


def available_providers(user_keys: dict[str, str] | None = None) -> list[str]:
    """Providers this user can actually narrate with."""
    keys = user_keys or {}
    return [p for p in PROVIDERS if keys.get(p) or platform_key(p)]


def _key_for(provider: str, user_keys: dict[str, str] | None) -> tuple[str, bool]:
    """(api_key, is_own). The creator's key always wins — it's their spend."""
    own = (user_keys or {}).get(provider)
    if own:
        return own, True
    platform = platform_key(provider)
    if not platform:
        raise VoiceError(f"{provider.title()} narration isn't configured — add your own key in Settings.")
    return platform, False


async def list_voices(provider: str, user_keys: dict[str, str] | None = None) -> list[dict]:
    """[{id, name, language, provider, cloned}] — cloned voices first."""
    api_key, is_own = _key_for(provider, user_keys)
    async with httpx.AsyncClient(timeout=25) as client:
        if provider == CARTESIA:
            resp = await client.get(
                f"{CARTESIA_BASE}/voices",
                headers={"X-API-Key": api_key, "Cartesia-Version": CARTESIA_VERSION},
            )
            if resp.status_code != 200:
                raise VoiceError("Couldn't reach Cartesia with that key.")
            rows = resp.json()
            rows = rows if isinstance(rows, list) else rows.get("data", [])
            voices = [
                {
                    "id": v.get("id"),
                    "name": v.get("name") or "Unnamed",
                    "language": v.get("language") or "en",
                    "provider": CARTESIA,
                    # A voice the creator made on their own account.
                    "cloned": is_own and not v.get("is_public", True),
                }
                for v in rows
                if v.get("id")
            ]
        else:
            resp = await client.get(f"{ELEVEN_BASE}/voices", headers={"xi-api-key": api_key})
            if resp.status_code != 200:
                raise VoiceError("Couldn't reach ElevenLabs with that key.")
            voices = [
                {
                    "id": v.get("voice_id"),
                    "name": v.get("name") or "Unnamed",
                    "language": (v.get("labels") or {}).get("language", "en"),
                    "provider": ELEVENLABS,
                    "cloned": (v.get("category") or "") == "cloned",
                }
                for v in resp.json().get("voices", [])
                if v.get("voice_id")
            ]

    voices.sort(key=lambda v: (not v["cloned"], v["name"].lower()))
    return voices[:MAX_VOICES]


async def synthesize(
    text: str,
    out_path: Path,
    voice_id: str,
    provider: str,
    user_keys: dict[str, str] | None = None,
    language: str = "en",
) -> Path:
    """Render one segment of narration to out_path (mp3)."""
    if provider not in PROVIDERS:
        raise VoiceError(f"Unknown narration provider '{provider}'.")
    api_key, is_own = _key_for(provider, user_keys)

    async with httpx.AsyncClient(timeout=90) as client:
        if provider == CARTESIA:
            resp = await client.post(
                f"{CARTESIA_BASE}/tts/bytes",
                headers={
                    "X-API-Key": api_key,
                    "Cartesia-Version": CARTESIA_VERSION,
                    "Content-Type": "application/json",
                },
                json={
                    "model_id": CARTESIA_MODEL,
                    "transcript": text,
                    "voice": {"mode": "id", "id": voice_id},
                    "language": (language or "en")[:2].lower(),
                    "output_format": {"container": "mp3", "sample_rate": 44100, "bit_rate": 128000},
                },
            )
        else:
            resp = await client.post(
                f"{ELEVEN_BASE}/text-to-speech/{voice_id}",
                headers={"xi-api-key": api_key, "Content-Type": "application/json"},
                json={
                    "text": text,
                    "model_id": ELEVEN_MODEL,
                    "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
                },
            )

    if resp.status_code != 200:
        detail = resp.text[:200]
        logger.warning("%s tts failed (%s): %s", provider, resp.status_code, detail)
        if resp.status_code in (401, 403):
            raise VoiceError(f"That {provider.title()} key was rejected — check it in Settings.")
        if resp.status_code == 429:
            raise VoiceError(f"{provider.title()} is rate-limiting or out of quota right now.")
        raise VoiceError(f"{provider.title()} couldn't produce that narration.")
    if not resp.content:
        raise VoiceError(f"{provider.title()} returned empty audio.")

    out_path.write_bytes(resp.content)
    if not is_own:  # only meter what we pay for
        from app.services.costs import track

        track("premium_voice")
    return out_path


async def synth_with_timings(
    text: str,
    out_path: Path,
    voice_id: str,
    provider: str,
    user_keys: dict[str, str] | None = None,
    language: str = "en",
) -> tuple[float, list[dict]]:
    """Narrate, then recover word timings by transcribing the result.

    Returns (duration, words) in the same shape edge-tts produces, so the
    caption builder doesn't care which voice engine was used.
    """
    from app.pipeline import transcribe
    from app.pipeline.assembler import probe_duration

    await synthesize(text, out_path, voice_id, provider, user_keys=user_keys, language=language)
    duration = probe_duration(out_path)
    try:
        # Whisper is CPU-bound sync work — keep it off the event loop.
        result = await asyncio.to_thread(transcribe.transcribe, out_path)
        # Whisper hands back numpy floats — cast so these stay plain JSON.
        words = [
            {"word": w["word"], "start": float(w["start"]), "end": float(w["end"])}
            for seg in (result.get("segments") or [])
            for w in (seg.get("words") or [])
        ]
    except Exception as exc:  # captions fall back to even spacing
        logger.warning("could not time premium narration, using fallback cues: %s", exc)
        words = []
    return duration, words
