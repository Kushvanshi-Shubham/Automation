"""Montage: several highlights from one upload joined into a single reel.

A clip render is one moment. This is the reel — the half of the gaming
claim that did not exist. Validation matters more than usual here because
the creator is spending one credit per clip, so a rejected request must
say what to fix rather than take the money.
"""
import asyncio

import pytest


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
        filename="gameplay.mp4",
        kind="video",
        path="C:/nonexistent/gameplay.mp4",
        duration=300.0,
        status="ready",
        transcript={"segments": []},   # gameplay: nothing said
        highlights=[
            {"start": 10.0, "end": 20.0, "title": "Loud moment", "reason": "3x louder", "source": "sound"},
            {"start": 60.0, "end": 70.0, "title": "Loud moment", "reason": "2x louder", "source": "sound"},
        ],
    )
    fields.update(overrides)

    async def insert():
        async with AsyncSessionLocal() as db:
            asset = Asset(**fields)
            db.add(asset)
            await db.commit()
            return str(asset.id)

    return asyncio.run(insert())


def _set_credits(value: int):
    """Every test here shares one user, and a montage costs a credit per clip,
    so without a top-up the later tests fail on 402 rather than on the thing
    they are checking."""
    from sqlalchemy import update

    from app.database import AsyncSessionLocal
    from app.models.user import User

    async def run():
        async with AsyncSessionLocal() as db:
            await db.execute(update(User).values(credit_balance=value))
            await db.commit()

    asyncio.run(run())


def _montage(client, auth_headers, asset_id, **body):
    payload = {"ranges": [{"start": 10.0, "end": 20.0}, {"start": 60.0, "end": 70.0}]}
    payload.update(body)
    _set_credits(50)
    return client.post(f"/api/media-assets/{asset_id}/montage", headers=auth_headers, json=payload)


def test_montage_queues_and_costs_one_credit_per_clip(client, auth_headers, no_render_dispatch):
    me = client.get("/api/auth/me", headers=auth_headers).json()
    asset_id = _insert_asset(me["id"])
    before = 50  # _montage tops up to this before posting

    resp = _montage(client, auth_headers, asset_id,
                    ranges=[{"start": 10.0, "end": 20.0},
                            {"start": 60.0, "end": 70.0},
                            {"start": 100.0, "end": 110.0}])
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "queued"
    # Three clips is three trims and three caption passes, not one job.
    assert body["credits_used"] == 3
    assert no_render_dispatch, "worker job must be enqueued after commit"

    after = client.get("/api/billing/credits", headers=auth_headers).json()["balance"]
    assert before - after == 3


def test_ranges_are_stored_in_source_order(client, auth_headers, no_render_dispatch):
    """The reel should follow the recording, not the order boxes were ticked."""
    from uuid import UUID

    from app.database import AsyncSessionLocal
    from app.models.video import Video

    me = client.get("/api/auth/me", headers=auth_headers).json()
    asset_id = _insert_asset(me["id"])
    video_id = _montage(client, auth_headers, asset_id,
                        ranges=[{"start": 100.0, "end": 110.0},
                                {"start": 10.0, "end": 20.0}]).json()["video_id"]

    async def read():
        async with AsyncSessionLocal() as db:
            return await db.get(Video, UUID(video_id))

    video = asyncio.run(read())
    assert video.output_type == "montage"
    starts = [r["start"] for r in video.script_data["montage"]["ranges"]]
    assert starts == [10.0, 100.0]


def test_one_moment_is_a_clip_not_a_montage(client, auth_headers, no_render_dispatch):
    me = client.get("/api/auth/me", headers=auth_headers).json()
    asset_id = _insert_asset(me["id"])
    resp = _montage(client, auth_headers, asset_id, ranges=[{"start": 10.0, "end": 20.0}])
    assert resp.status_code == 422
    assert "pick another one" in resp.json()["detail"]


def test_too_many_moments_is_rejected(client, auth_headers, no_render_dispatch):
    me = client.get("/api/auth/me", headers=auth_headers).json()
    asset_id = _insert_asset(me["id"])
    resp = _montage(client, auth_headers, asset_id,
                    ranges=[{"start": float(i * 20), "end": float(i * 20 + 6)} for i in range(7)])
    assert resp.status_code == 422
    assert "drop a few" in resp.json()["detail"]


def test_overlapping_moments_are_rejected(client, auth_headers, no_render_dispatch):
    """Overlap would play the same footage twice in a row."""
    me = client.get("/api/auth/me", headers=auth_headers).json()
    asset_id = _insert_asset(me["id"])
    resp = _montage(client, auth_headers, asset_id,
                    ranges=[{"start": 10.0, "end": 30.0}, {"start": 25.0, "end": 40.0}])
    assert resp.status_code == 422
    assert "overlap" in resp.json()["detail"]


def test_a_too_short_moment_is_rejected(client, auth_headers, no_render_dispatch):
    me = client.get("/api/auth/me", headers=auth_headers).json()
    asset_id = _insert_asset(me["id"])
    resp = _montage(client, auth_headers, asset_id,
                    ranges=[{"start": 10.0, "end": 12.0}, {"start": 60.0, "end": 70.0}])
    assert resp.status_code == 422
    assert "at least" in resp.json()["detail"]


def test_a_montage_longer_than_the_ceiling_is_rejected(client, auth_headers, no_render_dispatch):
    me = client.get("/api/auth/me", headers=auth_headers).json()
    asset_id = _insert_asset(me["id"], duration=1000.0)
    resp = _montage(client, auth_headers, asset_id,
                    ranges=[{"start": float(i * 100), "end": float(i * 100 + 40)} for i in range(4)])
    assert resp.status_code == 422
    assert "keep it under" in resp.json()["detail"]


def test_range_is_clamped_to_the_end_of_the_video(client, auth_headers, no_render_dispatch):
    """A suggestion running past the file must not reach ffmpeg as-is."""
    from uuid import UUID

    from app.database import AsyncSessionLocal
    from app.models.video import Video

    me = client.get("/api/auth/me", headers=auth_headers).json()
    asset_id = _insert_asset(me["id"], duration=65.0)
    video_id = _montage(client, auth_headers, asset_id,
                        ranges=[{"start": 10.0, "end": 20.0},
                                {"start": 55.0, "end": 90.0}]).json()["video_id"]

    async def read():
        async with AsyncSessionLocal() as db:
            return await db.get(Video, UUID(video_id))

    ranges = asyncio.run(read()).script_data["montage"]["ranges"]
    assert ranges[-1]["end"] == 65.0


def test_unknown_music_mood_is_rejected(client, auth_headers, no_render_dispatch):
    me = client.get("/api/auth/me", headers=auth_headers).json()
    asset_id = _insert_asset(me["id"])
    resp = _montage(client, auth_headers, asset_id, music_mood="party")
    assert resp.status_code == 422
    assert "music mood" in resp.json()["detail"].lower()


def test_music_mood_is_saved_for_the_renderer(client, auth_headers, no_render_dispatch):
    from uuid import UUID

    from app.database import AsyncSessionLocal
    from app.models.video import Video

    me = client.get("/api/auth/me", headers=auth_headers).json()
    asset_id = _insert_asset(me["id"])
    video_id = _montage(client, auth_headers, asset_id, music_mood="energetic").json()["video_id"]

    async def read():
        async with AsyncSessionLocal() as db:
            return await db.get(Video, UUID(video_id))

    assert asyncio.run(read()).script_data["music_mood"] == "energetic"


def test_audio_only_upload_cannot_be_montaged(client, auth_headers, no_render_dispatch):
    me = client.get("/api/auth/me", headers=auth_headers).json()
    asset_id = _insert_asset(me["id"], kind="audio", filename="voice.mp3")
    resp = _montage(client, auth_headers, asset_id)
    assert resp.status_code == 422


def test_another_users_asset_is_not_found(client, auth_headers, no_render_dispatch):
    import uuid as uuid_mod

    asset_id = _insert_asset(uuid_mod.uuid4())
    resp = _montage(client, auth_headers, asset_id)
    assert resp.status_code == 404


def test_every_completion_path_publishes_through_storage():
    """A rendered file must reach the browser, not just the worker's disk.

    This replaces a test that asserted a STRING was present in runner.py — it
    passed happily while the montage and clip branches wrote a bare
    "/media/<id>/final.mp4" into video_url. In the cloud the API and the worker
    are separate containers with no shared volume, so that URL 404s: the
    feature was broken in production and fully green in CI.

    _store_media is the only function that uploads to object storage, so the
    invariant is that no completion path may set video_url without it.
    """
    import re

    source = open("app/pipeline/runner.py", encoding="utf-8").read()
    assigns = re.findall(r"video(?:_row)?\.video_url\s*=\s*(.+)", source)
    assert assigns, "video_url is never assigned — did the runner move?"
    for expr in assigns:
        assert "/media/" not in expr, (
            f"video_url assigned a bare local path ({expr.strip()}) — it must be "
            "the return value of _store_media, or the render 404s in the cloud"
        )


def test_runner_guards_a_one_clip_montage():
    """The render branch defends itself; the endpoint is not the only gate."""
    import asyncio
    import inspect
    from pathlib import Path

    from app.pipeline import runner

    # Reaches the guard before touching the database or ffmpeg.
    video = type("V", (), {"script_data": {"montage": {"asset_id": "x", "ranges": [{"start": 0, "end": 9}]}}, "id": None})()
    with pytest.raises(RuntimeError, match="at least 2 clips"):
        asyncio.run(runner._run_montage("k", None, video, Path("."), Path(".")))
    # And the guard is genuinely in the branch, not inherited from a caller.
    assert "at least 2 clips" in inspect.getsource(runner._run_montage)
