"""Beat detection and cut snapping.

Tempo is checked against click tracks of a KNOWN bpm, because the only way
to know a tempo detector works is to give it a tempo you chose yourself.
The library tracks are then checked for plausibility rather than exactness
— nobody knows the true bpm of those, so asserting one would be inventing
a fact.
"""
import shutil
import subprocess
from pathlib import Path

import pytest

from app.services import beats

pytestmark = pytest.mark.skipif(
    shutil.which("ffmpeg") is None, reason="ffmpeg not installed"
)


def _click_track(path: Path, bpm: float, seconds: int = 20):
    """A short tone on every beat — an unambiguous pulse at a known tempo."""
    period = 60.0 / bpm
    subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
         "-f", "lavfi", "-i",
         f"aevalsrc='0.9*sin(2*PI*880*t)*lt(mod(t,{period}),0.03)':d={seconds}:s=22050",
         str(path)],
        capture_output=True, timeout=120, check=True,
    )


@pytest.mark.parametrize("bpm", [90, 120, 140])
def test_tempo_is_found_within_a_bpm(tmp_path, bpm):
    track = tmp_path / f"click_{bpm}.wav"
    _click_track(track, bpm)

    got = beats.detect(track)
    assert abs(got["bpm"] - bpm) < 1.0, got
    assert got["confidence"] > beats.MIN_CONFIDENCE * 2, "a click track should be unambiguous"


@pytest.mark.parametrize("bpm", [90, 120, 140])
def test_phase_lands_on_a_beat(tmp_path, bpm):
    """The grid must sit ON the pulse, not a beat away from it.

    Regression: striding the onset array by a whole number of hops drifted
    a third of a hop per beat, and the best offset came back a full beat
    out — which would have put every montage cut on the off-beat.
    """
    track = tmp_path / f"click_{bpm}.wav"
    _click_track(track, bpm)

    got = beats.detect(track)
    # Distance from the detected phase to the nearest true beat (the clicks
    # start at t=0, so beats are at multiples of the period).
    to_beat = min(got["phase"], abs(got["period"] - got["phase"]))
    assert to_beat <= 0.02, f"phase is {to_beat * 1000:.0f}ms off the beat"


def test_a_steady_tone_has_no_beat(tmp_path):
    """Loud is not the same as rhythmic — a pad must not fake a tempo."""
    track = tmp_path / "drone.wav"
    subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
         "-f", "lavfi", "-i", "sine=frequency=220:duration=20:sample_rate=22050",
         str(track)],
        capture_output=True, timeout=120, check=True,
    )
    with pytest.raises(beats.NoBeatError):
        beats.detect(track)


def test_silence_has_no_beat(tmp_path):
    track = tmp_path / "silence.wav"
    subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
         "-f", "lavfi", "-i", "anullsrc=r=22050:cl=mono", "-t", "10", str(track)],
        capture_output=True, timeout=120, check=True,
    )
    with pytest.raises(beats.NoBeatError):
        beats.detect(track)


def test_the_bundled_library_is_analysable():
    """Every shipped track should either give a grid or say it has none.

    Not asserting specific tempos: the true bpm of these tracks is not
    something this repo knows, so a hard number would be a made-up fact.
    """
    tracks = sorted(Path("assets/music").glob("*.mp3"))
    if not tracks:
        pytest.skip("music library not seeded")

    for track in tracks:
        try:
            got = beats.detect(track)
        except beats.NoBeatError:
            continue  # a valid answer for ambient beds
        assert beats.MIN_BPM <= got["bpm"] <= beats.MAX_BPM, (track.name, got)
        assert 0 <= got["phase"] < got["period"], (track.name, got)


# ---- snapping ---------------------------------------------------------------

def test_cuts_land_on_the_grid():
    period, phase = 0.5, 0.0
    wanted = [10.3, 9.8, 12.1]

    snapped = beats.snap_durations(wanted, period, phase)
    elapsed = 0.0
    for length in snapped:
        elapsed += length
        # Every cut point is a whole number of beats from the phase.
        beats_in = (elapsed - phase) / period
        assert abs(beats_in - round(beats_in)) < 1e-6, elapsed


def test_phase_is_absorbed_by_the_first_clip_only():
    """Music loops from its own start, so the grid is offset by the phase."""
    period, phase = 0.5, 0.2
    snapped = beats.snap_durations([10.0, 10.0, 10.0], period, phase)

    elapsed = 0.0
    for length in snapped:
        elapsed += length
        offset = (elapsed - phase) / period
        assert abs(offset - round(offset)) < 1e-6, elapsed


def test_no_clip_moves_by_more_than_a_beat():
    period = 0.5
    wanted = [7.4, 11.9, 6.05]
    snapped = beats.snap_durations(wanted, period)

    for original, new in zip(wanted, snapped):
        assert abs(new - original) <= period, (original, new)


def test_a_clip_is_never_snapped_below_the_minimum():
    """Rounding UP is right here: a 4-second clip to hit a beat trades the
    wrong thing."""
    snapped = beats.snap_durations([5.05], period=0.5, phase=0.0, min_seconds=5.0)
    assert snapped[0] >= 5.0


def test_no_period_means_no_change():
    wanted = [10.0, 8.5]
    assert beats.snap_durations(wanted, period=0.0) == wanted
