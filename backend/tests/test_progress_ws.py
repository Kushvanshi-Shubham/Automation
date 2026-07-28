"""Integration test: Redis pub/sub → WebSocket forwarding (requires local Redis)."""
import json
import threading
import time

import pytest

try:
    from app.services.progress import _sync_client, publish_progress

    _sync_client.ping()
    REDIS_AVAILABLE = True
except Exception:
    REDIS_AVAILABLE = False

pytestmark = pytest.mark.skipif(not REDIS_AVAILABLE, reason="local Redis not available")


def test_worker_progress_reaches_websocket(client):
    job_id = "test-job-ws-1"

    def publish_after_delay():
        # Give the WS subscriber a moment to attach before publishing.
        time.sleep(0.5)
        publish_progress(job_id, status="running", stage="audio", percent=30)
        publish_progress(job_id, status="completed", stage="completed", percent=100)

    thread = threading.Thread(target=publish_after_delay)
    with client.websocket_connect(f"/ws/pipeline/{job_id}") as ws:
        thread.start()
        first = json.loads(ws.receive_text())
        second = json.loads(ws.receive_text())

    thread.join()
    assert first == {"job_id": job_id, "status": "running", "stage": "audio", "progress": 30, "error": None}
    assert second["status"] == "completed"
    assert second["progress"] == 100
