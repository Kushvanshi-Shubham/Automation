"""The paid voice lane, which was entirely dead in production.

Found while answering "can we use Deepgram": both premium providers failed.
Cartesia returned 400 "Model sunsetted" for sonic-2, and the ElevenLabs key
in production could not authenticate. A creator picking a studio voice paid
3 extra credits and got an error - and nothing in the product noticed.

The offline tests here are cheap and always run. The live one is opt-in
(KLIPTOS_LIVE_VOICE=1) because it spends real money.
"""
import os

import pytest

from app.services import premium_voice as pv


def test_the_cartesia_model_is_not_a_sunsetted_one():
    """sonic-2 and sonic are both retired; they return 400 on every call."""
    assert pv.CARTESIA_MODEL not in ("sonic", "sonic-2"), "back on a sunsetted model"
    assert pv.CARTESIA_MODEL == "sonic-3"


def test_both_providers_are_still_declared():
    assert set(pv.PROVIDERS) == {"cartesia", "elevenlabs"}


def test_a_provider_with_no_key_is_not_offered():
    """available_providers is what the studio lists. Offering a provider we
    cannot authenticate is how a creator pays and then fails."""
    assert pv.available_providers({}) == [] or all(
        pv.platform_key(p) for p in pv.available_providers({})
    )


@pytest.mark.skipif(not os.environ.get("KLIPTOS_LIVE_VOICE"),
                    reason="spends real money; set KLIPTOS_LIVE_VOICE=1")
@pytest.mark.asyncio
async def test_cartesia_really_speaks_hindi(tmp_path):
    """The one that would have caught this. Shayari is the launch format and
    it is Hindi, so 'the lane works' means nothing unless it works in Hindi."""
    voices = await pv.list_voices("cartesia")
    hindi = [v for v in voices if str(v.get("language", "")).lower().startswith("hi")]
    assert hindi, "no Hindi voice available - shayari cannot use this provider"

    out = tmp_path / "sher.mp3"
    await pv.synthesize("बारिश आज भी छत को भीगोती है।", out, hindi[0]["id"],
                        "cartesia", language="hi")
    assert out.exists() and out.stat().st_size > 5000


# ---- a free plan must not be offered voices it cannot call -------------------

def _el(name, category, cloned=False):
    return {"id": name, "name": name, "provider": "elevenlabs",
            "category": category, "cloned": cloned, "language": "en"}


def test_a_paid_only_voice_is_never_the_default_pick():
    """ElevenLabs "professional" voices return 402 on a free plan. We sorted
    them to the top, so the default selection failed on a lane the studio had
    just advertised as available."""
    rows = [_el("Priyanka", "professional"), _el("Roger", "premade")]
    rows.sort(key=lambda v: (not pv._is_callable(v), not v["cloned"], v["name"].lower()))
    assert rows[0]["name"] == "Roger"


def test_a_creators_own_cloned_voice_still_wins():
    """Cloning is the whole reason someone adds their own key. A usable
    cloned voice must still outrank a stock one."""
    rows = [_el("Roger", "premade"), _el("Mine", "cloned", cloned=True)]
    rows.sort(key=lambda v: (not pv._is_callable(v), not v["cloned"], v["name"].lower()))
    assert rows[0]["name"] == "Mine"


def test_cartesia_voices_are_never_filtered():
    """Only ElevenLabs has the paid-voice split. Treating a Cartesia voice as
    blocked would hide all four Hindi voices — the ones shayari needs."""
    assert pv._is_callable({"provider": "cartesia", "name": "Aadhya"})


def test_a_voice_with_no_category_is_assumed_usable():
    """Older stored voices predate the field; assuming blocked would empty
    the list for everyone who already picked one."""
    assert pv._is_callable({"provider": "elevenlabs", "name": "x", "cloned": False})


def test_the_payment_error_says_what_to_do():
    """402 carried the one sentence that explained the failure and we replaced
    it with 'couldn't produce that narration', which nobody can act on."""
    import inspect

    src = inspect.getsource(pv.synthesize)
    assert "resp.status_code == 402" in src
    assert "paid plan" in src
