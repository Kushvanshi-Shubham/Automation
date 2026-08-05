"""Plan tiers: what Free gets, what Pro adds, and that nothing is
paywalled while enforcement is off (the beta state)."""
import asyncio

import pytest
from sqlalchemy import select

from app.pipeline import captions
from app.services import plans
from app.services.credits import credits_for_cost, engine_credit_cost


class _User:
    def __init__(self, email="creator@example.com", plan="free"):
        self.email = email
        self.plan = plan


@pytest.fixture()
def enforce(monkeypatch):
    monkeypatch.setattr("app.config.settings.PLAN_ENFORCEMENT_ENABLED", True)


def test_beta_serves_pro_to_everyone(monkeypatch):
    monkeypatch.setattr("app.config.settings.PLAN_ENFORCEMENT_ENABLED", False)
    assert plans.effective_plan(_User(plan="free")) == plans.PRO
    assert plans.allows(_User(plan="free"), "publish") is True


def test_free_plan_limits(enforce):
    free = _User(plan="free")
    assert plans.effective_plan(free) == plans.FREE
    assert plans.allows(free, "publish") is False
    assert plans.allows(free, "standing_orders") is False
    assert plans.allows(free, "teach_style") is False
    assert plans.features(free)["watermark"] is True
    assert plans.features(free)["max_height"] == 1280
    assert plans.features(free)["max_duration_seconds"] == 45


def test_pro_unlocks(enforce):
    pro = _User(plan="pro")
    for feature in ("publish", "standing_orders", "teach_style", "own_footage", "brand_kit"):
        assert plans.allows(pro, feature) is True
    assert plans.features(pro)["watermark"] is False
    assert plans.features(pro)["max_height"] == 1920
    assert plans.allows(pro, "premium_engines") is False  # Studio only


def test_admin_always_studio(enforce, monkeypatch):
    monkeypatch.setattr("app.config.settings.ADMIN_EMAILS", ["owner@kliptos.dev"])
    assert plans.effective_plan(_User(email="Owner@Kliptos.dev", plan="free")) == plans.STUDIO
    assert plans.allows(_User(email="owner@kliptos.dev"), "premium_engines") is True


def test_require_raises_402_with_plain_words(enforce):
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        plans.require(_User(plan="free"), "publish")
    assert exc.value.status_code == 402
    assert "Pro" in exc.value.detail


def test_tier_dimensions_scale_and_stay_even():
    assert plans.tier_dimensions(1080, 1920, 1920) == (1080, 1920)  # untouched
    w, h = plans.tier_dimensions(1080, 1920, 1280)
    assert (w, h) == (720, 1280)
    assert w % 2 == 0 and h % 2 == 0
    w, h = plans.tier_dimensions(1920, 1080, 1280)  # already under the cap
    assert (w, h) == (1920, 1080)


def test_credit_costs_come_from_real_cost(monkeypatch):
    monkeypatch.setattr("app.config.settings.CREDIT_PRICE_USD", 0.10)
    # 1 credit floor for the near-free stock lane
    assert engine_credit_cost("pexels") == 1
    # AI images (~$0.20 real) must cost more than a stock render
    assert engine_credit_cost("ai_image") == 4
    # A premium engine can never be sold below cost: $8.50 at 2x margin
    assert engine_credit_cost("veo_fast") == 170
    assert engine_credit_cost("nope") is None
    assert credits_for_cost(0.0) == 1


def test_watermark_lands_in_the_ass_file(tmp_path):
    marked = captions.write_ass([], tmp_path / "m.ass", watermark_seconds=12.0)
    text = marked.read_text(encoding="utf-8")
    assert captions.WATERMARK_TEXT in text
    assert "Style: Mark" in text

    clean = captions.build_segment_captions(
        words=[], text="hello world", duration=3.0, out_path=tmp_path / "c.ass",
    )
    assert captions.WATERMARK_TEXT not in clean.read_text(encoding="utf-8")


def _set_plan(email, plan):
    from app.database import AsyncSessionLocal
    from app.models.user import User as UserRow

    async def _run():
        async with AsyncSessionLocal() as db:
            row = (await db.execute(select(UserRow).where(UserRow.email == email))).scalar_one()
            row.plan = plan
            await db.commit()

    asyncio.run(_run())


def test_plan_endpoint_reports_features(client, auth_headers):
    body = client.get("/api/billing/plan", headers=auth_headers).json()
    assert body["plan"] in (plans.FREE, plans.PRO, plans.STUDIO)
    assert "watermark" in body["features"]
    assert body["engine_credits"]["pexels"] >= 1
    assert body["enforced"] is False


def test_publish_is_gated_for_free(client, auth_headers, monkeypatch):
    _set_plan("creator@example.com", "free")
    monkeypatch.setattr("app.config.settings.PLAN_ENFORCEMENT_ENABLED", True)
    monkeypatch.setattr("app.config.settings.ADMIN_EMAILS", [])
    resp = client.post(
        "/api/uploads/00000000-0000-0000-0000-000000000000/publish",
        headers=auth_headers,
        json={"channel_id": "00000000-0000-0000-0000-000000000000", "privacy": "unlisted", "category_id": "24"},
    )
    assert resp.status_code == 402
    assert "Pro" in resp.json()["detail"]

    # Two well-formed ids so schema validation passes and the plan gate is
    # what answers (the assets themselves don't need to exist).
    resp = client.post("/api/styles/learn", headers=auth_headers,
                       json={"name": "my style", "output_type": "narrated",
                             "asset_ids": ["11111111-1111-1111-1111-111111111111",
                                           "22222222-2222-2222-2222-222222222222"]})
    assert resp.status_code == 402

    resp = client.post("/api/series", headers=auth_headers,
                       json={"name": "Daily facts", "interval_hours": 24})
    assert resp.status_code == 402

    _set_plan("creator@example.com", "free")  # leave the shared user as found
