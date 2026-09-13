"""How long each silence in a recitation should be.

Owner, after hearing the first evenly-paced shayari: "every shayari are never
same — sometimes long gap sometimes short, the deep breath, heavy hearts."

He is right, and it was measurable rather than a matter of opinion. Three
Creative-Commons recordings of live Urdu/Sindhi recitation were pulled from
archive.org (a mushaira under CC BY 3.0, an Urdu reading under CC BY 2.5, and
an International Sindhi Mushaira under CC BY-NC 4.0 — downloaded for analysis
only, nothing redistributed) and every silence in 37 minutes of it was
measured with ffmpeg `silencedetect`. 831 pauses:

    min    p25    median  p75    p90    max
    0.25   0.38   0.53    0.86   1.26   7.85     (seconds)

Two findings decide this module:

1. **The spread is 3.3x between p25 and p90, and the distribution is heavily
   right-skewed** — 46% of pauses are under half a second, but a long tail
   runs past two. A single fixed value is not a slightly-wrong approximation
   of that; it has zero spread, which is the one property the real thing
   most obviously has.

2. **A pause longer than twice the median lands roughly every third pause**,
   found independently in both recordings (15% and 12% of pauses, median
   spacing 3). Those are the structural breaks — the end of a thought — and
   with one couplet per segment they fall almost exactly where a sher ends.

What the measurement does NOT tell us is *why* any individual pause was long:
that needs the audio aligned to the text, which we do not have. So the factors
below are informed judgement about what makes a reciter hold a line, checked
only against the overall shape the recordings do show. They are taste, and
they should be retuned by listening, not by staring at the numbers.
"""
from __future__ import annotations

import hashlib
import re

# Straight from the measured distribution above.
MEDIAN_PAUSE = 0.53
# The ceiling sits just above the measured p90 of 1.26s, not at the observed
# maximum: the longest silences in the recordings are between poets, with
# applause in them, not inside a recitation. The owner has already called one
# version "too slow", so the tail is deliberately clipped short of dead air.
MIN_PAUSE, MAX_PAUSE = 0.25, 1.9

# Sentence-final marks: the danda (Devanagari full stop), the Urdu full stop,
# and their Latin equivalents. A line that ENDS on one has finished a thought
# and is held; one ending on a comma or a dash is still running into the next.
_FINAL = ("।", "۔", ".", "!", "?", "…")
_RUNNING = (",", "،", "—", "-", ";", ":")

# A mood changes how long a reciter sits in a silence. Dard is held; hausla
# drives forward and refuses to wallow. These are judgement, not measurement.
MOOD_FACTOR: dict[str, float] = {
    "sad": 1.25,
    "nostalgic": 1.15,
    "love": 1.05,
    "romantic": 1.05,
    "calm": 1.10,
    "chill": 1.10,
    "motivational": 0.85,
    "hausla": 0.85,
    "hype": 0.75,
}


def _jitter(text: str, spread: float = 0.18) -> float:
    """A stable ±spread wobble derived from the line itself.

    Real pauses are never twice the same length, but a render must be
    reproducible — regenerating the same script has to give the same video,
    or nobody can tell whether a change they made did anything. Hashing the
    line gives variation that is arbitrary but fixed.
    """
    h = int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:8], 16)
    return 1.0 + ((h % 2000) / 1000.0 - 1.0) * spread


def _words(text: str) -> int:
    return max(1, len(re.findall(r"\S+", text)))


def _ending_factor(line: str) -> float:
    stripped = line.rstrip()
    if stripped.endswith(_FINAL):
        return 1.20
    if stripped.endswith(_RUNNING):
        return 0.80
    return 1.0


def _breath_factor(line: str, average_words: float) -> float:
    """A long line spends more air, so the breath after it is longer.

    Square-rooted deliberately: a line twice as long does not need twice the
    recovery, and un-damped this swamped every other factor.
    """
    ratio = _words(line) / max(1.0, average_words)
    return min(1.35, max(0.75, ratio ** 0.5))


def plan(
    segments: list[dict],
    *,
    line_pause: float,
    pause_after: float,
    mood: str | None = None,
) -> list[dict]:
    """Per-segment silences: `line` between the misras, `after` between shers.

    `line_pause` and `pause_after` are the format's base values. A format that
    asks for no silence gets none — this must never invent a pause for a news
    update, so a zero base stays zero throughout.
    """
    if not segments:
        return []

    mood_factor = MOOD_FACTOR.get((mood or "").strip().lower(), 1.0)
    average_words = sum(_words(s.get("text") or "") for s in segments) / len(segments)
    last = len(segments) - 1

    out = []
    for i, seg in enumerate(segments):
        text = seg.get("text") or ""
        lines = [ln for ln in text.splitlines() if ln.strip()]
        first_line = lines[0] if lines else text

        # Between the two misras: driven by how the FIRST line ends, because
        # that is the line the reciter is holding when the silence happens.
        inside = (
            line_pause
            * mood_factor
            * _ending_factor(first_line)
            * _breath_factor(first_line, average_words)
            * _jitter(first_line)
        )

        # Between shers: the structural break, and the one the recordings show
        # running long. The silence before the LAST sher is the longest in the
        # piece — the closing couplet is the one that has to land, and it
        # lands out of quiet.
        weight = 1.0
        if i == last:
            weight = 0.0          # nothing follows the final line but the end
        elif i == last - 1:
            weight = 1.35         # the run-up to the closing sher
        elif i == 0:
            weight = 0.9          # the opening moves before it settles

        after = (
            pause_after
            * weight
            * mood_factor
            * _ending_factor(text)
            * _breath_factor(text, average_words)
            * _jitter(text + "|after")
        )

        out.append({
            "line": _clamp(inside) if line_pause > 0 else 0.0,
            "after": _clamp(after) if (pause_after > 0 and weight > 0) else 0.0,
        })
    return out


def _clamp(seconds: float) -> float:
    return round(min(MAX_PAUSE, max(MIN_PAUSE, seconds)), 2)
