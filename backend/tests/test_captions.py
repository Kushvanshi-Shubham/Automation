from pathlib import Path

from app.pipeline.captions import build_segment_captions, fallback_cues, group_words

WORDS = [
    {"word": "The", "start": 0.1, "end": 0.27},
    {"word": "ocean", "start": 0.29, "end": 0.70},
    {"word": "covers", "start": 0.71, "end": 1.07},
    {"word": "seventy", "start": 1.09, "end": 1.43},
    {"word": "percent,", "start": 1.44, "end": 1.83},
    {"word": "easily.", "start": 1.9, "end": 2.4},
]


def test_group_words_max_three_and_punctuation_break():
    cues = group_words(WORDS)
    assert [c["text"] for c in cues] == ["The ocean covers", "seventy percent,", "easily."]
    # cues stretched to meet the next one (no flicker gaps)
    assert cues[0]["end"] == cues[1]["start"]
    assert cues[1]["end"] == cues[2]["start"]


def test_fallback_cues_spread_evenly():
    cues = fallback_cues("one two three four five six", 6.0)
    assert len(cues) == 2
    assert cues[0] == {"text": "one two three", "start": 0.0, "end": 3.0}
    assert cues[1]["end"] == 6.0


def test_ass_file_written_uppercase(tmp_path: Path):
    out = build_segment_captions(WORDS, "irrelevant", 2.5, tmp_path / "c.ass")
    content = out.read_text(encoding="utf-8")
    assert "[Events]" in content
    assert "THE OCEAN COVERS" in content
    assert "Dialogue: 0,0:00:00.10," in content


def test_ass_fallback_when_no_words(tmp_path: Path):
    out = build_segment_captions([], "hello brave new world", 4.0, tmp_path / "c.ass")
    content = out.read_text(encoding="utf-8")
    assert "HELLO BRAVE NEW" in content
    assert "WORLD" in content
