"""Does the visual mismatch come from the model, or from our own prompt?

The GTA render that started this produced seven visual prompts about gaming
peripherals for a script about a vehicle patch. Two candidate explanations:

  A. the model cannot couple a visual to its own line (an industry-hard
     problem — the whole market complains about it, so a real moat)
  B. our own recipe told it not to (an own goal — no moat, just a bug)

formats.py ends the gaming_update recipe with
  "visual_prompt = gaming setups, esports crowds, RGB keyboards,
   controller close-ups (no copyrighted game footage)."
which assigns the field a fixed palette, and _BASE_RULES never says the
visual must depict its OWN line. That clause exists in the repo exactly once,
on the bring-your-own-script path.

This runs the same subject through three prompt variants and prints the
visual prompts side by side. No render, no credits — just the script call.

    python scripts/visual_relevance_experiment.py

It does not modify any application file; the variants are monkeypatched.
"""
import argparse
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# The exact subject of the rejected render.
SUBJECT = "GTA 5 LIVE | MRRAJAPLAY #gtalive #gtaonline #gta5 #gtav #gaming"

# What the model was actually told, from formats.py gaming_update.
RECIPE_AS_IS = (
    "FORMAT: gaming update. You're the friend who read the patch notes so the viewer doesn't "
    "have to. Hook = the single biggest change gamers care about. Then the buffs/nerfs/new "
    "content that actually change how people play, with hype but zero filler. Gamer-native "
    "vocabulary (meta, nerfed, buffed) without cringe. visual_prompt = gaming setups, esports "
    "crowds, RGB keyboards, controller close-ups (no copyrighted game footage)."
)

# Same recipe with the palette assignment removed. Nothing else changes.
RECIPE_NO_PALETTE = (
    "FORMAT: gaming update. You're the friend who read the patch notes so the viewer doesn't "
    "have to. Hook = the single biggest change gamers care about. Then the buffs/nerfs/new "
    "content that actually change how people play, with hype but zero filler. Gamer-native "
    "vocabulary (meta, nerfed, buffed) without cringe."
)

# The coupling clause, lifted from the wording already used on the
# bring-your-own-script path (script_gen.py CUSTOM_SCRIPT_PROMPT).
COUPLING = (
    "- Every segment includes a visual_prompt: a concrete, filmable description of what THIS "
    "segment's own line is about — if the line names a vehicle, a place or an event, the visual "
    "must show that thing, described physically. Never a generic scene from the topic's wider "
    "category. Do not name trademarks, brands or real people; describe them instead (say "
    "\"a matte-black armoured hover-bike with a roof-mounted missile pod\", not the product name).\n"
)


def variants():
    from app.services import script_gen

    base = script_gen._BASE_RULES
    old_line = (
        "- Every segment includes a visual_prompt: a concrete, filmable description for stock-footage\n"
        "  search or AI video generation (no text overlays, no brand names, no celebrity likenesses).\n"
    )
    assert old_line in base, "base rules changed — update this experiment"
    coupled = base.replace(old_line, COUPLING)

    return [
        ("1. AS SHIPPED", base, RECIPE_AS_IS),
        ("2. palette removed only", base, RECIPE_NO_PALETTE),
        ("3. palette removed + coupling clause", coupled, RECIPE_NO_PALETTE),
    ]


async def run_one(name, rules, recipe, model):
    from app.services import script_gen

    original = script_gen._BASE_RULES
    script_gen._BASE_RULES = rules
    # STYLE_PROMPTS was built from _BASE_RULES at import time, so rebuild the
    # one style this format uses (news_update) with the patched rules.
    original_style = script_gen.STYLE_PROMPTS["news_update"]
    script_gen.STYLE_PROMPTS["news_update"] = original_style.replace(original, rules)
    try:
        return await script_gen.generate_script(
            topic=SUBJECT,
            tone="hype and energetic",
            duration_seconds=60,
            style="news_update",
            custom_instructions=recipe,
            model=model,
        )
    finally:
        script_gen._BASE_RULES = original
        script_gen.STYLE_PROMPTS["news_update"] = original_style


ENTITY_WORDS = {
    "gta", "oppressor", "vigilante", "rockstar", "heist", "vault", "bike", "hover",
    "car", "vehicle", "missile", "los santos", "chopper", "jet", "armoured", "armored",
    "motorcycle", "helicopter", "casino", "depot",
}
GENERIC_WORDS = {
    "keyboard", "rgb", "monitor", "desk", "headset", "controller", "mouse", "lan",
    "streamer", "setup", "pc tower", "gamer", "esports crowd", "cable", "chair",
}


def score(segments):
    ent = gen = 0
    for s in segments:
        v = (s.get("visual_prompt") or "").lower()
        if any(w in v for w in ENTITY_WORDS):
            ent += 1
        if any(w in v for w in GENERIC_WORDS):
            gen += 1
    return ent, gen


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="auto")
    args = ap.parse_args()

    results = []
    for name, rules, recipe in variants():
        print(f"\n{'=' * 78}\n{name}\n{'=' * 78}")
        try:
            out = await run_one(name, rules, recipe, args.model)
        except Exception as exc:
            print(f"  FAILED: {type(exc).__name__}: {exc}")
            continue
        segs = out.get("segments", [])
        for i, s in enumerate(segs):
            print(f"  [{i}] {(s.get('text') or '')[:78]}")
            print(f"      -> {(s.get('visual_prompt') or '')[:100]}")
        ent, gen = score(segs)
        results.append((name, len(segs), ent, gen))
        print(f"  scene-specific: {ent}/{len(segs)}   generic-peripheral: {gen}/{len(segs)}")

    print(f"\n{'=' * 78}\nSUMMARY — visual prompts naming something from their own line\n{'=' * 78}")
    for name, n, ent, gen in results:
        print(f"  {name:38s} specific {ent}/{n}   generic {gen}/{n}")
    print(
        "\nIf variant 1 is ~0 specific and variant 3 is most specific, the mismatch is\n"
        "OUR PROMPT, not the model — and 'nobody has solved visual relevance' is not a\n"
        "moat we can claim, because we had not tried."
    )


if __name__ == "__main__":
    asyncio.run(main())
