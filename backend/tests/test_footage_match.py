"""Auto-match: footage transcripts pinned to matching script scenes."""
import asyncio

import pytest
from sqlalchemy import select

from app.services.footage_match import match_segments


def _footage(asset_id="a1", chunks=None):
    return [{
        "id": asset_id,
        "transcript": {"language": "en", "segments": chunks or [
            {"start": 0.0, "end": 4.0, "text": "the indian government is renting out gpus"},
            {"start": 4.0, "end": 9.0, "text": "startups and researchers can book compute time today"},
            {"start": 9.0, "end": 14.0, "text": "a completely unrelated sentence about cooking pasta"},
        ]},
    }]


def test_match_pins_best_window():
    segments = [
        {"text": "The government is renting out GPUs for a dollar", "visual_prompt": "x", "duration_estimate": 4.0},
        {"text": "Something about deep sea fish and coral reefs", "visual_prompt": "y", "duration_estimate": 4.0},
    ]
    out, matched = match_segments(segments, _footage())
    assert matched == 1
    assert out[0]["asset_id"] == "a1"
    assert out[0]["asset_start"] == 0.0
    assert "asset_id" not in out[1] or out[1].get("asset_id") is None


def test_match_respects_existing_pins():
    segments = [
        {"text": "government renting out gpus for startups", "media_id": 123, "media_thumb": "t"},
        {"text": "government renting gpus researchers compute", "visual_prompt": ""},
    ]
    out, matched = match_segments(segments, _footage())
    assert out[0]["media_id"] == 123 and not out[0].get("asset_id")
    assert matched == 1
    assert out[1]["asset_id"] == "a1"


def test_no_weak_matches():
    segments = [{"text": "totally different topic entirely about gardening tulips", "visual_prompt": ""}]
    out, matched = match_segments(segments, _footage())
    assert matched == 0
    assert not out[0].get("asset_id")


def test_two_segments_dont_share_one_moment():
    segments = [
        {"text": "government renting gpus startups compute", "visual_prompt": ""},
        {"text": "government renting gpus startups compute", "visual_prompt": ""},
    ]
    out, matched = match_segments(segments, _footage())
    starts = [s.get("asset_start") for s in out if s.get("asset_id")]
    assert len(starts) == len(set(starts))


@pytest.fixture()
def capture_generate(monkeypatch):
    async def fake_generate(topic, **kwargs):
        return {
            "title": "t", "description": "d", "tags": [],
            "segments": [
                {"text": "The government is renting out GPUs to startups", "visual_prompt": "x", "duration_estimate": 3.0},
                {"text": "Researchers can book compute time starting today", "visual_prompt": "y", "duration_estimate": 3.0},
            ],
            "total_duration": 6.0,
        }

    monkeypatch.setattr("app.routers.scripts.script_gen.generate_script", fake_generate)


def _insert_ready_asset(email="creator@example.com"):
    from app.database import AsyncSessionLocal
    from app.models.asset import Asset
    from app.models.user import User

    async def _run():
        async with AsyncSessionLocal() as db:
            user = (await db.execute(select(User).where(User.email == email))).scalar_one()
            asset = Asset(
                user_id=user.id, filename="myvideo.mp4", kind="video", path="x.mp4",
                status="ready", duration=20.0,
                transcript={"language": "en", "segments": [
                    {"start": 0.0, "end": 5.0, "text": "the government is renting out gpus to startups",
                     "words": [{"word": "the", "start": 0.0, "end": 0.2}]},
                    {"start": 5.0, "end": 10.0, "text": "researchers can book compute time on the portal today",
                     "words": [{"word": "researchers", "start": 5.0, "end": 5.5}]},
                ]},
            )
            db.add(asset)
            await db.commit()
            return str(asset.id)

    return asyncio.run(_run())


def test_match_endpoint(client, auth_headers, capture_generate):
    resp = client.post("/api/scripts/generate", headers=auth_headers,
                       json={"custom_prompt": "gpu subsidies in india explained"})
    assert resp.status_code == 200
    video_id = resp.json()["video_id"]

    asset_id = _insert_ready_asset()
    resp = client.post(f"/api/scripts/{video_id}/match-footage", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["matched"] == 2
    assert body["segments"][0]["asset_id"] == asset_id
    assert body["segments"][1]["asset_id"] == asset_id
    assert body["segments"][0]["asset_start"] != body["segments"][1]["asset_start"]

    # persisted
    script = client.get(f"/api/scripts/{video_id}", headers=auth_headers).json()
    assert script["segments"][0]["asset_id"] == asset_id

    # cleanup so other tests see a pristine asset list
    client.delete(f"/api/media-assets/{asset_id}", headers=auth_headers)
