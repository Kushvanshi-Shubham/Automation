"""Every silence its own length.

Owner: "every shayari are never same - sometimes long gap sometimes short,
the deep breath, heavy hearts."

Measured rather than argued: 831 pauses across 37 minutes of CC-licensed
live Urdu/Sindhi recitation from archive.org gave p25 0.38s, median 0.53s,
p90 1.26s - a 3.3x spread with a heavy right tail, and a pause longer than
twice the median landing about every third pause.

The failure these guard against is not a crash. It is the model quietly
flattening back to one value, which sounds exactly like what he rejected.
"""
import statistics as st

import pytest

from app.services import rhythm
from app.services.formats import FORMATS, editing_for

SHERS = [
    {"text": "रात भर जागते रहे हम तो,\nसुबह ने भी कुछ नहीं कहा।"},
    {"text": "तेरा ज़िक्र था महफ़िल में\nऔर हम चुप रहे।"},
    {"text": "वो एक चुप्पी थी जो सब कह गई,\nऔर हम सुनते रह गए।"},
    {"text": "अब लौट आओ।"},
]


def _plan(mood="sad", **kw):
    e = editing_for(FORMATS["shayari"])
    return rhythm.plan(SHERS, line_pause=kw.get("line_pause", e["line_pause"]),
                       pause_after=kw.get("pause_after", e["pause_after"]), mood=mood)


def _all_gaps(plan):
    return [g for p in plan for g in (p["line"], p["after"]) if g > 0]


# ---- the point of the whole module -----------------------------------------

def test_no_two_silences_are_the_same_length():
    """The complaint, restated as an assertion."""
    gaps = _all_gaps(_plan())
    assert len(set(gaps)) == len(gaps), f"repeated pause lengths: {gaps}"


def test_the_spread_resembles_real_recitation():
    """Measured p90/p25 was 3.3x. Anything near 1.0 is the flat version."""
    gaps = _all_gaps(_plan())
    assert max(gaps) / min(gaps) > 2.5, "pauses are nearly uniform again"


def test_the_typical_pause_is_near_the_measured_median():
    """0.53s in the recordings. These are structural gaps only, so sitting a
    little above it is right; sitting far above is the 'too slow' complaint."""
    assert 0.4 <= st.median(_all_gaps(_plan())) <= 0.95


def test_nothing_ever_becomes_dead_air():
    for g in _all_gaps(_plan()):
        assert rhythm.MIN_PAUSE <= g <= rhythm.MAX_PAUSE
    assert rhythm.MAX_PAUSE < 2.0, "longer than any pause inside a real recitation"


# ---- what drives the variation ---------------------------------------------

def test_the_longest_silence_is_the_run_up_to_the_closing_sher():
    """The last couplet is the one that has to land, and it lands out of quiet.

    Identical text in every slot, so POSITION is the only thing that can
    differ — otherwise line length and per-line wobble mask the effect and
    the test passes even with the weighting removed.
    """
    same = [{"text": "एक ही शेर।"} for _ in range(5)]
    afters = [p["after"] for p in rhythm.plan(same, line_pause=0.0, pause_after=0.9)[:-1]]
    # Strictly greater, not >=. Identical text means identical wobble, so an
    # equality check here is satisfied by every gap being the same - which is
    # precisely the flat version this module exists to prevent.
    assert afters[-1] > afters[-2], "the closing sher is not given its beat"
    assert afters[0] < afters[1], "the opening should move before it settles"


def test_nothing_follows_the_final_line():
    """Trailing silence at the end of the video is just dead tape."""
    assert _plan()[-1]["after"] == 0.0


def test_a_heavy_mood_is_held_longer_than_a_driving_one():
    """Dard sits in the silence; hausla refuses to wallow."""
    sad = st.mean(_all_gaps(_plan(mood="sad")))
    hausla = st.mean(_all_gaps(_plan(mood="hausla")))
    assert sad > hausla * 1.2, f"mood changed nothing: {sad:.2f} vs {hausla:.2f}"


def test_an_unknown_mood_changes_nothing():
    assert _all_gaps(_plan(mood="klingon")) == _all_gaps(_plan(mood=None))


def test_a_line_that_ends_mid_thought_is_held_less():
    """A comma runs on into the next line; a danda has finished."""
    running = rhythm.plan([{"text": "पहली लाइन,"}, {"text": "दूसरी"}],
                          line_pause=0.0, pause_after=0.9)
    finished = rhythm.plan([{"text": "पहली लाइन।"}, {"text": "दूसरी"}],
                           line_pause=0.0, pause_after=0.9)
    assert running[0]["after"] < finished[0]["after"]


def test_a_longer_line_earns_a_longer_breath():
    short = rhythm.plan([{"text": "एक"}, {"text": "दो"}], line_pause=0.0, pause_after=0.9)
    long = rhythm.plan([{"text": "एक " * 14}, {"text": "दो"}], line_pause=0.0, pause_after=0.9)
    assert long[0]["after"] > short[0]["after"]


# ---- reproducibility --------------------------------------------------------

def test_the_same_script_always_breathes_the_same_way():
    """Variation must not be randomness. If a re-render differs, nobody can
    tell whether a change they made did anything."""
    assert _plan() == _plan()


def test_different_lines_get_different_wobble():
    a = rhythm.plan([{"text": "पहली"}, {"text": "x"}], line_pause=0.0, pause_after=0.9)
    b = rhythm.plan([{"text": "दूसरी"}, {"text": "x"}], line_pause=0.0, pause_after=0.9)
    assert a[0]["after"] != b[0]["after"]


# ---- it must never invent a pause -------------------------------------------

def test_a_format_that_asks_for_no_silence_gets_none():
    """Eight formats have no rhythm at all. Inventing one for a news update
    would change every video in the product."""
    plan = rhythm.plan(SHERS, line_pause=0.0, pause_after=0.0)
    assert all(p["line"] == 0.0 and p["after"] == 0.0 for p in plan)


def test_only_the_asked_for_half_is_filled_in():
    plan = rhythm.plan(SHERS, line_pause=0.0, pause_after=0.9)
    assert all(p["line"] == 0.0 for p in plan)
    assert any(p["after"] > 0 for p in plan)


def test_an_empty_script_does_not_explode():
    assert rhythm.plan([], line_pause=0.5, pause_after=0.9) == []


def test_a_single_sher_has_no_gap_after_it():
    plan = rhythm.plan([{"text": "अकेला शेर"}], line_pause=0.45, pause_after=0.9)
    assert plan[0]["after"] == 0.0 and plan[0]["line"] > 0


def test_a_segment_with_no_text_is_survivable():
    plan = rhythm.plan([{"text": ""}, {"text": "दूसरा"}], line_pause=0.45, pause_after=0.9)
    assert len(plan) == 2


# ---- the wire ---------------------------------------------------------------

def test_the_voice_lane_receives_the_mood():
    """The creator picks dard or hausla; it was stored on the video and then
    never reached the narration."""
    from app.pipeline.runner import _voice_rhythm

    assert _voice_rhythm({"mood": "sad"})["mood"] == "sad"


def test_the_plan_is_actually_used_by_the_synthesizer():
    import ast
    import inspect

    from app.pipeline import tts

    tree = ast.parse(inspect.getsource(tts.synth_script))
    calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)
             and isinstance(n.func, ast.Attribute) and n.func.attr == "plan"]
    assert calls, "synth_script no longer builds a rhythm plan"
