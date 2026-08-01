"""Integration test: Redis pub/sub → authenticated WebSocket (needs local Redis)."""
import asyncio
import json
import threading
import time

import pytest
from starlette.websockets import WebSocketDisconnect

try:
    from app.services.progress import _sync_client, publish_progress

    _sync_client.ping()
    REDIS_AVAILABLE = True
except Exception:
    REDIS_AVAILABLE = False

pytestmark = pytest.mark.skipif(not REDIS_AVAILABLE, reason="local Redis not available")


def _make_job_for_token(auth_headers):
    """Create a video+job row owned by the authenticated test user."""
    from sqlalchemy import select

    from app.core.security import decode_access_token
    from app.database import AsyncSessionLocal
    from app.models.pipeline_job import PipelineJob
    from app.models.user import User
    from uuid import UUID

    token = auth_headers["Authorization"].split()[1]
    user_id = UUID(decode_access_token(token))

    async def create():
        async with AsyncSessionLocal() as db:
            from app.models.video import Video

            video = Video(user_id=user_id, status="script_ready", title="ws test")
            db.add(video)
            await db.flush()
            job = PipelineJob(video_id=video.id, user_id=user_id, status="queued")
            db.add(job)
            await db.commit()
            return str(job.id)

    return asyncio.run(create()), token


def test_ws_requires_token(client, auth_headers):
    job_id, _ = _make_job_for_token(auth_headers)
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect(f"/ws/pipeline/{job_id}"):
            pass
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect(f"/ws/pipeline/{job_id}?token=garbage"):
            pass


def test_ws_rejects_foreign_job(client, auth_headers):
    _, token = _make_job_for_token(auth_headers)
    # random UUID that is not a job of this user
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect(
            f"/ws/pipeline/00000000-0000-0000-0000-00000000abcd?token={token}"
        ):
            pass


def test_worker_progress_reaches_authenticated_websocket(client, auth_headers):
    job_id, token = _make_job_for_token(auth_headers)

    def publish_after_delay():
        time.sleep(0.5)
        publish_progress(job_id, status="running", stage="audio", percent=30)
        publish_progress(job_id, status="completed", stage="completed", percent=100)

    thread = threading.Thread(target=publish_after_delay)
    with client.websocket_connect(f"/ws/pipeline/{job_id}?token={token}") as ws:
        thread.start()
        first = json.loads(ws.receive_text())
        second = json.loads(ws.receive_text())

    thread.join()
    assert first["status"] == "running" and first["progress"] == 30
    assert second["status"] == "completed" and second["progress"] == 100
