"""The "Narration pace" dropdown must be the only thing setting voice speed.

Owner pointed at it in the studio: "here is the main issue the narration pace."
He was right twice over. It was showing "Very slow - poetry, one line at a
time", which asks edge-tts for -52% and gets clamped to its -45% floor. And
the fix shipped the night before had made the control DEAD: a format's
speech_wps overrode whatever the creator picked, so the dropdown moved and
nothing happened.
"""
import ast
import inspect

from app.pipeline import proof, runner, tts
from app.services.formats import FORMATS, NARRATION_PACES, editing_for, render_defaults


# ---- the control has to work ------------------------------------------------

def test_the_creators_choice_is_what_the_voice_uses():
    """A format may SEED the dropdown; it may never override it."""
    chosen = runner._voice_rhythm({"words_per_second": 2.8,
                                   "editing": {"speech_wps": 1.2}})
    assert chosen["words_per_second"] == 2.8, "the dropdown is dead again"


def test_a_format_seeds_the_dropdown_with_its_speaking_rate():
    """Shayari WRITES at 1.2 w/s (short couplets) but is SPOKEN at 2.2, with
    silence filling the rest. The dropdown must show the speaking rate."""
    assert render_defaults(FORMATS["shayari"])["words_per_second"] == 2.2
    assert FORMATS["shayari"]["words_per_second"] == 1.2, "the writing budget is unchanged"


def test_formats_without_a_separate_speaking_rate_are_untouched():
    for key in ("reddit_story", "breaking_news", "viral_story"):
        assert render_defaults(FORMATS[key])["words_per_second"] == FORMATS[key]["words_per_second"]


def test_every_seeded_default_is_offered_in_the_dropdown():
    """A seeded value missing from NARRATION_PACES cannot be displayed, so the
    select falls back and the creator sees a pace that is not the real one."""
    for key, fmt in FORMATS.items():
        seeded = render_defaults(fmt).get("words_per_second")
        if seeded is not None:
            assert seeded in NARRATION_PACES, f"{key} seeds {seeded}, not a preset"


def test_nothing_points_at_the_dragged_floor_by_default():
    """1.2 clamps to edge-tts's -45% limit. It stays available for anyone who
    wants it, but no format may choose it for a creator."""
    assert tts.rate_for(1.2) == "-45%"
    for key, fmt in FORMATS.items():
        assert render_defaults(fmt).get("words_per_second", 2.5) > 1.2, f"{key} defaults to the floor"


def test_the_labels_describe_delivery_not_mood():
    """They used to conflate "unhurried" with "slow voice", which is why
    poetry pointed at the slowest setting. Unhurried is silence now."""
    assert "poetry, one line at a time" not in NARRATION_PACES[1.2]
    assert "pauses between lines" in NARRATION_PACES[2.2]


# ---- the proof must sound like the render -----------------------------------

def test_the_proof_hears_the_same_rhythm_as_the_render():
    """The proof exists to be checked before paying. It called synth_segment
    directly with no pauses, so the one thing worth checking - the gap between
    the misras - was the one thing it could not play."""
    src = inspect.getsource(proof)
    assert "tts.synth_script(" in src, "proof still synthesizes its own way"
    assert "runner._voice_rhythm(data)" in src, "proof ignores the format's rhythm"


def test_the_proof_does_not_build_its_own_rate():
    src = inspect.getsource(proof)
    assert "tts.rate_for(" not in src, "proof is computing delivery speed itself again"


def test_both_lanes_take_their_rhythm_from_one_place():
    """runner and proof must call the same helper, or they drift - which has
    now happened three times in this file's history."""
    for module in (runner, proof):
        tree = ast.parse(inspect.getsource(module))
        names = {n.func.attr if isinstance(n.func, ast.Attribute) else getattr(n.func, "id", "")
                 for n in ast.walk(tree) if isinstance(n, ast.Call)}
        assert "_voice_rhythm" in names, f"{module.__name__} does not use the shared rhythm"


# ---- and the silence still has to be there ----------------------------------

def test_shayari_still_gets_its_pauses_after_all_this():
    r = runner._voice_rhythm(render_defaults(FORMATS["shayari"]))
    assert r["line_pause"] > 0 and r["pause_after"] > 0
    assert r["words_per_second"] == 2.2


def test_a_creator_slowing_the_voice_keeps_the_pauses():
    """Pace and silence are independent knobs. Someone who wants a dragged
    delivery AND the breathing should get both."""
    r = runner._voice_rhythm({"words_per_second": 1.2,
                              "editing": editing_for(FORMATS["shayari"])})
    assert r["words_per_second"] == 1.2
    assert r["line_pause"] > 0, "slowing the voice silently removed the rhythm"
