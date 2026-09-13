"""Voice synthesis via edge-tts (free, no API key).

Each script segment becomes one MP3 plus word-boundary timings used for
caption burn-in. Durations are measured with ffprobe — edge-tts timing
events cover speech only, not trailing silence.
"""
import logging
from pathlib import Path

import edge_tts

from app.core.retry import with_retries
from app.pipeline.assembler import _run as _ffmpeg, probe_duration

logger = logging.getLogger("kliptos.tts")

DEFAULT_VOICE = "en-US-ChristopherNeural"

# edge-tts reads everything at one conversational pace. A shayari asked for
# "slow and deliberate" and got news-reader delivery, because nothing here
# could slow it down. Formats declare words_per_second; this converts that
# into the rate edge-tts understands, relative to its natural ~2.5 w/s.
BASE_WORDS_PER_SECOND = 2.5
MIN_RATE_PCT, MAX_RATE_PCT = -45, 25


def rate_for(words_per_second: float | None) -> str | None:
    """An edge-tts rate string like "-40%", or None to leave it alone."""
    if not words_per_second or words_per_second <= 0:
        return None
    pct = round((words_per_second / BASE_WORDS_PER_SECOND - 1) * 100)
    pct = max(MIN_RATE_PCT, min(MAX_RATE_PCT, pct))
    return None if pct == 0 else f"{pct:+d}%"


# --- pauses ----------------------------------------------------------------
#
# Owner's verdict on the first slow-narration shayari: "too slow, the gap is
# weird — if you download audio of shayari you will understand it". He is
# right, and the mistake was structural. Real shayari is NOT a slowed-down
# voice. The delivery is close to normal speed and the poetry lives in the
# SILENCE — between the two misras of a sher, and between one sher and the
# next. We were doing the opposite: dragging edge-tts to its -45% floor
# (which sounds like a slowed recording, not a recitation) and then putting
# the gap in the picture as a fade, where it reads as a glitch because the
# voice never actually stops.
#
# So the pause belongs here, in the audio. The visual just holds.

def _pad_audio(src: Path, seconds: float, out: Path) -> None:
    """Append exactly `seconds` of silence to an audio file."""
    _ffmpeg(["-i", str(src), "-af", f"apad=pad_dur={seconds:.2f}",
             "-c:a", "libmp3lame", "-q:a", "4", str(out)])


def _concat_audio(parts: list[Path], out: Path) -> None:
    listing = out.with_suffix(".txt")
    listing.write_text("\n".join(f"file '{p.name}'" for p in parts), encoding="utf-8")
    _ffmpeg(["-f", "concat", "-safe", "0", "-i", listing.name,
             "-c:a", "libmp3lame", "-q:a", "4", out.name], cwd=out.parent)


def utterances(text: str, line_pause: float) -> list[str]:
    """Split a segment into separately-spoken pieces.

    A sher is two misras. When the format asks for a pause between them they
    have to be synthesized apart, because no TTS engine will hold a silence
    that long on its own — it reads a line break as a comma at most.
    """
    if line_pause <= 0:
        return [text]
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    return lines if len(lines) > 1 else [text]


async def _synth_once(text: str, out_path: Path, voice: str, rate: str | None = None) -> tuple[float, list[dict]]:
    # boundary= must be requested explicitly in edge-tts 7.x, else no events.
    kwargs = {"boundary": "WordBoundary"}
    if rate:
        kwargs["rate"] = rate
    communicate = edge_tts.Communicate(text, voice, **kwargs)
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


async def synth_segment(
    text: str, out_path: Path, voice: str = DEFAULT_VOICE, rate: str | None = None
) -> tuple[float, list[dict]]:
    """Synthesize one segment (retried — edge-tts is a free network service
    and drops connections now and then).

    Returns (duration_seconds, words) where words is
    [{"word": str, "start": float, "end": float}] in segment-local seconds.
    """
    result = await with_retries(lambda: _synth_once(text, out_path, voice, rate), label="edge-tts")
    from app.services.costs import track

    track("tts_segment")
    return result


async def synth_script(
    segments: list[dict],
    workdir: Path,
    voice: str = DEFAULT_VOICE,
    provider: str | None = None,
    user_keys: dict[str, str] | None = None,
    language: str = "en",
    words_per_second: float | None = None,
    line_pause: float = 0.0,
    pause_after: float = 0.0,
    mood: str | None = None,
) -> list[dict]:
    """Synthesize all segments. Returns [{index, audio_path, duration, words}].

    provider=None uses free edge-tts; "cartesia"/"elevenlabs" narrate with
    the Pro voice lane (services/premium_voice.py), which returns the same
    shape so captions work identically either way.
    """
    results = []
    rate = rate_for(words_per_second)
    # Every silence its own length. A single fixed value has zero spread,
    # which is the one property real recitation most obviously has.
    from app.services import rhythm

    silences = rhythm.plan(segments, line_pause=line_pause,
                           pause_after=pause_after, mood=mood)

    async def _speak(text: str, path: Path) -> tuple[float, list[dict]]:
        """One utterance, through whichever voice lane is selected."""
        if provider:
            from app.services import premium_voice

            return await premium_voice.synth_with_timings(
                text, path, voice, provider, user_keys=user_keys, language=language,
            )
        return await synth_segment(text, path, voice, rate=rate)

    for i, seg in enumerate(segments):
        audio_path = workdir / f"seg_{i:02d}.mp3"
        inside, trailing = silences[i]["line"], silences[i]["after"]
        pieces = utterances(seg["text"], inside)

        if len(pieces) == 1 and trailing <= 0:
            duration, words = await _speak(seg["text"], audio_path)
        else:
            # Speak each piece, pad it with the silence that follows it, then
            # join. Word timings are in piece-local seconds and have to be
            # shifted by everything already on the timeline, or the captions
            # drift further out of sync with every pause added.
            padded, words, offset = [], [], 0.0
            for j, piece in enumerate(pieces):
                raw = workdir / f"seg_{i:02d}_p{j:02d}.mp3"
                _, piece_words = await _speak(piece, raw)
                gap = inside if j < len(pieces) - 1 else trailing
                if gap > 0:
                    held = workdir / f"seg_{i:02d}_q{j:02d}.mp3"
                    _pad_audio(raw, gap, held)
                else:
                    held = raw
                words.extend({**w, "start": w["start"] + offset, "end": w["end"] + offset}
                             for w in piece_words)
                offset += probe_duration(held)
                padded.append(held)
            if len(padded) == 1:
                padded[0].replace(audio_path)
            else:
                _concat_audio(padded, audio_path)
            duration = probe_duration(audio_path)

        results.append({"index": i, "audio_path": str(audio_path), "duration": duration, "words": words})
        logger.info("tts segment %d (%s): %.2fs, %d word events, %d piece(s), "
                    "pauses %.2f/%.2f", i, provider or "edge", duration,
                    len(words), len(pieces), inside, trailing)
    return results
