"""Voice synthesis via edge-tts (free, no API key).

Each script segment becomes one MP3 plus word-boundary timings used for
caption burn-in. Durations are measured with ffprobe — edge-tts timing
events cover speech only, not trailing silence.
"""
import logging
from pathlib import Path

import edge_tts

from app.core.retry import with_retries
from app.pipeline.assembler import probe_duration

logger = logging.getLogger("kliptos.tts")

DEFAULT_VOICE = "en-US-ChristopherNeural"


async def _synth_once(text: str, out_path: Path, voice: str) -> tuple[float, list[dict]]:
    # boundary= must be requested explicitly in edge-tts 7.x, else no events.
    communicate = edge_tts.Communicate(text, voice, boundary="WordBoundary")
    words: list[dict] = []
    with open(out_path, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                start = chunk["offset"] / 10_000_000
                words.append(
                    {
                        "word": chunk["text"],
                        "start": round(start, 3),
                        "end": round(start + chunk["duration"] / 10_000_000, 3),
                    }
                )
    if not out_path.exists() or out_path.stat().st_size == 0:
        # Empty output usually means the stream dropped mid-way — treat as
        # transient so the retry wrapper takes another shot.
        raise RuntimeError(f"edge-tts produced no audio (connection reset?) for: {text[:50]!r}")
    return probe_duration(out_path), words


async def synth_segment(text: str, out_path: Path, voice: str = DEFAULT_VOICE) -> tuple[float, list[dict]]:
    """Synthesize one segment (retried — edge-tts is a free network service
    and drops connections now and then).

    Returns (duration_seconds, words) where words is
    [{"word": str, "start": float, "end": float}] in segment-local seconds.
    """
    return await with_retries(lambda: _synth_once(text, out_path, voice), label="edge-tts")


async def synth_script(
    segments: list[dict],
    workdir: Path,
    voice: str = DEFAULT_VOICE,
) -> list[dict]:
    """Synthesize all segments. Returns [{index, audio_path, duration, words}]."""
    results = []
    for i, seg in enumerate(segments):
        audio_path = workdir / f"seg_{i:02d}.mp3"
        duration, words = await synth_segment(seg["text"], audio_path, voice)
        results.append({"index": i, "audio_path": str(audio_path), "duration": duration, "words": words})
        logger.info("tts segment %d: %.2fs, %d word events", i, duration, len(words))
    return results
