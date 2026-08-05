"""A creator must never be stuck with a spent credit and a frozen bar:
cancel returns it, and the reaper cleans up jobs nobody finished."""
import asyncio
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select


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
    """Renders enqueue but nothing consumes them — the deployed situation."""
    class _Task:
        id = "fake-task-id"

    monkeypatch.setattr("app.pipeline.tasks.run_pipeline.delay", lambda *_a, **_k: _Task())


def _start_render(client, auth_headers):
    video_id = client.post("/api/scripts/generate", headers=auth_headers,
                           json={"custom_prompt": "a story about stuck renders"}).json()["video_id"]
    resp = client.post("/api/pipeline/start", headers=auth_headers,
                       json={"video_id": video_id, "visual_engine": "pexels"})
    assert resp.status_code == 200
    return video_id, resp.json()["job_id"]


def _credits(client, auth_headers):
    return client.get("/api/billing/credits", headers=auth_headers).json()["balance"]


def test_cancel_refunds_and_frees_the_video(client, auth_headers, mock_generate, no_worker):
    before = _credits(client, auth_headers)
    video_id, job_id = _start_render(client, auth_headers)
    assert _credits(client, auth_headers) == before - 1

    resp = client.post(f"/api/pipeline/{job_id}/cancel", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["refunded_credits"] == 1
    assert _credits(client, auth_headers) == before

    # The script survives and can be rendered again.
    video = client.get(f"/api/videos/{video_id}", headers=auth_headers).json()
    assert video["status"] == "script_ready"
    again = client.post("/api/pipeline/start", headers=auth_headers,
                        json={"video_id": video_id, "visual_engine": "pexels"})
    assert again.status_code == 200
    client.post(f"/api/pipeline/{again.json()['job_id']}/cancel", headers=auth_headers)


def test_cancel_is_owner_only_and_not_for_finished_jobs(client, auth_headers, mock_generate, no_worker):
    _, job_id = _start_render(client, auth_headers)
    assert client.post("/api/pipeline/00000000-0000-0000-0000-000000000000/cancel",
                       headers=auth_headers).status_code == 404

    from app.database import AsyncSessionLocal
    from app.models.pipeline_job import PipelineJob

    async def _complete():
        async with AsyncSessionLocal() as db:
            job = await db.get(PipelineJob, __import__("uuid").UUID(job_id))
            job.status = "completed"
            await db.commit()

    asyncio.run(_complete())
    resp = client.post(f"/api/pipeline/{job_id}/cancel", headers=auth_headers)
    assert resp.status_code == 422
    assert "already finished" in resp.json()["detail"]


def test_reaper_refunds_jobs_no_worker_finished(client, auth_headers, mock_generate, no_worker):
    from app.database import AsyncSessionLocal
    from app.models.pipeline_job import PipelineJob
    from app.models.video import Video
    from app.pipeline.reaper import _run

    before = _credits(client, auth_headers)
    video_id, job_id = _start_render(client, auth_headers)

    # Backdate the video so the job looks abandoned (never picked up).
    async def _age():
        async with AsyncSessionLocal() as db:
            video = await db.get(Video, __import__("uuid").UUID(video_id))
            video.created_at = datetime.now(timezone.utc) - timedelta(hours=2)
            await db.commit()

    asyncio.run(_age())
    result = asyncio.run(_run())
    assert result["reaped"] >= 1
    assert _credits(client, auth_headers) == before

    async def _check():
        async with AsyncSessionLocal() as db:
            job = (await db.execute(
                select(PipelineJob).where(PipelineJob.id == __import__("uuid").UUID(job_id))
            )).scalar_one()
            video = await db.get(Video, __import__("uuid").UUID(video_id))
            return job.status, video.status

    job_status, video_status = asyncio.run(_check())
    assert job_status == "failed"
    assert video_status == "script_ready"


def test_reaper_leaves_fresh_jobs_alone(client, auth_headers, mock_generate, no_worker):
    from app.pipeline.reaper import _run

    _, job_id = _start_render(client, auth_headers)
    assert asyncio.run(_run())["reaped"] == 0
    status = client.get(f"/api/pipeline/{job_id}", headers=auth_headers).json()["status"]
    assert status == "queued"
    client.post(f"/api/pipeline/{job_id}/cancel", headers=auth_headers)
