import asyncio

import httpx
import pytest


def test_security_headers_on_responses(client):
    resp = client.get("/api/health")
    assert resp.headers["x-content-type-options"] == "nosniff"
    assert resp.headers["x-frame-options"] == "DENY"
    assert "strict-origin" in resp.headers["referrer-policy"]


def test_retry_helper_retries_transient():
    from app.core.retry import with_retries

    calls = {"n": 0}

    async def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            raise RuntimeError("503 UNAVAILABLE — model overloaded")
        return "ok"

    out = asyncio.run(with_retries(flaky, attempts=3, base_delay=0.01))
    assert out == "ok"
    assert calls["n"] == 3


def test_retry_helper_gives_up_on_permanent():
    from app.core.retry import with_retries

    calls = {"n": 0}

    async def broken():
        calls["n"] += 1
        raise ValueError("invalid api key")  # not transient -> no retry

    with pytest.raises(ValueError):
        asyncio.run(with_retries(broken, attempts=3, base_delay=0.01))
    assert calls["n"] == 1


def test_retry_helper_exhausts_attempts():
    from app.core.retry import with_retries

    calls = {"n": 0}

    async def always_down():
        calls["n"] += 1
        raise httpx.ConnectError("connection refused")

    with pytest.raises(httpx.ConnectError):
        asyncio.run(with_retries(always_down, attempts=3, base_delay=0.01))
    assert calls["n"] == 3


def test_rate_limit_blocks_after_threshold(client, auth_headers, monkeypatch):
    """With limits ON and a tiny threshold, the third call in a window is 429."""
    from app.config import settings
    from app.middleware import rate_limit as rl

    monkeypatch.setattr(settings, "RATE_LIMITS_ENABLED", True)
    monkeypatch.setitem(rl.LIMITS, "topics_refresh", (2, 60))

    # Clean slate for this user's counter
    import redis as redis_sync

    from app.middleware.auth import get_current_user  # noqa: F401 (documented dependency)

    r = redis_sync.Redis.from_url(settings.REDIS_URL, decode_responses=True, protocol=2)
    for key in r.scan_iter("rl:topics_refresh:*"):
        r.delete(key)

    async def fake_harvest(db):
        return {"added": 0}

    monkeypatch.setattr("app.routers.topics.harvest_topics", fake_harvest)

    assert client.post("/api/topics/refresh", headers=auth_headers).status_code == 200
    assert client.post("/api/topics/refresh", headers=auth_headers).status_code == 200
    resp = client.post("/api/topics/refresh", headers=auth_headers)
    assert resp.status_code == 429
    assert "retry-after" in resp.headers

    for key in r.scan_iter("rl:topics_refresh:*"):
        r.delete(key)


def test_magic_byte_sniffer():
    from app.routers.media import _looks_like_media

    assert _looks_like_media(b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00", ".mp4")
    assert _looks_like_media(b"\x1a\x45\xdf\xa3" + b"\x00" * 12, ".webm")
    assert _looks_like_media(b"ID3\x04\x00\x00\x00\x00\x00\x00\x00\x00", ".mp3")
    assert _looks_like_media(b"\xff\xfb\x90\x00" + b"\x00" * 12, ".mp3")
    assert _looks_like_media(b"RIFF\x24\x08\x00\x00WAVEfmt ", ".wav")
    assert not _looks_like_media(b"#!/bin/sh\nrm -rf /", ".mp4")
    assert not _looks_like_media(b"MZ\x90\x00" + b"\x00" * 12, ".mp3")  # PE executable
    assert not _looks_like_media(b"", ".mp4")


def test_cost_tracking_counters():
    from app.services import costs

    month = "203307"  # synthetic month so real counters stay untouched
    key = costs._month_key("pexels_clip", month)
    import redis as redis_sync

    from app.config import settings

    r = redis_sync.Redis.from_url(settings.REDIS_URL, decode_responses=True, protocol=2)
    r.delete(key)
    try:
        r.incrbyfloat(key, 3)
        usage = costs.month_usage(month)
        assert usage["pexels_clip"] == 3.0
        assert usage["llm:gemini"] == 0.0
        est = costs.estimated_cost_usd({"llm:openai": 10, "pexels_clip": 3})
        assert est["llm:openai"] == 0.2   # 10 * $0.02
        assert est["pexels_clip"] == 0.0  # free API
        assert est["total"] == 0.2
    finally:
        r.delete(key)


def test_economics_endpoint_owner_gated(client, auth_headers, monkeypatch):
    from app.config import settings

    resp = client.get("/api/billing/economics", headers=auth_headers)
    assert resp.status_code == 403  # not an owner

    monkeypatch.setattr(settings, "ADMIN_EMAILS", ["creator@example.com"])
    resp = client.get("/api/billing/economics", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "credits" in body and "estimated_cost_usd" in body
    assert body["implied_revenue_usd"] == body["credits"]["net_spent"] * body["credit_price_usd"]


def test_pipeline_active_lists_running_jobs(client, auth_headers, monkeypatch):
    """The RAIL conveyor endpoint: in-flight jobs only, with progress."""
    async def fake_generate(topic, **kwargs):
        return {"title": "Rail test", "description": "d", "tags": [],
                "segments": [{"text": "hello world", "visual_prompt": "x", "duration_estimate": 2.0}],
                "total_duration": 2.0}

    monkeypatch.setattr("app.routers.scripts.script_gen.generate_script", fake_generate)
    import app.pipeline.tasks as pt

    class FakeTask:
        id = "fake"

    monkeypatch.setattr(pt.run_pipeline, "delay", lambda jid: FakeTask())

    vid = client.post("/api/scripts/generate", headers=auth_headers,
                      json={"custom_prompt": "rail conveyor active test"}).json()["video_id"]
    assert client.post("/api/pipeline/start", headers=auth_headers,
                       json={"video_id": vid, "visual_engine": "pexels"}).status_code == 200

    items = client.get("/api/pipeline/active", headers=auth_headers).json()["items"]
    mine = [i for i in items if i["video_id"] == vid]
    assert len(mine) == 1
    assert mine[0]["status"] == "queued"
    assert mine[0]["progress"]["percent"] == 0

    # video response now carries series_id (null here) for the reel tag
    v = client.get(f"/api/videos/{vid}", headers=auth_headers).json()
    assert "series_id" in v and v["series_id"] is None
