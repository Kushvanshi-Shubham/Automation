"""Guards on the two lanes that spend real money without asking.

Both were found by audit, not by a user, and both leak silently — which is
why they get behaviour tests rather than a comment. A leak nobody notices is
worse than a crash.
"""
import asyncio
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select, update

from app.database import AsyncSessionLocal
from app.models.credit import CreditLedger
from app.models.user import User


@pytest.fixture(autouse=True)
def restore_the_user():
    before = _snapshot()
    yield
    if before:
        _set_user(**before)
    _clear_proof_rows()


def _snapshot():
    async def run():
        async with AsyncSessionLocal() as db:
            u = (await db.execute(select(User))).scalars().first()
            return None if u is None else {"credit_balance": u.credit_balance, "plan": u.plan}

    return asyncio.run(run())


def _set_user(**values):
    async def run():
        async with AsyncSessionLocal() as db:
            await db.execute(update(User).values(**values))
            await db.commit()

    asyncio.run(run())


def _clear_proof_rows():
    from sqlalchemy import delete

    async def run():
        async with AsyncSessionLocal() as db:
            await db.execute(delete(CreditLedger).where(CreditLedger.type == "proof_ai_image"))
            await db.commit()

    asyncio.run(run())


# ---- autopilot pricing -------------------------------------------------------

def test_autopilot_prices_ai_image_per_scene():
    """A flat price meant an unattended daily series rendered at a loss.

    ai_image bills per generated image, so a 7-scene episode is several times
    the cost of a stock-footage one. The studio already prices it that way;
    this makes the series agree instead of quietly undercharging.
    """
    from app.pipeline.series_tasks import _series_render_cost
    from app.services.credits import engine_credit_cost

    assert _series_render_cost("ai_image", 7) == engine_credit_cost("ai_image", scenes=7)
    assert _series_render_cost("ai_image", 7) > _series_render_cost("pexels", 7)


def test_autopilot_still_charges_at_least_one_credit():
    """The floor holds for the cheap lanes and for a missing engine."""
    from app.pipeline.series_tasks import SERIES_RENDER_COST, _series_render_cost

    assert _series_render_cost("pexels", 7) == SERIES_RENDER_COST
    assert _series_render_cost(None, 7) == SERIES_RENDER_COST
    assert _series_render_cost("ai_image", 0) >= SERIES_RENDER_COST


def test_a_bigger_episode_costs_more():
    from app.pipeline.series_tasks import _series_render_cost

    assert _series_render_cost("ai_image", 12) > _series_render_cost("ai_image", 3)


# ---- free proof renders ------------------------------------------------------

def _make_video(client, auth_headers, capture_generate):
    return client.post("/api/scripts/generate", headers=auth_headers,
                       json={"custom_prompt": "a quiet evening in the old city",
                             "output_type": "narrated"}).json()["video_id"]


@pytest.fixture()
def capture_generate(monkeypatch):
    async def fake_generate(topic, **kwargs):
        return {
            "title": "t", "description": "d", "tags": [],
            "segments": [{"text": "hello world", "visual_prompt": "x", "duration_estimate": 2.0}],
            "total_duration": 2.0,
        }

    monkeypatch.setattr("app.routers.scripts.script_gen.generate_script", fake_generate)


@pytest.fixture()
def no_proof_dispatch(monkeypatch):
    calls = []
    import app.pipeline.proof as pf

    class FakeTask:
        id = "fake"

    monkeypatch.setattr(pf.render_proof, "delay", lambda *a, **k: calls.append(a) or FakeTask())
    return calls


def test_ai_image_previews_are_capped_per_day(client, auth_headers, capture_generate, no_proof_dispatch):
    """Free previews spend real Vertex money per press, and with plan
    enforcement off every signed-in stranger can reach the expensive lane."""
    from app.routers.pipeline import FREE_AI_PROOFS_PER_DAY

    video_id = _make_video(client, auth_headers, capture_generate)
    body = {"video_id": video_id, "scene_index": 0, "visual_engine": "ai_image"}

    for i in range(FREE_AI_PROOFS_PER_DAY):
        resp = client.post("/api/pipeline/proof", headers=auth_headers, json=body)
        assert resp.status_code == 200, f"preview {i + 1} should be allowed: {resp.text}"

    over = client.post("/api/pipeline/proof", headers=auth_headers, json=body)
    assert over.status_code == 429
    assert "unlimited" in over.json()["detail"], "the message must say what still works"


def test_stock_previews_are_never_capped(client, auth_headers, capture_generate, no_proof_dispatch):
    """Only the lane that costs money per press is limited — the whole point
    of a proof render is to judge the look before paying."""
    from app.routers.pipeline import FREE_AI_PROOFS_PER_DAY

    video_id = _make_video(client, auth_headers, capture_generate)
    for _ in range(FREE_AI_PROOFS_PER_DAY + 3):
        resp = client.post("/api/pipeline/proof", headers=auth_headers,
                           json={"video_id": video_id, "scene_index": 0, "visual_engine": "pexels"})
        assert resp.status_code == 200, resp.text


def test_the_cap_counts_in_the_database_not_just_redis(client, auth_headers, capture_generate, no_proof_dispatch):
    """A rate limit that a Redis restart clears is not a spend cap."""
    video_id = _make_video(client, auth_headers, capture_generate)
    client.post("/api/pipeline/proof", headers=auth_headers,
                json={"video_id": video_id, "scene_index": 0, "visual_engine": "ai_image"})

    async def count():
        async with AsyncSessionLocal() as db:
            return await db.scalar(
                select(CreditLedger).where(CreditLedger.type == "proof_ai_image").limit(1)
            )

    row = asyncio.run(count())
    assert row is not None, "the preview must leave a durable record"
    assert row.amount == 0, "a preview is free — the row is an audit record, not a charge"


def test_yesterdays_previews_do_not_count_against_today(client, auth_headers, capture_generate, no_proof_dispatch):
    from app.routers.pipeline import FREE_AI_PROOFS_PER_DAY

    video_id = _make_video(client, auth_headers, capture_generate)
    me = client.get("/api/auth/me", headers=auth_headers).json()

    async def seed_old():
        from uuid import UUID

        async with AsyncSessionLocal() as db:
            old = datetime.now(timezone.utc) - timedelta(days=2)
            for _ in range(FREE_AI_PROOFS_PER_DAY + 2):
                db.add(CreditLedger(user_id=UUID(me["id"]), amount=0, type="proof_ai_image",
                                    description="old", created_at=old))
            await db.commit()

    asyncio.run(seed_old())

    resp = client.post("/api/pipeline/proof", headers=auth_headers,
                       json={"video_id": video_id, "scene_index": 0, "visual_engine": "ai_image"})
    assert resp.status_code == 200, "a day-old preview must not consume today's allowance"
