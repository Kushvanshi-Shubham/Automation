"""Per-format editing grammar.

A shayari and a news update are not the same video in different colours.
This is the layer that makes them cut differently — and the regression risk
is that it quietly changes every OTHER format too, so the defaults are
pinned here against the exact values that shipped before it existed.
"""
import subprocess
from pathlib import Path

import pytest

from app.pipeline import assembler, captions, runner
from app.pipeline.assembler import MOTION_CURVES
from app.services.formats import FORMATS, MOTIONS, editing_for, render_defaults


# ---- the defaults must be the old behaviour, exactly ------------------------

def test_a_format_that_says_nothing_renders_as_before():
    """Every format except the four given a recipe must be untouched."""
    assert editing_for(FORMATS["reddit_story"]) == {
        "motion": "kenburns", "transition": "cut", "fade": 0.0, "words_per_cue": 3,
    }


def test_the_default_ken_burns_numbers_are_the_original_ones():
    """These two numbers were in the shipped zoompan expression. If they move,
    every previously-rendered format starts moving at a different speed."""
    assert MOTION_CURVES["kenburns"] == (0.0009, 1.18)


def test_the_motions_are_actually_different_from_each_other():
    """Names are free; the numbers are the feature. Ordering rather than exact
    values, so these stay true when the speeds get retuned by eye."""
    drift, kb, punch, still = (MOTION_CURVES[k] for k in ("drift", "kenburns", "punch", "still"))
    assert drift[0] < kb[0] < punch[0], "drift/punch must differ in SPEED from the default"
    assert drift[1] < kb[1] < punch[1], "and in how far the frame travels"
    assert still == (0.0, 1.0), "still must not move at all"


def test_old_videos_have_no_recipe_and_get_the_defaults():
    """script_data from before this feature has no 'editing' key at all."""
    assert runner._editing(None) == runner._editing({}) == editing_for(None)
    assert runner._editing({"caption_style": "classic"})["motion"] == "kenburns"


# ---- the recipe has to actually reach the renderer -------------------------

def test_the_recipe_is_written_onto_the_video_at_generation_time():
    """render_defaults is the only channel from a format to script_data. If
    editing is not in here, the whole layer is dead code."""
    out = render_defaults(FORMATS["shayari"])
    assert out["editing"]["motion"] == "drift"
    assert out["editing"]["words_per_cue"] == 7


def test_shayari_holds_the_line_and_breathes():
    e = editing_for(FORMATS["shayari"])
    assert e["motion"] == "drift", "a couplet should not be chased by the camera"
    assert e["transition"] == "soft" and e["fade"] > 0
    assert e["words_per_cue"] >= 6, "3-word chunks destroy a couplet's shape"


def test_news_and_gaming_push_in():
    for key in ("breaking_news", "gaming_update"):
        assert editing_for(FORMATS[key])["motion"] == "punch"


def test_the_motion_list_and_the_motion_curves_cannot_drift_apart():
    """Two dicts, two files, same keys: a motion offered in the UI with no
    curve behind it falls back to kenburns and nobody sees an error."""
    assert set(MOTIONS) == set(MOTION_CURVES)


def test_every_format_names_a_motion_that_exists():
    """A typo here is silent — .get() falls back to kenburns."""
    for key, fmt in FORMATS.items():
        assert editing_for(fmt)["motion"] in MOTIONS, f"{key} names an unknown motion"
        assert editing_for(fmt)["transition"] in ("cut", "soft"), key


# ---- captions -------------------------------------------------------------

def _words(n):
    return [{"word": f"w{i}", "start": i * 0.5, "end": i * 0.5 + 0.4} for i in range(n)]


def test_a_format_can_hold_a_whole_line():
    three = captions.group_words(_words(12), max_words=3)
    seven = captions.group_words(_words(12), max_words=7)
    assert len(seven) < len(three), "more words per cue must mean fewer cues"


def test_the_no_word_timings_path_honours_it_too():
    """Fallback cues used a hardcoded 3 — a shayari with no word timings
    would have been chopped up regardless of its recipe."""
    long = captions.fallback_cues("a b c d e f g h i j k l", 12.0, max_words=7)
    short = captions.fallback_cues("a b c d e f g h i j k l", 12.0, max_words=3)
    assert len(long) < len(short)


def test_captions_default_to_three_words():
    assert len(captions.fallback_cues("a b c d e f", 6.0)) == 2


# ---- fades ----------------------------------------------------------------

def test_no_fade_produces_no_filter():
    assert assembler._fade_filter(7.0, 0.0) == ""


def test_a_shot_too_short_to_fade_is_left_alone():
    """0.3s in and 0.3s out of a 0.4s shot is a shot that is never visible."""
    assert assembler._fade_filter(0.4, 0.3) == ""


def test_the_fade_out_lands_at_the_end_of_the_shot():
    f = assembler._fade_filter(7.0, 0.3)
    assert "st=6.70:d=0.30" in f
    assert "t=in:st=0" in f


# ---- and it has to survive ffmpeg ------------------------------------------

def _have_ffmpeg() -> bool:
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=10)
        return True
    except Exception:
        return False


requires_ffmpeg = pytest.mark.skipif(not _have_ffmpeg(), reason="ffmpeg not installed")


@requires_ffmpeg
@pytest.mark.parametrize("motion", sorted(MOTION_CURVES))
def test_every_motion_builds_a_filtergraph_ffmpeg_accepts(tmp_path, motion):
    """A bad zoompan expression is accepted by every unit test above and
    fails only in production, mid-render, after the money is spent."""
    still = tmp_path / "in.png"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi",
                    "-i", "testsrc=size=540x960:duration=1", "-frames:v", "1", str(still)],
                   check=True, capture_output=True, timeout=60)
    out = tmp_path / f"{motion}.mp4"
    assembler.image_to_clip(still, 2.0, out, width=540, height=960, motion=motion)
    assert out.exists() and out.stat().st_size > 1000
    assert abs(assembler.probe_duration(out) - 2.0) < 0.35, "motion changed the shot length"


@requires_ffmpeg
def test_a_soft_shot_is_the_same_length_as_a_hard_cut(tmp_path):
    """The reason this is a per-shot fade and not an xfade chain: an xfade
    shortens the video while the narration keeps its length, and nothing
    downstream would re-sync them."""
    src = tmp_path / "src.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi",
                    "-i", "testsrc=size=540x960:duration=4", "-pix_fmt", "yuv420p", str(src)],
                   check=True, capture_output=True, timeout=60)
    hard, soft = tmp_path / "hard.mp4", tmp_path / "soft.mp4"
    assembler.render_segment_silent(src, 3.0, hard, width=540, height=960, fade=0.0)
    assembler.render_segment_silent(src, 3.0, soft, width=540, height=960, fade=0.3)
    assert abs(assembler.probe_duration(hard) - assembler.probe_duration(soft)) < 0.1


# ---- the wires -------------------------------------------------------------
#
# Everything above proves the recipe EXISTS and that the functions ACCEPT it.
# That is exactly what was true of the bring-your-own-script bug: settings
# computed correctly, function ready to receive them, nothing passing them.
# These drive the real call sites.

import asyncio  # noqa: E402


class _Video:
    def __init__(self, **data):
        self.id = "vid"
        self.script_data = data
        self.visual_engine = "ai_image"
        self.user_id = "u"


SHAYARI = {"motion": "drift", "transition": "soft", "fade": 0.3, "words_per_cue": 7}


def test_the_format_motion_reaches_the_ken_burns_call(monkeypatch):
    """_visual_for_scene builds the moving shot. If the recipe stops here,
    a shayari drifts at news speed and nothing anywhere reports it."""
    seen = {}
    monkeypatch.setattr("app.services.image_gen.generate_image",
                        lambda *a, **k: asyncio.sleep(0))
    monkeypatch.setattr(runner.assembler, "image_to_clip",
                        lambda *a, **k: seen.update(k))

    asyncio.run(runner._visual_for_scene(
        None, 0, {"text": "raat", "visual_prompt": "rain on glass"},
        Path("clip.mp4"), 5.0,
        video=_Video(editing=SHAYARI), aspect={"w": 1080, "h": 1920, "orientation": "portrait"},
        asset_paths={}, ai_visuals=True, gen_keys={}, used_ids=set(),
    ))
    assert seen.get("motion") == "drift", "the format's motion never reached the renderer"


def test_a_format_with_no_recipe_still_gets_ken_burns(monkeypatch):
    seen = {}
    monkeypatch.setattr("app.services.image_gen.generate_image",
                        lambda *a, **k: asyncio.sleep(0))
    monkeypatch.setattr(runner.assembler, "image_to_clip", lambda *a, **k: seen.update(k))
    asyncio.run(runner._visual_for_scene(
        None, 0, {"text": "x", "visual_prompt": "y"}, Path("clip.mp4"), 5.0,
        video=_Video(), aspect={"w": 1080, "h": 1920, "orientation": "portrait"},
        asset_paths={}, ai_visuals=True, gen_keys={}, used_ids=set(),
    ))
    assert seen.get("motion") == "kenburns"


def _assemble(data, silent=False, monkeypatch=None, tmp_path=None):
    caps, rend = {}, {}
    monkeypatch.setattr(runner.captions, "build_segment_captions",
                        lambda **k: (caps.update(k), tmp_path / "c.ass")[1])
    monkeypatch.setattr(runner.assembler, "render_segment", lambda *a, **k: rend.update(k))
    monkeypatch.setattr(runner.assembler, "render_segment_silent", lambda *a, **k: rend.update(k))
    runner._assemble_segment(
        index=0, seg={"text": "ek sher"},
        seg_audio={"duration": 6.0, "words": [], "audio_path": str(tmp_path / "a.mp3")},
        clip=tmp_path / "v.mp4", out_path=tmp_path / "o.mp4", workdir=tmp_path,
        data=data, aspect={"w": 1080, "h": 1920}, watermark=False, silent=silent,
    )
    return caps, rend


def test_the_line_length_reaches_the_caption_builder(monkeypatch, tmp_path):
    caps, _ = _assemble({"editing": SHAYARI}, monkeypatch=monkeypatch, tmp_path=tmp_path)
    assert caps.get("words_per_cue") == 7, "shayari captions still chopped to 3 words"


def test_the_fade_reaches_the_shot_renderer(monkeypatch, tmp_path):
    _, rend = _assemble({"editing": SHAYARI}, monkeypatch=monkeypatch, tmp_path=tmp_path)
    assert rend.get("fade") == 0.3


def test_a_cut_format_renders_with_no_fade_at_all(monkeypatch, tmp_path):
    """Not "a fade of zero applied" — the filter must not be there, so every
    non-soft format goes through the identical filtergraph it always did."""
    _, rend = _assemble({}, monkeypatch=monkeypatch, tmp_path=tmp_path)
    assert rend.get("fade") == 0.0
    assert assembler._fade_filter(6.0, rend["fade"]) == ""


def test_a_soft_recipe_with_transition_cut_does_not_fade(monkeypatch, tmp_path):
    """transition is the switch; fade is only its size."""
    _, rend = _assemble({"editing": {"transition": "cut", "fade": 0.9}},
                        monkeypatch=monkeypatch, tmp_path=tmp_path)
    assert rend.get("fade") == 0.0


def test_the_silent_lane_gets_the_same_treatment(monkeypatch, tmp_path):
    """music_visual renders through render_segment_silent — it was the lane
    most likely to be forgotten, since it has no narration."""
    caps, rend = _assemble({"editing": SHAYARI}, silent=True,
                           monkeypatch=monkeypatch, tmp_path=tmp_path)
    assert rend.get("fade") == 0.3 and caps.get("words_per_cue") == 7
