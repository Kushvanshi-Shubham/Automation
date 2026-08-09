"""The Pro voice lane: gated by plan, surcharged unless the creator
brings their own key, and never silently downgraded."""
import pytest

from app.services import premium_voice


@pytest.fixture()
def mock_generate(monkeypatch):
    async def fake_generate(topic, **kwargs):
        return {
            "title": "t", "description": "d", "tags": [],
            "segments": [{"text": "hello world", "visual_prompt": "x", "duration_estimate": 2.0}],
            "total_duration": 2.0,
        }

    monkeypatch.setattr("app.routers.scripts.script_gen.generate_script", fake_generate)


@pytest.fixture()
def no_worker(monkeypatch):
    class _Task:
        id = "t"

    monkeypatch.setattr("app.pipeline.tasks.run_pipeline.delay", lambda *_a, **_k: _Task())


@pytest.fixture()
def platform_voice_key(monkeypatch):
    monkeypatch.setattr("app.config.settings.CARTESIA_API_KEY", "sk_car_test")


def _new_video(client, auth_headers):
    return client.post("/api/scripts/generate", headers=auth_headers,
                       json={"custom_prompt": "a story about voices"}).json()["video_id"]


def _top_up(email="creator@example.com", to=50):
    """Earlier tests spend the shared user's credits — set a known balance."""
    import asyncio

    from sqlalchemy import select

    from app.database import AsyncSessionLocal
    from app.models.user import User

    async def _run():
        async with AsyncSessionLocal() as db:
            user = (await db.execute(select(User).where(User.email == email))).scalar_one()
            user.credit_balance = to
            await db.commit()

    asyncio.run(_run())


def test_providers_follow_the_available_keys(monkeypatch):
    monkeypatch.setattr("app.config.settings.CARTESIA_API_KEY", None)
    monkeypatch.setattr("app.config.settings.ELEVENLABS_API_KEY", None)
    assert premium_voice.available_providers() == []
    assert premium_voice.available_providers({"cartesia": "k"}) == ["cartesia"]
    monkeypatch.setattr("app.config.settings.ELEVENLABS_API_KEY", "platform")
    assert "elevenlabs" in premium_voice.available_providers()


def test_unknown_provider_is_rejected(client, auth_headers, mock_generate, no_worker):
    video_id = _new_video(client, auth_headers)
    resp = client.post("/api/pipeline/start", headers=auth_headers,
                       json={"video_id": video_id, "visual_engine": "pexels",
                             "voice_provider": "robovoice", "voice_id": "x"})
    assert resp.status_code == 422
    assert "narration provider" in resp.json()["detail"]


def test_premium_voice_needs_a_voice_id(client, auth_headers, mock_generate, no_worker, platform_voice_key):
    video_id = _new_video(client, auth_headers)
    resp = client.post("/api/pipeline/start", headers=auth_headers,
                       json={"video_id": video_id, "visual_engine": "pexels", "voice_provider": "cartesia"})
    assert resp.status_code == 422
    assert "Pick a voice" in resp.json()["detail"]


def test_premium_voice_costs_extra_credits(client, auth_headers, mock_generate, no_worker, platform_voice_key):
    _top_up()
    before = client.get("/api/billing/credits", headers=auth_headers).json()["balance"]
    video_id = _new_video(client, auth_headers)
    resp = client.post("/api/pipeline/start", headers=auth_headers,
                       json={"video_id": video_id, "visual_engine": "pexels",
                             "voice_provider": "cartesia", "voice_id": "voice-123"})
    assert resp.status_code == 200
    # 1 credit for the stock render + 3 for studio-grade narration
    after = client.get("/api/billing/credits", headers=auth_headers).json()["balance"]
    assert before - after == 4

    script = client.get(f"/api/scripts/{video_id}", headers=auth_headers).json()
    assert script["defaults"]["voice_id"] == "voice-123"
    client.post(f"/api/pipeline/{resp.json()['job_id']}/cancel", headers=auth_headers)


def test_no_surcharge_when_the_creator_brings_their_own_key(
    client, auth_headers, mock_generate, no_worker, platform_voice_key, monkeypatch
):
    async def fake_keys(db, user_id):
        return {"cartesia": "sk_car_theirs"}

    monkeypatch.setattr("app.routers.pipeline.get_user_keys", fake_keys)
    _top_up()
    before = client.get("/api/billing/credits", headers=auth_headers).json()["balance"]
    video_id = _new_video(client, auth_headers)
    resp = client.post("/api/pipeline/start", headers=auth_headers,
                       json={"video_id": video_id, "visual_engine": "pexels",
                             "voice_provider": "cartesia", "voice_id": "voice-123"})
    assert resp.status_code == 200
    after = client.get("/api/billing/credits", headers=auth_headers).json()["balance"]
    assert before - after == 1  # their spend, not ours
    client.post(f"/api/pipeline/{resp.json()['job_id']}/cancel", headers=auth_headers)


def test_free_plan_cannot_use_studio_voices(
    client, auth_headers, mock_generate, no_worker, platform_voice_key, monkeypatch
):
    from tests.test_plans import _set_plan

    _set_plan("creator@example.com", "free")
    monkeypatch.setattr("app.config.settings.PLAN_ENFORCEMENT_ENABLED", True)
    monkeypatch.setattr("app.config.settings.ADMIN_EMAILS", [])
    video_id = _new_video(client, auth_headers)
    resp = client.post("/api/pipeline/start", headers=auth_headers,
                       json={"video_id": video_id, "visual_engine": "pexels",
                             "voice_provider": "cartesia", "voice_id": "voice-123"})
    assert resp.status_code == 402
    assert "Pro" in resp.json()["detail"]


def test_missing_key_asks_for_one(client, auth_headers, mock_generate, no_worker, monkeypatch):
    monkeypatch.setattr("app.config.settings.CARTESIA_API_KEY", None)
    video_id = _new_video(client, auth_headers)
    resp = client.post("/api/pipeline/start", headers=auth_headers,
                       json={"video_id": video_id, "visual_engine": "pexels",
                             "voice_provider": "cartesia", "voice_id": "v"})
    assert resp.status_code == 422
    assert "Settings" in resp.json()["detail"]
