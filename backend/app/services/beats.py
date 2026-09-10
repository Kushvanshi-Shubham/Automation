"""Find the beat grid of a music track, so montage cuts can land on it.

A montage whose cuts fall on the beat reads as edited; the same clips cut
at arbitrary lengths read as a dump. This is the difference, and it is
cheap: the tempo of a track is one autocorrelation away.

**What this does and does not do.** It finds the tempo and where the beats
sit, then `snap_durations` nudges each clip's length to end on a beat. It
does NOT move the action to the beat — a kill that happens off-beat still
happens off-beat. The cut lands on the beat; the content does not shift.

Deliberately no librosa. It would be more accurate on live drumming and
tempo changes, and it would also add a large dependency plus scipy for a
job that steady-tempo library music makes easy. If we ever accept creator-
supplied music with rubato, revisit that trade.
"""
import logging
import subprocess
from pathlib import Path

import numpy as np

logger = logging.getLogger("kliptos.beats")

# Fine enough to place a beat within ~10ms, which is well under the ~30ms
# at which a listener notices a cut being early or late.
HOP_SECONDS = 0.01
SAMPLE_RATE = 22050
# Dance/hip-hop/lo-fi library music lives here. Searching wider invites
# octave errors, where 90 BPM is detected as 45 or 180.
MIN_BPM, MAX_BPM = 70.0, 180.0
# Below this, the autocorrelation peak is not meaningfully stronger than
# the noise floor and snapping would move cuts for no audible reason.
MIN_CONFIDENCE = 1.25
# Fewer distinct onsets than this is not a rhythm. Twenty seconds at the
# slowest tempo we search is ~23 beats, so this stays well inside what any
# real music track produces.
MIN_ONSETS = 8


class NoBeatError(RuntimeError):
    """No steady pulse found — snapping cuts to it would be arbitrary."""


def _onset_envelope(path: Path) -> np.ndarray:
    """Per-hop rise in energy: high where a new sound starts."""
    proc = subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(path),
         "-vn", "-ac", "1", "-ar", str(SAMPLE_RATE), "-f", "s16le", "-"],
        capture_output=True, timeout=300,
    )
    if proc.returncode != 0 or not proc.stdout:
        raise NoBeatError("could not decode audio")
    samples = np.frombuffer(proc.stdout, dtype="<i2").astype(np.float32) / 32768.0

    hop = int(SAMPLE_RATE * HOP_SECONDS)
    usable = (samples.size // hop) * hop
    if usable < hop * 200:  # under ~2s of audio
        raise NoBeatError("track too short to find a tempo")
    energy = np.sqrt((samples[:usable].reshape(-1, hop) ** 2).mean(axis=1))
    # Half-wave rectified difference: onsets are where energy JUMPS, not
    # where it is merely high — a sustained pad is loud but has no pulse.
    #
    # Prepending 0 rather than energy[0] on purpose. A track that opens on
    # the downbeat has its loudest onset in the first hop, and treating that
    # hop as "no change" threw the beat away — phase then locked onto the
    # SECOND beat and every cut sat one beat off the grid.
    onset = np.maximum(np.diff(energy, prepend=0.0), 0.0)
    # ...but that prepended value is itself an artificial onset, and on a
    # steady tone it is the ONLY one — a single spike autocorrelates well
    # enough to fake a tempo. A real pulse has many onsets, so require them.
    peak = float(onset.max())
    if peak <= 0:
        raise NoBeatError("no onsets at all")
    if int((onset > peak * 0.1).sum()) < MIN_ONSETS:
        raise NoBeatError("too few onsets to call it a pulse")
    return onset


def detect(path: Path) -> dict:
    """{"bpm", "period", "phase", "confidence"} for a music file.

    `phase` is the offset of the first beat from the start of the track, so
    a caller looping the track from 0 knows where the grid begins.
    Raises NoBeatError when nothing steady is found.
    """
    onset = _onset_envelope(path)
    onset = onset - onset.mean()

    # FFT autocorrelation — np.correlate on a 3-minute envelope is O(n^2)
    # and takes seconds; this is milliseconds.
    n = 1 << (2 * onset.size - 1).bit_length()
    spectrum = np.fft.rfft(onset, n)
    acf = np.fft.irfft(spectrum * np.conjugate(spectrum))[: onset.size]
    if acf[0] <= 0:
        raise NoBeatError("silent or constant audio")
    acf /= acf[0]

    # ceil / floor, not int(): a SHORTER lag is a FASTER tempo, so
    # truncating the fast end downwards searched past MAX_BPM and could
    # return 182 bpm from a 70-180 search.
    lo = int(np.ceil(60.0 / MAX_BPM / HOP_SECONDS))
    hi = int(np.floor(60.0 / MIN_BPM / HOP_SECONDS))
    if hi >= acf.size:
        raise NoBeatError("track too short for the tempo range")
    window = acf[lo:hi + 1]
    lag = lo + int(np.argmax(window))
    peak = float(acf[lag])
    # Compared against the average correlation across the search range, so
    # "there is a pulse" means a peak that stands out, not just a maximum
    # (every signal has a maximum).
    baseline = float(np.mean(np.abs(window))) or 1e-9
    confidence = peak / baseline
    if confidence < MIN_CONFIDENCE:
        raise NoBeatError(f"no steady pulse (confidence {confidence:.2f})")

    # Parabolic interpolation around the peak. Without it the period is
    # quantised to 10ms, and a 3ms error compounds into ~90ms of drift over
    # 30 beats — enough for the later cuts in a montage to sit off the grid.
    if 0 < lag < acf.size - 1:
        a, b, c = float(acf[lag - 1]), float(acf[lag]), float(acf[lag + 1])
        denom = a - 2 * b + c
        if denom != 0:
            # Clamped: interpolation can nudge the peak just outside the
            # searched range, and returning 182 bpm from a 70-180 search
            # breaks the contract the caller was given.
            lag = min(max(lag + 0.5 * (a - c) / denom, float(lo)), float(hi))
    period = lag * HOP_SECONDS
    # Phase: slide a pulse train over the onset envelope and keep the offset
    # with the most onset energy sitting on beats.
    # Octave errors are tolerable here and worth stating: if a 90 BPM track
    # reads as 180, cuts land on eighth notes instead of quarter notes and
    # still sit ON the grid. It is only a wrong tempo, never a wrong beat.
    #
    # The grid must be built from the FRACTIONAL period. Striding the array
    # by a whole number of hops instead drifts a third of a hop per beat,
    # which over 30 beats is 0.1s — enough that the best offset came back
    # a whole beat out, putting every cut on the off-beat.
    step = max(1, int(round(period / HOP_SECONDS)))
    beat_count = max(1, int((onset.size * HOP_SECONDS) / period))
    grid = np.arange(beat_count) * period
    best_offset, best_score = 0, -1.0
    for offset in range(step):
        idx = np.rint((offset * HOP_SECONDS + grid) / HOP_SECONDS).astype(int)
        idx = idx[idx < onset.size]
        score = float(onset[idx].sum()) if idx.size else 0.0
        if score > best_score:
            best_offset, best_score = offset, score

    return {
        "bpm": round(60.0 / period, 1),
        "period": round(period, 4),
        "phase": round(best_offset * HOP_SECONDS, 4),
        "confidence": round(confidence, 2),
    }


def snap_durations(
    durations: list[float],
    period: float,
    phase: float = 0.0,
    min_seconds: float = 5.0,
) -> list[float]:
    """Nudge each clip length so every cut falls on a beat.

    The music is looped from its own start, so the grid sits at
    `phase + k * period`. The FIRST cut therefore has to absorb the phase;
    every later one is a whole number of beats after it.

    Lengths only ever move by less than one beat, so at 120 BPM no clip
    shifts by more than half a second — the rhythm is gained without
    losing a visible amount of the moment. A clip that would fall under
    `min_seconds` is rounded UP instead, because shipping a 4-second clip
    to hit a beat trades the wrong thing.
    """
    if period <= 0:
        return list(durations)

    out: list[float] = []
    elapsed = 0.0
    for i, wanted in enumerate(durations):
        target = elapsed + wanted
        # Where is the nearest beat to the end of this clip?
        beats = round((target - phase) / period)
        snapped = phase + beats * period
        if i == 0 and snapped <= 0:
            snapped = phase + period
        length = snapped - elapsed
        # Never shorten below the floor, and never invert.
        while length < min_seconds:
            beats += 1
            length = (phase + beats * period) - elapsed
        out.append(round(length, 3))
        elapsed += out[-1]
    return out
