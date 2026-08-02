import asyncio

import pytest


@pytest.fixture(autouse=True)
def cleanup_renders():
    """This module runs alphabetically FIRST — it must leave the shared test
    user pristine (balance 3, only the signup-grant ledger row) for test_auth."""
    yield
    from sqlalchemy import delete, update

    from app.database import AsyncSessionLocal
    from app.models.credit import CreditLedger
    from app.models.pipeline_job import PipelineJob
    from app.models.user import User
    from app.models.video import Video

    async def wipe():
        async with AsyncSessionLocal() as db:
            await db.execute(delete(PipelineJob))
            await db.execute(delete(CreditLedger).where(CreditLedger.type == "video_debit"))
            await db.execute(delete(Video))
            await db.execute(update(User).values(credit_balance=3))
            await db.commit()

    asyncio.run(wipe())


def test_aspect_catalog(client, auth_headers):
    resp = client.get("/api/pipeline/aspect-ratios", headers=auth_headers)
    assert resp.status_code == 200
    items = {i["key"]: i for i in resp.json()["items"]}
    assert set(items) == {"9:16", "1:1", "16:9"}
    assert items["9:16"]["width"] == 1080 and items["9:16"]["height"] == 1920
    assert items["16:9"]["width"] == 1920 and items["16:9"]["height"] == 1080


@pytest.fixture()
def script_video(client, auth_headers, monkeypatch):
    async def fake_generate(topic, **kwargs):
        return {
            "title": "t", "description": "d", "tags": [],
            "segments": [{"text": "hello world", "visual_prompt": "x", "duration_estimate": 2.0}],
            "total_duration": 2.0,
        }

    monkeypatch.setattr("app.routers.scripts.script_gen.generate_script", fake_generate)
    return client.post(
        "/api/scripts/generate", headers=auth_headers,
        json={"custom_prompt": "aspect ratio test"},
    ).json()["video_id"]


def test_pipeline_rejects_unknown_aspect(client, auth_headers, script_video):
    resp = client.post(
        "/api/pipeline/start", headers=auth_headers,
        json={"video_id": script_video, "visual_engine": "pexels", "aspect_ratio": "4:3"},
    )
    assert resp.status_code == 422
    assert "aspect" in resp.json()["detail"].lower()


def test_pipeline_stores_aspect(client, auth_headers, script_video, monkeypatch):
    import app.pipeline.tasks as pt

    class FakeTask:
        id = "fake-celery-id"

    monkeypatch.setattr(pt.run_pipeline, "delay", lambda jid: FakeTask())
    resp = client.post(
        "/api/pipeline/start", headers=auth_headers,
        json={"video_id": script_video, "visual_engine": "pexels", "aspect_ratio": "16:9"},
    )
    assert resp.status_code == 200, resp.text
    video = client.get(f"/api/videos/{script_video}", headers=auth_headers).json()
    assert video["aspect_ratio"] == "16:9"


def test_write_ass_scales_to_play_res(tmp_path):
    from app.pipeline.captions import write_ass

    cues = [{"text": "hello world", "start": 0.0, "end": 1.0,
             "words": [{"word": "hello", "start": 0.0, "end": 0.5},
                       {"word": "world", "start": 0.5, "end": 1.0}]}]
    landscape = write_ass(cues, tmp_path / "l.ass", play_res=(1920, 1080)).read_text(encoding="utf-8")
    assert "PlayResX: 1920" in landscape and "PlayResY: 1080" in landscape
    # classic fontsize 88 tuned for 1920-high frame -> ~50 at 1080
    assert landscape.split("Style: Caption,Arial,")[1].startswith("50,")

    default = write_ass(cues, tmp_path / "p.ass").read_text(encoding="utf-8")
    assert "PlayResX: 1080" in default and "PlayResY: 1920" in default
    assert default.split("Style: Caption,Arial,")[1].startswith("88,")  # unscaled


def test_pick_file_respects_orientation():
    from app.pipeline.visuals.pexels import _pick_file

    video = {"video_files": [
        {"file_type": "video/mp4", "width": 1080, "height": 1920, "link": "p"},
        {"file_type": "video/mp4", "width": 1920, "height": 1080, "link": "l"},
    ]}
    assert _pick_file(video, 1080, 1920, "portrait")["link"] == "p"
    assert _pick_file(video, 1920, 1080, "landscape")["link"] == "l"
    # square target accepts either; picks the smallest covering 1080x1080
    assert _pick_file(video, 1080, 1080, "square") is not None
    # no orientation match -> falls back instead of failing the render
    portrait_only = {"video_files": [{"file_type": "video/mp4", "width": 1080, "height": 1920, "link": "p"}]}
    assert _pick_file(portrait_only, 1920, 1080, "landscape")["link"] == "p"
