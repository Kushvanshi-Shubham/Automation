import asyncio
import io

import pytest


@pytest.fixture(autouse=True)
def cleanup_assets():
    yield
    from sqlalchemy import delete, select

    from app.database import AsyncSessionLocal
    from app.models.asset import Asset
    from app.models.credit import CreditLedger
    from app.models.pipeline_job import PipelineJob
    from app.models.video import Video

    async def wipe():
        async with AsyncSessionLocal() as db:
            # Clip videos (and their jobs/ledger rows) must not bleed into
            # other modules' pagination-sensitive tests.
            clip_ids = (await db.execute(select(Video.id).where(Video.output_type == "clip"))).scalars().all()
            if clip_ids:
                await db.execute(delete(PipelineJob).where(PipelineJob.video_id.in_(clip_ids)))
                await db.execute(delete(CreditLedger).where(CreditLedger.video_id.in_(clip_ids)))
                await db.execute(delete(Video).where(Video.id.in_(clip_ids)))
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


# Minimal valid-looking file heads (magic bytes) for the content sniff.
FAKE_MP4 = b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 64
FAKE_MP3 = b"ID3\x04\x00\x00\x00\x00\x00\x00" + b"\x00" * 64


def test_upload_rejects_bad_extension(client, auth_headers):
    resp = client.post(
        "/api/media-assets",
        headers=auth_headers,
        files={"file": ("malware.exe", io.BytesIO(b"xx"), "application/octet-stream")},
    )
    assert resp.status_code == 422


def test_upload_rejects_mismatched_content(client, auth_headers, no_dispatch):
    """An .mp4 whose bytes are not a video container must be rejected."""
    resp = client.post(
        "/api/media-assets",
        headers=auth_headers,
        files={"file": ("totally_a_video.mp4", io.BytesIO(b"#!/bin/sh\nrm -rf /"), "video/mp4")},
    )
    assert resp.status_code == 422
    assert "content" in resp.json()["detail"].lower()
    assert no_dispatch == []


def test_upload_and_lifecycle(client, auth_headers, no_dispatch):
    resp = client.post(
        "/api/media-assets",
        headers=auth_headers,
        files={"file": ("podcast_ep1.mp4", io.BytesIO(FAKE_MP4), "video/mp4")},
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
        files={"file": ("episode.mp3", io.BytesIO(FAKE_MP3), "audio/mpeg")},
    )
    assert resp.json()["kind"] == "audio"


def test_words_in_range_shifts_and_clips():
    from app.pipeline.transcribe import words_in_range

    transcript = {"segments": [
        {"start": 0, "end": 5, "text": "hello there", "words": [
            {"word": "hello", "start": 0.5, "end": 1.0},
            {"word": "there", "start": 1.2, "end": 1.8},
        ]},
        {"start": 5, "end": 12, "text": "the best moment ever", "words": [
            {"word": "the", "start": 5.5, "end": 5.8},
            {"word": "best", "start": 6.0, "end": 6.5},
            {"word": "moment", "start": 6.7, "end": 7.4},
            {"word": "ever", "start": 9.9, "end": 10.6},
        ]},
    ]}
    words = words_in_range(transcript, 5.0, 10.0)
    assert [w["word"] for w in words] == ["the", "best", "moment", "ever"]
    assert words[0]["start"] == 0.5  # 5.5 shifted by clip start
    assert words[-1]["end"] == 5.0   # 10.6 clipped to range end
    assert words_in_range(transcript, 20, 30) == []


@pytest.fixture()
def no_render_dispatch(monkeypatch):
    dispatched = []
    import app.pipeline.tasks as pt

    class FakeTask:
        id = "fake-celery-id"

    monkeypatch.setattr(pt.run_pipeline, "delay", lambda jid: dispatched.append(jid) or FakeTask())
    return dispatched


def _insert_asset(user_id, **overrides):
    from uuid import UUID

    from app.database import AsyncSessionLocal
    from app.models.asset import Asset

    fields = dict(
        user_id=UUID(str(user_id)),
        filename="podcast.mp4",
        kind="video",
        path="C:/nonexistent/podcast.mp4",
        duration=60.0,
        status="ready",
        transcript={"segments": [{"start": 0, "end": 60, "text": "great content", "words": [
            {"word": "great", "start": 10.0, "end": 10.5},
            {"word": "content", "start": 10.7, "end": 11.4},
        ]}]},
        highlights=[{"start": 8.0, "end": 30.0, "title": "Great moment", "reason": "hook"}],
    )
    fields.update(overrides)

    async def insert():
        async with AsyncSessionLocal() as db:
            asset = Asset(**fields)
            db.add(asset)
            await db.commit()
            return str(asset.id)

    return asyncio.run(insert())


def test_create_clip_renders_and_deducts(client, auth_headers, no_render_dispatch):
    me = client.get("/api/auth/me", headers=auth_headers).json()
    asset_id = _insert_asset(me["id"])

    resp = client.post(
        f"/api/media-assets/{asset_id}/clips",
        headers=auth_headers,
        json={"start": 8.0, "end": 30.0, "title": "Great moment"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "queued"
    assert no_render_dispatch  # worker job enqueued after commit

    video = client.get(f"/api/videos/{body['video_id']}", headers=auth_headers).json()
    assert video["output_type"] == "clip"
    assert video["status"] == "rendering"
    assert video["title"] == "Great moment"

    after = client.get("/api/auth/me", headers=auth_headers).json()
    assert after["credit_balance"] == me["credit_balance"] - 1


def test_create_clip_validations(client, auth_headers, no_render_dispatch):
    me = client.get("/api/auth/me", headers=auth_headers).json()

    processing = _insert_asset(me["id"], status="processing")
    resp = client.post(f"/api/media-assets/{processing}/clips", headers=auth_headers,
                       json={"start": 0, "end": 20})
    assert resp.status_code == 422 and "analyzed" in resp.json()["detail"]

    audio = _insert_asset(me["id"], kind="audio", filename="ep.mp3")
    resp = client.post(f"/api/media-assets/{audio}/clips", headers=auth_headers,
                       json={"start": 0, "end": 20})
    assert resp.status_code == 422 and "Audio" in resp.json()["detail"]

    ready = _insert_asset(me["id"])
    for start, end in [(10, 12), (0, 95), (30, 20), (-5, 20), (70, 80)]:
        resp = client.post(f"/api/media-assets/{ready}/clips", headers=auth_headers,
                           json={"start": start, "end": end})
        assert resp.status_code == 422, f"({start},{end}) should be rejected"

    assert no_render_dispatch == []  # nothing enqueued on any failure


def test_create_clip_requires_credits(client, auth_headers, no_render_dispatch):
    from sqlalchemy import update

    from app.database import AsyncSessionLocal
    from app.models.user import User

    me = client.get("/api/auth/me", headers=auth_headers).json()
    asset_id = _insert_asset(me["id"])

    async def set_credits(value):
        async with AsyncSessionLocal() as db:
            await db.execute(update(User).values(credit_balance=value))
            await db.commit()

    asyncio.run(set_credits(0))
    try:
        resp = client.post(f"/api/media-assets/{asset_id}/clips", headers=auth_headers,
                           json={"start": 8, "end": 30})
        assert resp.status_code == 402
        assert no_render_dispatch == []
    finally:
        asyncio.run(set_credits(10))


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
