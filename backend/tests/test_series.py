import asyncio
from datetime import datetime, timedelta, timezone

import pytest


@pytest.fixture(autouse=True)
def cleanup_series():
    yield
    from sqlalchemy import delete, update

    from app.database import AsyncSessionLocal
    from app.models.series import Series
    from app.models.video import Video

    async def wipe():
        async with AsyncSessionLocal() as db:
            await db.execute(update(Video).values(series_id=None))
            await db.execute(delete(Series))
            await db.commit()

    asyncio.run(wipe())


def test_series_crud(client, auth_headers):
    resp = client.post(
        "/api/series",
        headers=auth_headers,
        json={"name": "Daily Gaming Facts", "category": "gaming", "interval_hours": 24},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["is_active"] is True
    assert body["next_run_at"] is not None
    sid = body["id"]

    listed = client.get("/api/series", headers=auth_headers).json()
    assert any(s["id"] == sid for s in listed)

    paused = client.patch(f"/api/series/{sid}", headers=auth_headers, json={"is_active": False}).json()
    assert paused["is_active"] is False

    assert client.delete(f"/api/series/{sid}", headers=auth_headers).status_code == 204


def test_series_validation(client, auth_headers):
    assert client.post("/api/series", headers=auth_headers,
                       json={"name": "x2", "interval_hours": 7}).status_code == 422
    assert client.post("/api/series", headers=auth_headers,
                       json={"name": "x2", "category": "astrology"}).status_code == 422
    assert client.post("/api/series", headers=auth_headers,
                       json={"name": "x2", "output_type": "image"}).status_code == 422
    assert client.post("/api/series", headers=auth_headers,
                       json={"name": "x2", "auto_publish": True}).status_code == 422  # no channel


def test_series_active_limit(client, auth_headers):
    for i in range(3):
        assert client.post("/api/series", headers=auth_headers,
                           json={"name": f"Series {i}"}).status_code == 200
    resp = client.post("/api/series", headers=auth_headers, json={"name": "One too many"})
    assert resp.status_code == 422
    assert "Maximum" in resp.json()["detail"]


def test_tick_dispatches_due_and_advances_schedule(client, auth_headers, monkeypatch):
    created = client.post("/api/series", headers=auth_headers, json={"name": "Tick test"}).json()

    dispatched = []
    monkeypatch.setattr(
        "app.pipeline.series_tasks.run_series_once",
        type("T", (), {"delay": staticmethod(lambda sid: dispatched.append(sid))}),
    )

    from app.pipeline.series_tasks import _tick

    n = asyncio.run(_tick())
    assert n >= 1
    assert created["id"] in dispatched

    # second tick immediately: nothing due anymore (next_run advanced)
    dispatched.clear()
    asyncio.run(_tick())
    assert created["id"] not in dispatched


def test_run_one_skips_without_credits(client, auth_headers, monkeypatch):
    created = client.post("/api/series", headers=auth_headers, json={"name": "Broke test"}).json()

    from sqlalchemy import update

    from app.database import AsyncSessionLocal
    from app.models.user import User
    from app.pipeline.series_tasks import _run_one

    async def drain_credits(value):
        async with AsyncSessionLocal() as db:
            await db.execute(update(User).values(credit_balance=value))
            await db.commit()

    asyncio.run(drain_credits(0))
    result = asyncio.run(_run_one(created["id"]))
    assert result == {"skipped": "no_credits"}
    asyncio.run(drain_credits(10))

    detail = client.get("/api/series", headers=auth_headers).json()
    row = next(s for s in detail if s["id"] == created["id"])
    assert "credits" in (row["last_error"] or "")


def test_run_one_creates_video_and_deducts(client, auth_headers, monkeypatch):
    created = client.post(
        "/api/series", headers=auth_headers,
        json={"name": "Theme run", "topic_prompt": "daily chess puzzles explained", "output_type": "visual"},
    ).json()

    async def fake_generate(topic, **kwargs):
        return {
            "title": "Chess puzzle of the day",
            "description": "d", "tags": ["chess"],
            "segments": [{"text": "White to move and win.", "visual_prompt": "chess board dramatic light", "duration_estimate": 3.0}],
            "total_duration": 3.0,
        }

    dispatched = {}
    monkeypatch.setattr("app.services.script_gen.generate_script", fake_generate)
    import app.pipeline.tasks as tasks_mod
    monkeypatch.setattr(
        tasks_mod.run_pipeline, "delay",
        lambda job_id: dispatched.setdefault("job", job_id),
    )

    before = client.get("/api/billing/credits", headers=auth_headers).json()["balance"]

    from app.pipeline.series_tasks import _run_one

    result = asyncio.run(_run_one(created["id"]))
    assert "video_id" in result
    assert dispatched.get("job")

    after = client.get("/api/billing/credits", headers=auth_headers).json()["balance"]
    assert after == before - 1

    video = client.get(f"/api/videos/{result['video_id']}", headers=auth_headers).json()
    assert video["title"] == "Chess puzzle of the day"
    assert video["output_type"] == "visual"


def test_series_format_validation(client, auth_headers):
    resp = client.post("/api/series", headers=auth_headers,
                       json={"name": "Bad fmt", "format": "hollywood"})
    assert resp.status_code == 422

    # image carousels can't auto-publish to YouTube -> not series-able
    resp = client.post("/api/series", headers=auth_headers,
                       json={"name": "Carousel", "format": "image_carousel"})
    assert resp.status_code == 422

    resp = client.post("/api/series", headers=auth_headers,
                       json={"name": "Reddit night", "format": "reddit_story"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["format"] == "reddit_story"


def test_run_one_applies_format_recipe(client, auth_headers, monkeypatch):
    created = client.post(
        "/api/series", headers=auth_headers,
        json={"name": "Reddit stories daily", "topic_prompt": "wild roommate drama stories",
              "format": "reddit_story"},
    ).json()

    captured = {}

    async def fake_generate(topic, **kwargs):
        captured["topic"] = topic
        captured.update(kwargs)
        return {
            "title": "My roommate's secret",
            "description": "d", "tags": [],
            "segments": [{"text": "I never should have checked.", "visual_prompt": "x", "duration_estimate": 3.0}],
            "total_duration": 3.0,
        }

    monkeypatch.setattr("app.services.script_gen.generate_script", fake_generate)
    import app.pipeline.tasks as tasks_mod
    monkeypatch.setattr(tasks_mod.run_pipeline, "delay", lambda job_id: None)

    from app.pipeline.series_tasks import _run_one

    result = asyncio.run(_run_one(created["id"]))
    assert "video_id" in result
    # The format's recipe and style drive generation
    assert captured["style"] == "viral_story"
    assert "FIRST PERSON" in captured["custom_instructions"]

    video = client.get(f"/api/videos/{result['video_id']}", headers=auth_headers).json()
    assert video["output_type"] == "narrated"

    # Render defaults landed in script_data for the runner
    from uuid import UUID

    from app.database import AsyncSessionLocal
    from app.models.video import Video

    async def fetch():
        async with AsyncSessionLocal() as db:
            return (await db.get(Video, UUID(result["video_id"]))).script_data

    data = asyncio.run(fetch())
    assert data["format"] == "reddit_story"
    assert data["background_query"]
    assert data["music_mood"] == "calm"
