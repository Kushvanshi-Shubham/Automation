"""How a scene gets its visual, and what happens when it cannot.

These cover the chain that produced the rejected GTA render: the order
visuals are chosen in, what the model is told, what happens when a source
has nothing, and who pays for it.
"""
import asyncio
from pathlib import Path

import pytest

from app.pipeline import runner


class _Video:
    def __init__(self, **data):
        self.id = "vid"
        self.script_data = data
        self.visual_engine = data.get("_engine")
        self.user_id = "u"


ASPECT = {"w": 1080, "h": 1920, "orientation": "portrait"}


def _call(seg, *, ai_visuals=False, video=None, asset_paths=None, used_ids=None, client=None):
    return asyncio.run(runner._visual_for_scene(
        client, 0, seg, Path("clip.mp4"), 5.0,
        video=video or _Video(), aspect=ASPECT,
        asset_paths=asset_paths or {}, ai_visuals=ai_visuals,
        gen_keys={}, used_ids=used_ids if used_ids is not None else set(),
    ))


# ---- priority order ----------------------------------------------------------

def test_a_pinned_clip_wins_over_ai_generation(monkeypatch):
    """The bug this replaces: media_id sat BELOW the AI branch, so on the
    ai_image engine a creator could pin a clip to every scene, see seven green
    'Visual pinned' confirmations, pay, and get generated stills anyway."""
    pinned, generated = [], []

    async def fake_by_id(client, media_id, out, **kw):
        pinned.append(media_id)

    async def fake_generate(*a, **k):
        generated.append(1)

    monkeypatch.setattr(runner.pexels, "fetch_clip_by_id", fake_by_id)
    monkeypatch.setattr("app.services.image_gen.generate_image", fake_generate)

    _call({"text": "a line", "media_id": 42}, ai_visuals=True)

    assert pinned == [42], "the creator's pin must be used"
    assert not generated, "nothing should have been generated for a pinned scene"


def test_own_footage_wins_over_everything(monkeypatch):
    cut = []
    monkeypatch.setattr(runner.assembler, "cut_source", lambda *a, **k: cut.append(a))

    _call({"text": "a line", "asset_id": "abc", "media_id": 42},
          ai_visuals=True, asset_paths={"abc": Path("src.mp4")})

    assert cut, "uploaded footage is the creator's strongest signal"


def test_stock_is_the_last_resort(monkeypatch):
    queries = []

    async def fake_fetch(client, query, out, used, **kw):
        queries.append(query)

    monkeypatch.setattr(runner.pexels, "fetch_clip", fake_fetch)
    _call({"text": "the line", "visual_prompt": "a red door"})
    assert queries == ["a red door"]


def test_a_background_format_ignores_the_per_scene_prompt(monkeypatch):
    """Formats like Reddit Story run one continuous background."""
    queries = []

    async def fake_fetch(client, query, out, used, **kw):
        queries.append(query)

    monkeypatch.setattr(runner.pexels, "fetch_clip", fake_fetch)
    _call({"text": "the line", "visual_prompt": "a red door"},
          video=_Video(background_query="parkour gameplay"))
    assert queries == ["parkour gameplay"]


# ---- what the image model is told ---------------------------------------------

def test_the_narration_reaches_the_image_prompt(monkeypatch):
    """A visual_prompt written for stock search can be disconnected from its
    own line — passing the line means a thin prompt still lands near the
    subject rather than far from it."""
    prompts = []

    async def fake_generate(prompt, out, **kw):
        prompts.append(prompt)

    monkeypatch.setattr("app.services.image_gen.generate_image", fake_generate)
    monkeypatch.setattr(runner.assembler, "image_to_clip", lambda *a, **k: None)

    _call({"text": "The Oppressor MK2 lock-on radius was nerfed.",
           "visual_prompt": "a hover-bike banking over a highway"}, ai_visuals=True)

    assert prompts and "hover-bike" in prompts[0]
    assert "Oppressor MK2" in prompts[0], "the line is context for the image"


def test_the_prompt_still_bans_text():
    from app.services.image_gen import scene_prompt

    out = scene_prompt("a red door", says="A red door stands open.")
    assert "no text" in out.lower() and "no watermarks" in out.lower()


def test_the_prompt_specifies_one_aspect_not_two():
    """STYLE_SUFFIX used to append '(4:5)' after scene_prompt had already said
    '(9:16)' — two contradictory composition instructions in one string."""
    from app.services.image_gen import scene_prompt

    out = scene_prompt("a red door", aspect="9:16")
    assert "9:16" in out
    assert "4:5" not in out


# ---- failure handling ---------------------------------------------------------

def test_a_scene_with_no_stock_match_widens_the_query(monkeypatch):
    """Specific prompts mean more zero-result searches. Widening loses
    specificity; failing loses the whole render."""
    tried = []

    async def fake_fetch(client, query, out, used, **kw):
        tried.append(query)
        if len(tried) < 3:
            raise RuntimeError("no results")

    monkeypatch.setattr(runner.pexels, "fetch_clip", fake_fetch)
    asyncio.run(runner._fallback_visual(
        None, 0, {"text": "The armoured hover-bike banks over the neon highway"},
        Path("c.mp4"), 5.0,
        video=_Video(background_query="neon city night"), aspect=ASPECT, used_ids=set(),
    ))
    # Widening, not repeating: the format's theme, then a short noun phrase from
    # the line, then a query stock can always answer.
    assert tried == [
        "neon city night",
        "The armoured hover-bike banks",
        "abstract soft gradient background motion",
    ]


def test_the_format_background_is_tried_before_the_house_query(monkeypatch):
    tried = []

    async def fake_fetch(client, query, out, used, **kw):
        tried.append(query)

    monkeypatch.setattr(runner.pexels, "fetch_clip", fake_fetch)
    asyncio.run(runner._fallback_visual(
        None, 0, {"text": "a line"}, Path("c.mp4"), 5.0,
        video=_Video(background_query="city at night"), aspect=ASPECT, used_ids=set(),
    ))
    assert tried == ["city at night"]


def test_a_total_failure_names_the_scene(monkeypatch):
    async def always_fail(*a, **k):
        raise RuntimeError("dead")

    monkeypatch.setattr(runner.pexels, "fetch_clip", always_fail)
    with pytest.raises(RuntimeError, match="scene 1"):
        asyncio.run(runner._fallback_visual(
            None, 0, {"text": "a line"}, Path("c.mp4"), 5.0,
            video=_Video(), aspect=ASPECT, used_ids=set(),
        ))


# ---- the prompt rules the render depends on ------------------------------------

def test_the_visual_must_depict_its_own_line():
    """0/7 scene-specific visuals became 6/7 with this clause. It is the whole
    fix for the render the owner rejected."""
    from app.services.script_gen import _BASE_RULES, _POETIC_RULES

    for rules in (_BASE_RULES, _POETIC_RULES):
        assert "THIS" in rules or "this line" in rules.lower()
    assert "OWN LINE IS ABOUT" in _BASE_RULES
    assert "keyboard" in _BASE_RULES, "the concrete counter-example earns its place"


def test_no_format_assigns_the_visual_prompt_a_fixed_palette():
    """formats.py:245 ended the gaming recipe with 'visual_prompt = gaming
    setups, esports crowds, RGB keyboards, controller close-ups' — an
    ASSIGNMENT, and all seven rejected visuals were that list enumerated."""
    from app.services.formats import FORMATS

    for key, fmt in FORMATS.items():
        recipe = fmt.get("script_recipe") or ""
        if "visual_prompt =" not in recipe:
            continue
        clause = recipe.split("visual_prompt =", 1)[1]
        assert "THIS line" in clause or "the couplet itself" in clause or "is ignored" in clause, (
            f"{key}: the recipe still assigns visual_prompt a fixed palette instead of "
            "pointing it at the segment's own line"
        )
