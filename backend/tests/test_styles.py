"""Teach a style: learn endpoint, catalog listing, and use in script generation."""
import asyncio
import uuid

import pytest

TRANSCRIPT = {
    "language": "en",
    "segments": [{
        "start": 0, "end": 3, "text": "hey you need to see this",
        "words": [{"word": "hey", "start": 0, "end": 0.3}],
    }],
}


@pytest.fixture(autouse=True)
def cleanup_styles():
    yield
    from sqlalchemy import delete

    from app.database import AsyncSessionLocal
    from app.models.asset import Asset
    from app.models.user_format import UserFormat

    async def wipe():
        async with AsyncSessionLocal() as db:
            # Learned styles must not bleed into test_formats' exact-catalog check.
            await db.execute(delete(UserFormat))
            await db.execute(delete(Asset))
            await db.commit()

    asyncio.run(wipe())


@pytest.fixture(autouse=True)
def no_learn_dispatch(monkeypatch):
    """Learning must not hit the real Celery broker during tests."""
    dispatched = []
    import app.pipeline.style_tasks as t

    monkeypatch.setattr(t.learn_style, "delay", lambda ufid: dispatched.append(ufid))
    return dispatched


@pytest.fixture()
def capture_generate(monkeypatch):
    captured = {}

    async def fake_generate(topic, **kwargs):
        captured["topic"] = topic
        captured.update(kwargs)
        return {
            "title": "t", "description": "d", "tags": [],
            "segments": [{"text": "hello world", "visual_prompt": "x", "duration_estimate": 2.0}],
            "total_duration": 2.0,
        }

    monkeypatch.setattr("app.routers.scripts.script_gen.generate_script", fake_generate)
    return captured


def _user_id(email="creator@example.com"):
    from sqlalchemy import select

    from app.database import AsyncSessionLocal
    from app.models.user import User

    async def fetch():
        async with AsyncSessionLocal() as db:
            return str((await db.execute(select(User).where(User.email == email))).scalar_one().id)

    return asyncio.run(fetch())


def _insert_asset(user_id, **overrides):
    from uuid import UUID

    from app.database import AsyncSessionLocal
    from app.models.asset import Asset

    fields = dict(
        user_id=UUID(str(user_id)),
        filename="reel1.mp4",
        kind="video",
        path="x.mp4",
        duration=30.0,
        status="ready",
        transcript=TRANSCRIPT,
    )
    fields.update(overrides)

    async def insert():
        async with AsyncSessionLocal() as db:
            asset = Asset(**fields)
            db.add(asset)
            await db.commit()
            return str(asset.id)

    return asyncio.run(insert())


def _make_ready(style_id, **overrides):
    from uuid import UUID

    from app.database import AsyncSessionLocal
    from app.models.user_format import UserFormat

    fields = dict(
        status="ready",
        script_recipe="HOOK with a bold claim, short punchy sentences, end with a question CTA.",
        caption_style="karaoke",
        music_mood="energetic",
        tone="fast and confident",
        profile={"summary": "Fast, punchy, question-driven reels.", "reels": 2,
                 "avg_wps": 3.1, "hooks": ["hey you need to see this"]},
    )
    fields.update(overrides)

    async def flip():
        async with AsyncSessionLocal() as db:
            uf = await db.get(UserFormat, UUID(str(style_id)))
            for k, v in fields.items():
                setattr(uf, k, v)
            await db.commit()

    asyncio.run(flip())


def _learn(client, auth_headers, asset_ids, **extra):
    return client.post("/api/styles/learn", headers=auth_headers,
                       json={"name": "My reel style", "asset_ids": asset_ids, **extra})


def test_learn_validation(client, auth_headers, no_learn_dispatch):
    uid = _user_id()
    good = _insert_asset(uid)

    # unknown asset
    resp = _learn(client, auth_headers, [good, str(uuid.uuid4())])
    assert resp.status_code == 422

    # fewer than 2 assets
    assert _learn(client, auth_headers, [good]).status_code == 422

    # bad output_type
    other = _insert_asset(uid, filename="reel2.mp4")
    assert _learn(client, auth_headers, [good, other], output_type="clip").status_code == 422

    # not-ready and transcript-less assets are named in plain English
    processing = _insert_asset(uid, filename="cooking.mp4", status="processing")
    resp = _learn(client, auth_headers, [good, processing])
    assert resp.status_code == 422 and "cooking.mp4" in resp.json()["detail"]

    silent = _insert_asset(uid, filename="silent.mp4", transcript=None)
    resp = _learn(client, auth_headers, [good, silent])
    assert resp.status_code == 422 and "transcript" in resp.json()["detail"]

    audio = _insert_asset(uid, filename="pod.mp3", kind="audio")
    assert _learn(client, auth_headers, [good, audio]).status_code == 422

    assert no_learn_dispatch == []  # nothing enqueued on any failure


def test_learn_happy_path_and_list(client, auth_headers, no_learn_dispatch):
    uid = _user_id()
    a1 = _insert_asset(uid)
    a2 = _insert_asset(uid, filename="reel2.mp4")

    resp = _learn(client, auth_headers, [a1, a2])
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "learning"
    assert no_learn_dispatch == [body["id"]]

    items = client.get("/api/styles", headers=auth_headers).json()["items"]
    assert [i["id"] for i in items] == [body["id"]]
    assert items[0]["name"] == "My reel style"
    assert items[0]["status"] == "learning"
    assert items[0]["output_type"] == "narrated"

    assert client.delete(f"/api/styles/{body['id']}", headers=auth_headers).status_code == 204
    assert client.get("/api/styles", headers=auth_headers).json()["items"] == []


def test_delete_missing_and_foreign(client, auth_headers):
    assert client.delete(f"/api/styles/{uuid.uuid4()}", headers=auth_headers).status_code == 404

    # Someone else's style is invisible — 404, not 403.
    from app.database import AsyncSessionLocal
    from app.models.user import User
    from app.models.user_format import UserFormat

    async def insert_foreign():
        async with AsyncSessionLocal() as db:
            other = User(email="other@example.com", google_id="google-other-456")
            db.add(other)
            await db.flush()
            uf = UserFormat(user_id=other.id, name="Not yours", status="ready")
            db.add(uf)
            await db.commit()
            return str(uf.id)

    foreign_id = asyncio.run(insert_foreign())
    assert client.delete(f"/api/styles/{foreign_id}", headers=auth_headers).status_code == 404


def test_style_limit(client, auth_headers, no_learn_dispatch):
    uid = _user_id()
    a1 = _insert_asset(uid)
    a2 = _insert_asset(uid, filename="reel2.mp4")
    for _ in range(5):
        assert _learn(client, auth_headers, [a1, a2]).status_code == 200
    resp = _learn(client, auth_headers, [a1, a2])
    assert resp.status_code == 422 and "Style limit" in resp.json()["detail"]


def test_generate_while_learning_rejected(client, auth_headers, no_learn_dispatch):
    uid = _user_id()
    a1 = _insert_asset(uid)
    a2 = _insert_asset(uid, filename="reel2.mp4")
    style_id = _learn(client, auth_headers, [a1, a2]).json()["id"]

    resp = client.post("/api/scripts/generate", headers=auth_headers,
                       json={"custom_prompt": "why my plants keep dying",
                             "format": f"user:{style_id}"})
    assert resp.status_code == 422
    assert "still learning" in resp.json()["detail"]

    # unknown / not-owned styles 422 too
    resp = client.post("/api/scripts/generate", headers=auth_headers,
                       json={"custom_prompt": "why my plants keep dying",
                             "format": f"user:{uuid.uuid4()}"})
    assert resp.status_code == 422 and resp.json()["detail"] == "Unknown style"


def test_generate_with_ready_style(client, auth_headers, no_learn_dispatch, capture_generate):
    uid = _user_id()
    a1 = _insert_asset(uid)
    a2 = _insert_asset(uid, filename="reel2.mp4")
    style_id = _learn(client, auth_headers, [a1, a2]).json()["id"]
    _make_ready(style_id)

    resp = client.post("/api/scripts/generate", headers=auth_headers,
                       json={"custom_prompt": "why my plants keep dying",
                             "format": f"user:{style_id}"})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["format"] == f"user:{style_id}"
    assert body["output_type"] == "narrated"
    assert body["defaults"]["caption_style"] == "karaoke"
    assert body["defaults"]["music_mood"] == "energetic"

    # the learned recipe leads the instruction stack and the tone applies
    assert "HOOK with a bold claim" in capture_generate["custom_instructions"]
    assert capture_generate["tone"] == "fast and confident"

    # defaults round-trip through GET so the studio can seed its pickers
    script = client.get(f"/api/scripts/{body['video_id']}", headers=auth_headers).json()
    assert script["format"] == f"user:{style_id}"
    assert script["defaults"]["caption_style"] == "karaoke"


def test_formats_catalog_includes_ready_styles(client, auth_headers, no_learn_dispatch):
    uid = _user_id()
    a1 = _insert_asset(uid)
    a2 = _insert_asset(uid, filename="reel2.mp4")

    learning_id = _learn(client, auth_headers, [a1, a2]).json()["id"]
    ready_id = _learn(client, auth_headers, [a1, a2]).json()["id"]
    _make_ready(ready_id)

    items = client.get("/api/scripts/formats", headers=auth_headers).json()["items"]
    by_key = {i["key"]: i for i in items}

    assert f"user:{learning_id}" not in by_key  # only READY styles are offered
    mine = by_key[f"user:{ready_id}"]
    assert mine["own"] is True
    assert mine["label"] == "My reel style"
    assert mine["desc"] == "Fast, punchy, question-driven reels."
    assert mine["output_type"] == "narrated"
    assert mine["available"] is True
    assert mine["controls"] == ["voice", "captions", "aspect", "scenes"]

    # built-ins are marked own=False and come first
    assert by_key["reddit_story"]["own"] is False
    assert items[0]["own"] is False
