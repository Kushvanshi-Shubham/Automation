"""Where the pause in shayari actually belongs.

Owner's verdict on the first slow render: "too slow, the gap is weird - in
shayari like if u download audio of shayari u will understand it."

Both halves were the same mistake. We dragged the voice to edge-tts's -45%
floor (which sounds like a slowed recording, not a recitation) and put the
gap in the PICTURE as a fade, where it reads as a glitch because the voice
never actually stops. Real shayari is spoken near normal speed and the
poetry lives in the silence between the misras and between the shers.
"""
import subprocess

import pytest

from app.pipeline import tts
from app.pipeline.assembler import probe_duration
from app.services.formats import FORMATS, editing_for

SHER = "पहली मिसरा यहाँ है\nदूसरी मिसरा यहाँ है"


# ---- the recipe ------------------------------------------------------------

def test_the_voice_is_no_longer_dragged_to_the_floor():
    """1.2 w/s asked edge-tts for -52% and got clamped to its -45% limit —
    the maximum slowdown the engine allows, on every single shayari."""
    e = editing_for(FORMATS["shayari"])
    assert tts.rate_for(FORMATS["shayari"]["words_per_second"]) == "-45%", "the old floor"
    assert e["speech_wps"] == 2.2
    assert tts.rate_for(e["speech_wps"]) == "-12%", "measured, not slowed"


def test_the_silence_is_in_the_audio_not_the_picture():
    e = editing_for(FORMATS["shayari"])
    assert e["line_pause"] > 0 and e["pause_after"] > e["line_pause"], (
        "the gap between shers should be longer than the one inside a sher"
    )
    assert e["transition"] == "cut" and e["fade"] == 0.0, (
        "the rejected dip-to-black must not come back"
    )


def test_no_format_ships_the_rejected_fade():
    """The soft machinery stays and stays tested, but nothing uses it until
    a human has watched one and liked it."""
    for key, fmt in FORMATS.items():
        assert editing_for(fmt)["transition"] == "cut", f"{key} still dips to black"


def test_the_script_budget_and_the_speaking_rate_are_separate():
    """Keeping these apart is the whole trick: short couplets (1.2 w/s of
    words) delivered at a natural pace, with silence filling the rest."""
    fmt = FORMATS["shayari"]
    assert fmt["words_per_second"] == 1.2
    assert editing_for(fmt)["speech_wps"] != fmt["words_per_second"]


def test_formats_that_name_no_rhythm_are_untouched():
    e = editing_for(FORMATS["reddit_story"])
    assert e["line_pause"] == 0.0 and e["pause_after"] == 0.0 and e["speech_wps"] is None


# ---- splitting -------------------------------------------------------------

def test_a_sher_is_split_into_its_two_misras():
    assert tts.utterances(SHER, 0.55) == ["पहली मिसरा यहाँ है", "दूसरी मिसरा यहाँ है"]


def test_a_format_with_no_line_pause_never_splits():
    assert tts.utterances(SHER, 0.0) == [SHER]


def test_a_single_line_segment_is_left_whole():
    assert tts.utterances("sirf ek line", 0.55) == ["sirf ek line"]


def test_blank_lines_do_not_become_empty_utterances():
    """An empty string reaches TTS as "" and fails the render after the
    credit is taken — the same trap blank scenes already have a guard for."""
    assert tts.utterances("line one\n\n\nline two", 0.55) == ["line one", "line two"]


def test_the_model_is_told_to_break_the_couplet():
    """utterances() can only place the pause if it can see the line break,
    so the prompt has to ask for one. Silent failure otherwise: the whole
    sher becomes one utterance and the rhythm quietly disappears."""
    from app.services.script_gen import STYLE_PROMPTS, _POETIC_RULES

    poetry = STYLE_PROMPTS["poetry"]
    assert "EXACTLY TWO lines" in poetry
    assert "newline between them" in poetry
    # It lives in the poetry style, NOT the rules poetry and lyrical share:
    # a lyrical segment genuinely is one line, and demanding two there would
    # quietly wreck the music-video format.
    assert "EXACTLY TWO lines" not in _POETIC_RULES
    assert "EXACTLY TWO lines" not in STYLE_PROMPTS["lyrical"]


# ---- and it has to survive ffmpeg -----------------------------------------

def _have_ffmpeg() -> bool:
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=10)
        return True
    except Exception:
        return False


requires_ffmpeg = pytest.mark.skipif(not _have_ffmpeg(), reason="ffmpeg not installed")


@requires_ffmpeg
def test_padding_adds_exactly_the_silence_asked_for(tmp_path):
    src = tmp_path / "a.mp3"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi",
                    "-i", "sine=frequency=440:duration=2", str(src)],
                   check=True, capture_output=True, timeout=60)
    out = tmp_path / "padded.mp3"
    tts._pad_audio(src, 0.9, out)
    assert abs(probe_duration(out) - 2.9) < 0.12


@requires_ffmpeg
def test_joining_pieces_keeps_the_total_length(tmp_path):
    """If concat drops or overlaps a piece, every caption after it is wrong."""
    parts = []
    for i in range(3):
        p = tmp_path / f"p{i}.mp3"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi",
                        "-i", f"sine=frequency={300 + i * 100}:duration=1", str(p)],
                       check=True, capture_output=True, timeout=60)
        parts.append(p)
    out = tmp_path / "joined.mp3"
    tts._concat_audio(parts, out)
    assert abs(probe_duration(out) - 3.0) < 0.2


# ---- the thing most likely to break silently -------------------------------

@requires_ffmpeg
def test_word_timings_are_shifted_by_every_pause_before_them(tmp_path, monkeypatch):
    """Each piece is synthesized alone, so its word events start at 0. If they
    are not shifted by everything already on the timeline, the second misra's
    captions appear while the first is still being spoken — and the drift
    grows with every pause, so the last sher is the worst.
    """
    async def fake_speak(text, path, voice, rate=None):
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi",
                        "-i", "sine=frequency=440:duration=1", str(path)],
                       check=True, capture_output=True, timeout=60)
        # One word event per piece, spanning its whole second.
        return 1.0, [{"word": text.split()[0], "start": 0.0, "end": 1.0}]

    monkeypatch.setattr(tts, "synth_segment", fake_speak)

    import asyncio

    from app.services import rhythm

    segments = [{"text": "first" + chr(10) + "second"}]
    # Ask the same planner the synthesizer uses, rather than hardcoding a
    # number the planner is free to vary.
    expected = rhythm.plan(segments, line_pause=0.5, pause_after=0.8)[0]

    out = asyncio.run(tts.synth_script(
        segments, tmp_path, line_pause=0.5, pause_after=0.8,
    ))
    seg = out[0]
    # 1s speech + the misra gap + 1s speech + the trailing gap
    assert abs(seg["duration"] - (2.0 + expected["line"] + expected["after"])) < 0.25,         seg["duration"]

    starts = [w["start"] for w in seg["words"]]
    assert len(starts) == 2
    assert abs(starts[0] - 0.0) < 0.05, "first misra should start at zero"
    assert abs(starts[1] - (1.0 + expected["line"])) < 0.25, (
        f"second misra caption at {starts[1]:.2f}s - should be after 1s of "
        f"speech plus the {expected['line']:.2f}s pause"
    )


@requires_ffmpeg
def test_a_format_with_no_pauses_takes_the_original_single_shot_path(tmp_path, monkeypatch):
    """No pause means one synthesis call and untouched timings — every other
    format must be bit-for-bit what it was."""
    calls = []

    async def fake_speak(text, path, voice, rate=None):
        calls.append(text)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi",
                        "-i", "sine=frequency=440:duration=1", str(path)],
                       check=True, capture_output=True, timeout=60)
        return 1.0, [{"word": "w", "start": 0.0, "end": 1.0}]

    monkeypatch.setattr(tts, "synth_segment", fake_speak)

    import asyncio
    out = asyncio.run(tts.synth_script([{"text": "first\nsecond"}], tmp_path))
    assert calls == ["first\nsecond"], "split the segment when it was told not to"
    assert out[0]["words"] == [{"word": "w", "start": 0.0, "end": 1.0}]


def test_the_rhythm_reaches_the_voice_lane():
    """The settings were computed correctly and then not passed, twice in one
    night, in two different files. This drives the real wire."""
    from app.pipeline.runner import _voice_rhythm
    from app.services.formats import render_defaults

    r = _voice_rhythm(render_defaults(FORMATS["shayari"]))
    # Bases, not final values — services/rhythm.py varies each one from here.
    assert r["line_pause"] > 0 and r["pause_after"] > r["line_pause"]
    assert r["words_per_second"] == 2.2, "spoke at the script budget instead of the delivery rate"


def test_a_format_with_no_delivery_rate_still_uses_its_script_budget():
    """The old behaviour for every other format: words_per_second doubles as
    the speaking rate. Removing that would silently un-pace eight formats."""
    from app.pipeline.runner import _voice_rhythm

    assert _voice_rhythm({"words_per_second": 2.8})["words_per_second"] == 2.8
    assert _voice_rhythm({})["words_per_second"] is None, "None means leave the voice alone"


def test_the_render_actually_calls_the_voice_rhythm_helper():
    """The helper above is tested, but nothing proves run() USES it — and
    deleting one line there silently reverts every format to unpaced,
    unrated narration with no error anywhere.

    run() cannot be driven from a unit test (DB, network, ffmpeg, a live
    Celery job), so this asserts the call site structurally: find the real
    tts.synth_script(...) call in the AST and check the rhythm is spread
    into it. Not a string match — reformat it freely and this still holds.
    """
    import ast
    import inspect

    from app.pipeline import runner

    tree = ast.parse(inspect.getsource(runner))
    calls = [
        n for n in ast.walk(tree)
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Attribute) and n.func.attr == "synth_script"
    ]
    assert calls, "no synth_script call found in runner - did it move?"

    for call in calls:
        spread = [
            kw for kw in call.keywords
            if kw.arg is None and isinstance(kw.value, ast.Call)
            and getattr(kw.value.func, "id", None) == "_voice_rhythm"
        ]
        assert spread, (
            "synth_script is called without **_voice_rhythm(data) - the "
            "format's delivery rate and pauses reach nothing"
        )
