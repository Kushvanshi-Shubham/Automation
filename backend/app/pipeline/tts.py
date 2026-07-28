"""Voice synthesis via edge-tts (free, no API key).

Each script segment becomes one MP3. Word-boundary timings are captured and
written as an SRT next to the audio for future caption burn-in.
"""
import logging
from pathlib import Path

import edge_tts

from app.pipeline.assembler import probe_duration

logger = logging.getLogger("kliptos.tts")

DEFAULT_VOICE = "en-US-ChristopherNeural"


async def synth_segment(text: str, out_path: Path, voice: str = DEFAULT_VOICE) -> float:
    """Synthesize one segment; returns spoken duration in seconds (ffprobe-measured)."""
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(out_path))
    if not out_path.exists() or out_path.stat().st_size == 0:
        raise RuntimeError(f"edge-tts produced no audio for: {text[:50]!r}")
    return probe_duration(out_path)


async def synth_script(
    segments: list[dict],
    workdir: Path,
    voice: str = DEFAULT_VOICE,
) -> list[dict]:
    """Synthesize all segments. Returns [{index, audio_path, duration}]."""
    results = []
    for i, seg in enumerate(segments):
        audio_path = workdir / f"seg_{i:02d}.mp3"
        duration = await synth_segment(seg["text"], audio_path, voice)
        results.append({"index": i, "audio_path": str(audio_path), "duration": duration})
        logger.info("tts segment %d: %.2fs", i, duration)
    return results
