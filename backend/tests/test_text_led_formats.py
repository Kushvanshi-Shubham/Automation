"""Formats that do not speak.

Owner: "narration is not good for shayari... it is not necessary that there
must be every type of narrations also."

He is right, and the research agrees: the dominant shayari reel sets the
couplet as typography over a still and lets music carry it - every tutorial
is "insert your text, pick a font, pick a track". A TTS sher is the worst of
both, neither a human voice nor clean type. Whether a format speaks is part
of its grammar, alongside how it cuts and what it looks like.
"""
import pytest

from app.pipeline import captions, runner
from app.services.formats import FORMATS, editing_for


# ---- which formats speak ----------------------------------------------------

def test_shayari_does_not_speak():
    assert FORMATS["shayari"]["output_type"] == "visual"


def test_a_silent_format_offers_no_voice_control():
    """A voice picker on a format with no voice is a control with nothing
    behind it - the same dead-control bug three other settings have had."""
    for key, fmt in FORMATS.items():
        if fmt.get("output_type") in ("visual", "image", "fake_text"):
            assert "voice" not in (fmt.get("controls") or []), f"{key} offers a dead voice picker"


def test_the_narrated_formats_still_narrate():
    """Reddit and viral stories ARE someone reading aloud; news is a read.
    Silencing those would destroy them."""
    for key in ("reddit_story", "viral_story", "breaking_news", "gaming_update"):
        assert FORMATS[key]["output_type"] == "narrated", f"{key} lost its narration"


# ---- the sher must appear whole ---------------------------------------------

SHER = "पहली मिसरा यहाँ है\nदूसरी मिसरा यहाँ है"


def test_a_held_couplet_is_one_cue_not_three_word_chunks():
    cues = captions.held_cue(SHER, 7.0)
    assert len(cues) == 1
    assert cues[0]["end"] == 7.0, "the sher must stay for the whole shot"


def test_both_misras_survive_as_two_lines():
    r"""ASS needs \N for a line break, and _escape strips backslashes - so a
    break written into the text was being eaten before it reached libass."""
    cue = captions.held_cue(SHER, 7.0)[0]
    rendered = captions._escape(cue["text"], uppercase=False)
    assert r"\N" in rendered, "the couplet collapsed onto one line"
    assert rendered.count(r"\N") == 1


def test_an_ordinary_caption_is_untouched_by_that():
    """Every other format's cues have no newlines and must render identically."""
    assert captions._escape("three word cue", uppercase=False) == "three word cue"
    assert r"\N" not in captions._escape("three word cue", uppercase=False)


def test_a_blank_segment_produces_no_cue():
    assert captions.held_cue("   ", 5.0) == []
    assert captions.held_cue("\n\n", 5.0) == []


def test_hold_is_off_unless_the_format_asks():
    assert editing_for(FORMATS["reddit_story"])["caption_hold"] is False
    assert editing_for(FORMATS["shayari"])["caption_hold"] is True


def test_the_hold_flag_reaches_the_caption_builder(monkeypatch, tmp_path):
    """The wire, driven for real - four settings have now been computed
    correctly and then never passed."""
    seen = {}
    monkeypatch.setattr(runner.captions, "build_segment_captions",
                        lambda **k: (seen.update(k), tmp_path / "c.ass")[1])
    monkeypatch.setattr(runner.assembler, "render_segment_silent", lambda *a, **k: None)
    runner._assemble_segment(
        index=0, seg={"text": SHER},
        seg_audio={"duration": 7.0, "words": [], "audio_path": ""},
        clip=tmp_path / "v.mp4", out_path=tmp_path / "o.mp4", workdir=tmp_path,
        data={"editing": editing_for(FORMATS["shayari"])},
        aspect={"w": 1080, "h": 1920}, watermark=False, silent=True,
    )
    assert seen.get("hold") is True


def test_words_given_to_a_held_cue_are_ignored():
    """A held segment must not fall back to word-chunking just because word
    timings happen to exist (they will, if someone opts into narration)."""
    words = [{"word": "x", "start": 0.0, "end": 0.5}] * 6
    path = captions.build_segment_captions(
        words=words, text=SHER, duration=7.0,
        out_path=__import__("pathlib").Path(__import__("tempfile").mkdtemp()) / "a.ass",
        hold=True,
    )
    body = path.read_text(encoding="utf-8")
    assert body.count("Dialogue:") == 1, "held segment was chunked anyway"
