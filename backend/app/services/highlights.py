"""Find the moments worth clipping in uploaded footage, by sound.

Kliptos already suggests highlights by *speech*: whisper transcribes the
upload and an LLM picks the best spoken moments, with a real reason for
each (see transcribe.suggest_highlights). That works well for streams,
commentary and podcasts.

It finds nothing in gameplay. A montage of gunfights has almost no
transcript to reason about, so the creator was told "no strong clip moments
found" and left to scrub the timeline themselves — which is exactly the
case Kliptos claims to serve. This module fills that gap from the audio
track instead, and `merge` combines the two so speech-picked moments still
lead where they exist.

**The signal is loudness, and loudness is a proxy, not a verdict.** In
gameplay and reaction footage the interesting moments are usually the loud
ones — a kill, a shout, a crowd, a crash — so peaks in short-window RMS
find them cheaply and deterministically. What it cannot do is understand
what happened: a loud menu jingle scores as well as a clutch play, and a
quiet, tense moment scores badly. Callers must present these as suggestions
the creator confirms, never as "the best bits".

Deliberately no ML here. A model that watched the video would be better and
would also mean a GPU, a download, and seconds-to-minutes per upload; this
runs in about the time it takes ffmpeg to decode the audio track alone.
"""
import logging
import subprocess
from pathlib import Path

import numpy as np

logger = logging.getLogger("kliptos.highlights")

# Audio is decoded mono at this rate purely to measure energy. 8 kHz is far
# below speech fidelity and that is fine — we never listen to it, and it
# keeps a 10-minute upload at ~10 MB of PCM instead of ~100 MB.
SAMPLE_RATE = 8000
# One RMS reading per 250 ms: short enough to catch a gunshot, long enough
# that a single click doesn't read as a highlight.
HOP_SECONDS = 0.25
# Lead-in matters more than the aftermath. A viewer needs the setup to
# understand the payoff, so the window opens BEFORE the peak.
LEAD_IN_SECONDS = 4.0
LEAD_OUT_SECONDS = 6.0
# Two windows closer than this are the same moment twice.
MIN_SEPARATION_SECONDS = 8.0
# A peak must be this many times the recording's own median energy to count.
# Relative, not absolute, so a quietly-recorded video is judged on its own
# dynamics rather than against a fixed dBFS.
MIN_PEAK_RATIO = 1.6


class NoAudioError(RuntimeError):
    """The upload has no usable audio track, so loudness tells us nothing."""


def _decode_mono_pcm(source: Path) -> np.ndarray:
    """Decode the audio track to a 1-D float array in [-1, 1]."""
    proc = subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(source),
         "-vn", "-ac", "1", "-ar", str(SAMPLE_RATE), "-f", "s16le", "-"],
        capture_output=True, timeout=600,
    )
    # A video with no audio stream exits non-zero here, which is a normal
    # outcome for silent screen recordings rather than a failure to report.
    if proc.returncode != 0 or not proc.stdout:
        raise NoAudioError((proc.stderr or b"").decode("utf-8", "replace")[-300:] or "no audio stream")
    pcm = np.frombuffer(proc.stdout, dtype="<i2")
    if pcm.size == 0:
        raise NoAudioError("audio track decoded to nothing")
    return pcm.astype(np.float32) / 32768.0


def _energy_envelope(samples: np.ndarray) -> np.ndarray:
    """RMS per HOP_SECONDS window."""
    hop = int(SAMPLE_RATE * HOP_SECONDS)
    usable = (samples.size // hop) * hop
    if usable == 0:
        return np.zeros(0, dtype=np.float32)
    frames = samples[:usable].reshape(-1, hop)
    return np.sqrt((frames.astype(np.float64) ** 2).mean(axis=1))


def find_highlights(
    source: Path,
    duration: float | None = None,
    limit: int = 5,
    min_seconds: float = 5.0,
    max_seconds: float = 90.0,
) -> list[dict]:
    """Ranked candidate clip windows, loudest moment first.

    Each entry is {"start", "end", "score", "peak_at"} with seconds rounded
    to 2dp. `score` is the peak's energy relative to the recording's median,
    so it is comparable within one upload and NOT across uploads.

    Returns [] when the audio is too uniform to single anything out — an
    empty list means "nothing stood out", which is a real answer and must
    not be dressed up as a suggestion.
    """
    envelope = _energy_envelope(_decode_mono_pcm(source))
    if envelope.size < 4:
        return []

    audio_length = envelope.size * HOP_SECONDS
    # Trust ffmpeg's own audio length over a container-reported duration that
    # may disagree, but never suggest a window past the end of the video.
    limit_seconds = min(audio_length, duration) if duration else audio_length

    median = float(np.median(envelope))
    if median <= 0:
        # Mostly-silent recording with occasional noise: fall back to the
        # mean so a division by ~0 cannot invent enormous scores.
        median = float(envelope.mean()) or 1e-9

    window = min(max(min_seconds, LEAD_IN_SECONDS + LEAD_OUT_SECONDS), max_seconds)
    picks: list[dict] = []
    # Greedy: take the loudest remaining frame, claim its neighbourhood,
    # repeat. Simpler than true peak-picking and it cannot return two
    # windows describing the same burst.
    remaining = envelope.copy()
    for _ in range(limit):
        idx = int(np.argmax(remaining))
        peak = float(remaining[idx])
        if peak <= 0 or peak / median < MIN_PEAK_RATIO:
            break
        peak_at = idx * HOP_SECONDS
        start = max(0.0, peak_at - LEAD_IN_SECONDS)
        end = min(limit_seconds, start + window)
        # Clipped by the end of the recording — pull the start back so the
        # window keeps its length instead of being silently truncated.
        if end - start < window:
            start = max(0.0, end - window)
        if end - start >= min_seconds:
            picks.append({
                "start": round(start, 2),
                "end": round(end, 2),
                "peak_at": round(peak_at, 2),
                "score": round(peak / median, 2),
            })
        blank = int(MIN_SEPARATION_SECONDS / HOP_SECONDS)
        remaining[max(0, idx - blank):idx + blank] = 0.0
        if not remaining.any():
            break

    return picks


# Total suggestions shown for one upload. Matches the speech-based cap: past
# about eight the creator is scrolling a list instead of choosing.
MAX_SUGGESTIONS = 8


def describe(pick: dict) -> dict:
    """Turn a raw window into something the clips list can render.

    The existing UI expects title + reason on every highlight, and those
    strings are the only place a creator learns HOW a moment was chosen.
    So the reason states the actual measurement rather than implying we
    understood the footage.
    """
    return {
        "start": pick["start"],
        "end": pick["end"],
        "title": "Loud moment",
        "reason": f"{pick['score']:g}x louder than the rest of this recording",
        "source": "sound",
    }


def merge(speech: list[dict], sound: list[dict], limit: int = MAX_SUGGESTIONS) -> list[dict]:
    """Speech-picked highlights first, topped up with loud moments.

    Speech leads because an LLM that read the transcript can say WHY a
    moment matters, which loudness never can. Sound only fills the
    remaining slots — and never re-suggests a moment already covered, since
    two entries for one burst just wastes the creator's attention.
    """
    out = [{**h, "source": h.get("source", "speech")} for h in speech][:limit]
    for pick in sound:
        if len(out) >= limit:
            break
        # The peak is the moment itself; if it already sits inside a
        # suggestion, that moment is covered however the window was framed.
        peak = pick.get("peak_at", (pick["start"] + pick["end"]) / 2)
        if any(h["start"] <= peak <= h["end"] for h in out):
            continue
        out.append(describe(pick))
    return out
