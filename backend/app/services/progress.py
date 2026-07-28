"""Pipeline progress events over Redis pub/sub.

Celery workers run in separate processes/containers, so they can never reach
the API's in-memory WebSocket connections. Workers publish progress here;
the API's WebSocket endpoint subscribes and forwards to browsers.
"""
import json
from typing import Any

import redis as redis_sync
import redis.asyncio as redis_async

from app.config import settings

CHANNEL_PREFIX = "pipeline:progress:"

# Sync client for Celery workers (module-level pool, lazy connect).
# protocol=2: keep RESP2 for compatibility with older Redis servers (dev uses
# the 5.0 Windows port, which has no HELLO command).
_sync_client = redis_sync.Redis.from_url(settings.REDIS_URL, decode_responses=True, protocol=2)


def channel_for(job_id: str) -> str:
    return f"{CHANNEL_PREFIX}{job_id}"


def publish_progress(job_id: str, *, status: str, stage: str, percent: float, error: str | None = None) -> None:
    """Called from Celery tasks (sync context)."""
    payload: dict[str, Any] = {
        "job_id": job_id,
        "status": status,
        "stage": stage,
        "progress": percent,
        "error": error,
    }
    _sync_client.publish(channel_for(job_id), json.dumps(payload))


def async_redis() -> redis_async.Redis:
    """Fresh async client for API-side subscribers."""
    return redis_async.from_url(settings.REDIS_URL, decode_responses=True, protocol=2)
