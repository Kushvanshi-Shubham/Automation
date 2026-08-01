import asyncio
import io

import pytest


@pytest.fixture(autouse=True)
def cleanup_assets():
    yield
    from sqlalchemy import delete

    from app.database import AsyncSessionLocal
    from app.models.asset import Asset

    async def wipe():
        async with AsyncSessionLocal() as db:
            await db.execute(delete(Asset))
            await db.commit()

    asyncio.run(wipe())


@pytest.fixture(autouse=True)
def no_dispatch(monkeypatch):
    """Uploads must not hit the real Celery broker during tests."""
    dispatched = []
    import app.pipeline.asset_tasks as t

    monkeypatch.setattr(t.process_asset, "delay", lambda aid: dispatched.append(aid))
    return dispatched


def test_upload_rejects_bad_extension(client, auth_headers):
    resp = client.post(
        "/api/media-assets",
        headers=auth_headers,
        files={"file": ("malware.exe", io.BytesIO(b"xx"), "application/octet-stream")},
    )
    assert resp.status_code == 422


def test_upload_and_lifecycle(client, auth_headers, no_dispatch):
    resp = client.post(
        "/api/media-assets",
        headers=auth_headers,
        files={"file": ("podcast_ep1.mp4", io.BytesIO(b"fake video bytes"), "video/mp4")},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "uploaded"
    assert body["kind"] == "video"
    assert body["filename"] == "podcast_ep1.mp4"
    assert no_dispatch == [body["id"]]  # processing task dispatched

    listed = client.get("/api/media-assets", headers=auth_headers).json()
    assert any(a["id"] == body["id"] for a in listed)

    assert client.delete(f"/api/media-assets/{body['id']}", headers=auth_headers).status_code == 204
    assert client.get(f"/api/media-assets/{body['id']}", headers=auth_headers).status_code == 404


def test_audio_kind_detection(client, auth_headers, no_dispatch):
    resp = client.post(
        "/api/media-assets",
        headers=auth_headers,
        files={"file": ("episode.mp3", io.BytesIO(b"fake audio"), "audio/mpeg")},
    )
    assert resp.json()["kind"] == "audio"


def test_highlight_suggestion_validation():
    from app.pipeline.transcribe import suggest_highlights

    async def run():
        import app.services.llm as llm

        async def fake_generate(system, user, temperature=0.4, model="auto", user_keys=None):
            return {"highlights": [
                {"start": 10, "end": 40, "title": "Great moment", "reason": "strong hook"},
                {"start": 5, "end": 8, "title": "too short", "reason": "x"},      # < 5s → dropped
                {"start": 0, "end": 300, "title": "too long", "reason": "x"},     # > 90s → dropped
                {"start": "bad", "end": 1, "title": "invalid", "reason": "x"},    # bad types → dropped
            ]}

        orig = llm.generate_json
        llm.generate_json = fake_generate
        try:
            return await suggest_highlights({"segments": [{"start": 0, "end": 60, "text": "hello"}]})
        finally:
            llm.generate_json = orig

    out = asyncio.run(run())
    assert len(out) == 1
    assert out[0]["title"] == "Great moment"
