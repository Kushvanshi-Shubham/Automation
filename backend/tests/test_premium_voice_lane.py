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
