"""Loudness-based highlight detection.

These build real media with ffmpeg rather than mocking the decode, because
the thing worth testing is whether a detected window actually lands on the
burst — and a mocked envelope would only test the arithmetic I already
wrote.
"""
import shutil
import subprocess

import pytest

from app.services import highlights

pytestmark = pytest.mark.skipif(
    shutil.which("ffmpeg") is None, reason="ffmpeg not installed"
)


def _make_video(path, spec: str, seconds: int):
    """A black video whose audio follows `spec` (an ffmpeg volume expression)."""
    subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
         "-f", "lavfi", "-i", f"color=c=black:s=64x64:d={seconds}",
         "-f", "lavfi", "-i", f"sine=frequency=440:duration={seconds}",
         "-af", spec, "-c:v", "libx264", "-preset", "ultrafast",
         "-c:a", "aac", "-shortest", str(path)],
        capture_output=True, timeout=120, check=True,
    )


def test_finds_the_burst_and_not_the_quiet_part(tmp_path):
    """One loud burst at 30s in an otherwise quiet 60s recording."""
    video = tmp_path / "burst.mp4"
    # Quiet everywhere, loud between 30s and 34s.
    _make_video(video, "volume='if(between(t,30,34),1.0,0.05)':eval=frame", 60)

    picks = highlights.find_highlights(video, duration=60.0)
    assert picks, "a 20x volume jump should be detectable"

    top = picks[0]
    # The peak must be inside the burst, not merely nearby.
    assert 30 <= top["peak_at"] <= 34, f"peak landed at {top['peak_at']}s"
    # And the window must actually contain it.
    assert top["start"] <= top["peak_at"] <= top["end"]
    # Lead-in, not lead-out: a viewer needs the setup before the payoff.
    assert top["start"] < top["peak_at"], "window should open before the peak"
    assert top["score"] > highlights.MIN_PEAK_RATIO


def test_even_audio_suggests_nothing(tmp_path):
    """A constant tone has no highlight. Returning one would be a lie."""
    video = tmp_path / "flat.mp4"
    _make_video(video, "volume=0.5", 40)

    assert highlights.find_highlights(video, duration=40.0) == []


def test_windows_do_not_describe_the_same_moment_twice(tmp_path):
    """Two bursts far apart give two windows; one burst gives one."""
    video = tmp_path / "two.mp4"
    _make_video(
        video,
        "volume='if(between(t,10,12)+between(t,50,52),1.0,0.05)':eval=frame",
        70,
    )

    picks = highlights.find_highlights(video, duration=70.0)
    assert len(picks) >= 2
    peaks = sorted(p["peak_at"] for p in picks[:2])
    assert peaks[1] - peaks[0] >= highlights.MIN_SEPARATION_SECONDS


def test_silent_video_raises_no_audio(tmp_path):
    """A silent screen recording is a normal upload, not a failure."""
    video = tmp_path / "silent.mp4"
    subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
         "-f", "lavfi", "-i", "color=c=black:s=64x64:d=10",
         "-c:v", "libx264", "-preset", "ultrafast", str(video)],
        capture_output=True, timeout=120, check=True,
    )
    with pytest.raises(highlights.NoAudioError):
        highlights.find_highlights(video, duration=10.0)


def test_windows_never_run_past_the_end(tmp_path):
    """A burst in the last seconds must not suggest a range beyond the file."""
    video = tmp_path / "late.mp4"
    _make_video(video, "volume='if(gt(t,27),1.0,0.05)':eval=frame", 30)

    for pick in highlights.find_highlights(video, duration=30.0):
        assert pick["end"] <= 30.0 + 0.01, pick
        assert pick["end"] - pick["start"] >= 5.0, "window shrank below the clip minimum"


def test_duration_shorter_than_audio_is_respected(tmp_path):
    """Container duration wins when it is the stricter of the two."""
    video = tmp_path / "clamp.mp4"
    _make_video(video, "volume='if(between(t,20,24),1.0,0.05)':eval=frame", 40)

    for pick in highlights.find_highlights(video, duration=25.0):
        assert pick["end"] <= 25.0 + 0.01, pick


# ---- merge: how the two signals combine -------------------------------------

def test_speech_leads_and_sound_tops_up():
    speech = [{"start": 5.0, "end": 15.0, "title": "The point", "reason": "explains the setup"}]
    sound = [{"start": 40.0, "end": 50.0, "peak_at": 44.0, "score": 2.4}]

    out = highlights.merge(speech, sound)
    assert [h["source"] for h in out] == ["speech", "sound"]
    assert out[0]["title"] == "The point"
    assert out[1]["title"] == "Loud moment"
    assert "2.4x louder" in out[1]["reason"]


def test_a_moment_is_never_suggested_twice():
    """A loud peak inside a speech highlight is the same moment."""
    speech = [{"start": 5.0, "end": 15.0, "title": "A", "reason": "r"}]
    sound = [{"start": 8.0, "end": 18.0, "peak_at": 12.0, "score": 3.0}]

    assert highlights.merge(speech, sound) == [
        {"start": 5.0, "end": 15.0, "title": "A", "reason": "r", "source": "speech"}
    ]


def test_gameplay_case_sound_only():
    """No transcript to reason about — the whole list comes from loudness.
    This is the case that previously showed 'no strong clip moments found'."""
    sound = [
        {"start": 10.0, "end": 20.0, "peak_at": 14.0, "score": 3.1},
        {"start": 60.0, "end": 70.0, "peak_at": 64.0, "score": 2.0},
    ]
    out = highlights.merge([], sound)
    assert len(out) == 2
    assert all(h["source"] == "sound" for h in out)
    assert all(h["title"] and h["reason"] for h in out), "the clips list renders both"


def test_merge_respects_the_cap():
    speech = [{"start": float(i * 20), "end": float(i * 20 + 10), "title": "t", "reason": "r"}
              for i in range(10)]
    assert len(highlights.merge(speech, [])) == highlights.MAX_SUGGESTIONS
