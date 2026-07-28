"""Voice synthesis via edge-tts (free, no API key).

Each script segment becomes one MP3 plus word-boundary timings used for
caption burn-in. Durations are measured with ffprobe — edge-tts timing
events cover speech only, not trailing silence.
"""
import logging
from pathlib import Path

import edge_tts

from app.pipeline.assembler import probe_duration

logger = logging.getLogger("kliptos.tts")

DEFAULT_VOICE = "en-US-ChristopherNeural"


async def synth_segment(text: str, out_path: Path, voice: str = DEFAULT_VOICE) -> tuple[float, list[dict]]:
    """Synthesize one segment.

    Returns (duration_seconds, words) where words is
    [{"word": str, "start": float, "end": float}] in segment-local seconds.
    """
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
        raise RuntimeError(f"edge-tts produced no audio for: {text[:50]!r}")
    return probe_duration(out_path), words


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
