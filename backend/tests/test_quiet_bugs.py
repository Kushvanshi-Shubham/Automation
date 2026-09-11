"""Four bugs that failed silently.

None of these raised an error, showed a warning, or looked wrong in the UI.
They were found by reading code, which is why each gets a test — the next
person to touch these files will not know what they are for otherwise.
"""
import asyncio

import pytest


# ---- 1. bring-your-own-script threw away everything the creator configured ----

@pytest.fixture()
def capture_custom(monkeypatch):
    captured = {}

    async def fake_format(script_text, **kwargs):
        captured["script_text"] = script_text
        captured.update(kwargs)
        return {
            "title": "t", "description": "d", "tags": [],
            "segments": [{"text": "their exact words", "visual_prompt": "x", "duration_estimate": 2.0}],
            "total_duration": 2.0,
        }

    monkeypatch.setattr("app.routers.scripts.script_gen.format_custom_script", fake_format)
    return captured


def test_a_pasted_script_still_gets_the_creators_settings(client, auth_headers, capture_custom):
    """The format recipe, the mood, their typed instructions, their learned
    style and their standing feedback notes were all assembled and then
    dropped on this path — the function did not even take the argument."""
    resp = client.post("/api/scripts/generate", headers=auth_headers, json={
        "custom_script": "This is my own writing and nobody should change a word of it. "
                         "It is long enough to pass the minimum length check easily.",
        "format": "shayari",
        "custom_instructions": "always use rain imagery",
    })
    assert resp.status_code == 200, resp.text

    instructions = capture_custom.get("custom_instructions")
    assert instructions, "the creator's settings never reached the generator"
    assert "rain imagery" in instructions, "their own typed instruction was dropped"


def test_the_wording_promise_is_protected():
    """Settings apply to visuals, captions and music — never the text. This
    path's one promise is that their words survive untouched, so a standing
    note like 'always end with follow for part 2' must not add a line."""
    from app.services.script_gen import format_custom_script
    import inspect

    src = inspect.getsource(format_custom_script)
    assert "must NOT change, add to" in src
    assert "ignore that part" in src, "the model needs an explicit instruction to skip wording rules"


def test_no_settings_means_no_extra_prompt_text():
    """A creator with nothing configured must get the original prompt."""
    import inspect
    from app.services.script_gen import format_custom_script

    # The guard block is only appended when there is something to append.
    src = inspect.getsource(format_custom_script)
    assert 'guarded = ""' in src


# ---- 2. the two lanes that cost money reported as free ------------------------

def test_the_expensive_lanes_are_priced():
    """SERVICES is built from UNIT_COSTS_USD's keys, so a tracked service
    missing from the dict was counted and then priced at zero — the
    economics panel was structurally unable to report a loss."""
    from app.services.costs import SERVICES, UNIT_COSTS_USD

    for service in ("premium_voice", "ai_image"):
        assert service in UNIT_COSTS_USD, f"{service} is tracked but has no price"
        assert UNIT_COSTS_USD[service] > 0, f"{service} priced at zero"
        assert service in SERVICES


def test_the_two_cost_tables_agree():
    """credits.py prices what we CHARGE; costs.py prices what we PAY. If they
    disagree on the same lane, one of them is lying about the margin."""
    from app.services.costs import UNIT_COSTS_USD
    from app.services.credits import ENGINE_REAL_COST_USD

    assert UNIT_COSTS_USD["premium_voice"] == ENGINE_REAL_COST_USD["premium_voice"]


def test_image_generation_is_counted():
    """image_gen had no track() call at all, so the most expensive lane in
    the product was invisible to the economics panel."""
    import inspect

    from app.services import image_gen

    src = inspect.getsource(image_gen.generate_image)
    assert 'track("ai_image")' in src
    # And only on success — a filtered or failed call bills nothing.
    assert src.index("f.write(inline.data)") < src.index('track("ai_image")')


# ---- 3. Whisper was guessing the language ------------------------------------

def test_the_language_hint_maps_our_offered_languages():
    """Auto-detect decides from the opening seconds and flips mid-file on
    Hinglish, dragging the word timings — and those timings are the captions."""
    from app.pipeline.transcribe import LANGUAGE_CODES
    from app.services.voices import LANGUAGES

    for language in LANGUAGES:
        assert language.lower() in LANGUAGE_CODES, f"{language} has no Whisper code"
    assert LANGUAGE_CODES["hindi"] == "hi"


def test_an_unknown_language_falls_back_to_autodetect():
    """A missing or unrecognised language must not crash — None means
    Whisper decides, which is the old behaviour."""
    from app.pipeline.transcribe import LANGUAGE_CODES

    assert LANGUAGE_CODES.get("klingon") is None
    assert LANGUAGE_CODES.get("") is None


def test_generated_speech_is_transcribed_in_the_language_we_spoke():
    import inspect

    from app.services import premium_voice

    src = inspect.getsource(premium_voice)
    assert "transcribe.transcribe, out_path, language" in src, (
        "we know what language we just spoke — never make Whisper guess it back"
    )


# ---- 4. deleting footage silently broke every video using it -----------------

def _insert_asset(user_id):
    from uuid import UUID

    from app.database import AsyncSessionLocal
    from app.models.asset import Asset

    async def run():
        async with AsyncSessionLocal() as db:
            asset = Asset(user_id=UUID(str(user_id)), filename="gameplay.mp4", kind="video",
                          path="C:/nonexistent/g.mp4", duration=120.0, status="ready")
            db.add(asset)
            await db.commit()
            return str(asset.id)

    return asyncio.run(run())


def _insert_video(user_id, script_data):
    from uuid import UUID

    from app.database import AsyncSessionLocal
    from app.models.video import Video

    async def run():
        async with AsyncSessionLocal() as db:
            v = Video(user_id=UUID(str(user_id)), title="My short", status="ready",
                      output_type="narrated", script_data=script_data)
            db.add(v)
            await db.commit()
            return str(v.id)

    return asyncio.run(run())


def test_footage_still_used_by_a_video_cannot_be_deleted(client, auth_headers):
    """A video stores only the asset ID, not the footage. Deleting the upload
    breaks it, and the creator finds out on a re-render, after it is gone."""
    me = client.get("/api/auth/me", headers=auth_headers).json()
    asset_id = _insert_asset(me["id"])
    _insert_video(me["id"], {"segments": [{"text": "a line", "asset_id": asset_id}]})

    resp = client.delete(f"/api/media-assets/{asset_id}", headers=auth_headers)
    assert resp.status_code == 409
    detail = resp.json()["detail"]
    assert "My short" in detail, "name the videos so the creator can go and unpin"
    assert "Unpin" in detail


def test_the_guard_covers_clips_and_montages_too(client, auth_headers):
    me = client.get("/api/auth/me", headers=auth_headers).json()
    for key, data in (
        ("clip", lambda a: {"clip": {"asset_id": a, "start": 0, "end": 9}}),
        ("montage", lambda a: {"montage": {"asset_id": a, "ranges": []}}),
    ):
        asset_id = _insert_asset(me["id"])
        _insert_video(me["id"], data(asset_id))
        resp = client.delete(f"/api/media-assets/{asset_id}", headers=auth_headers)
        assert resp.status_code == 409, f"{key} render was not protected"


def test_unused_footage_deletes_normally(client, auth_headers):
    """The guard must not make the delete button useless."""
    me = client.get("/api/auth/me", headers=auth_headers).json()
    asset_id = _insert_asset(me["id"])
    resp = client.delete(f"/api/media-assets/{asset_id}", headers=auth_headers)
    assert resp.status_code == 204
