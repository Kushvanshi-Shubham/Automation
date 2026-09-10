"""Monthly credit renewal.

This task moves real money, so the tests pin the decisions rather than
the implementation: it must never reduce a balance, never grant on the
plan a user is merely *served*, and never pay someone twice in a month.
"""
import asyncio
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select, update

from app.database import AsyncSessionLocal
from app.models.credit import CreditLedger
from app.models.user import User
from app.pipeline.credit_grants import GRANT_INTERVAL_DAYS, _run


@pytest.fixture(autouse=True)
def restore_the_user():
    """Put the shared user back exactly as it was.

    Every test file here runs against one sqlite database and one signed-up
    user, and these tests rewrite that user's plan, email and balance. Left
    behind, an email set to an admin address makes plans.effective_plan
    return Studio for every later test in the run — which is how this file
    broke three tests in other modules that had nothing to do with it.
    """
    before = _snapshot()
    yield
    if before:
        _set_user(**before)


def _snapshot():
    async def run():
        async with AsyncSessionLocal() as db:
            user = (await db.execute(select(User))).scalars().first()
            if user is None:
                return None
            return {
                "email": user.email,
                "plan": user.plan,
                "credit_balance": user.credit_balance,
                "credits_granted_at": user.credits_granted_at,
            }

    return asyncio.run(run())


def _tick():
    return asyncio.run(_run())


def _set_user(**values):
    async def run():
        async with AsyncSessionLocal() as db:
            await db.execute(update(User).values(**values))
            await db.commit()

    asyncio.run(run())


def _user():
    async def run():
        async with AsyncSessionLocal() as db:
            return (await db.execute(select(User))).scalars().first()

    return asyncio.run(run())


def _grant_entries():
    async def run():
        async with AsyncSessionLocal() as db:
            rows = (await db.execute(
                select(CreditLedger).where(CreditLedger.type == "subscription_grant")
            )).scalars().all()
            return [(r.amount, r.description) for r in rows]

    return asyncio.run(run())


@pytest.fixture()
def a_user(client, auth_headers):
    """One signed-up user, due for renewal, on the real free plan."""
    client.get("/api/auth/me", headers=auth_headers)
    _set_user(
        plan="free",
        email="creator@example.com",   # not an admin address
        credit_balance=0,
        credits_granted_at=datetime.now(timezone.utc) - timedelta(days=GRANT_INTERVAL_DAYS + 1),
    )
    return _user()


def test_a_spent_out_free_user_gets_topped_up(a_user):
    """The dead end this exists to remove: three renders and no way past."""
    before = len(_grant_entries())
    result = _tick()

    assert result["granted"] == 1
    assert _user().credit_balance == 3
    entries = _grant_entries()
    assert len(entries) == before + 1
    assert entries[-1][0] == 3
    assert "Free" in entries[-1][1]


def test_renewal_tops_up_rather_than_adding(a_user):
    """Unused free credits must not stack into a bankable pile."""
    _set_user(credit_balance=2,
              credits_granted_at=datetime.now(timezone.utc) - timedelta(days=GRANT_INTERVAL_DAYS + 1))
    _tick()
    # Topped up TO 3, not 2 + 3.
    assert _user().credit_balance == 3


def test_a_balance_above_the_allowance_is_never_reduced(a_user):
    """Someone who bought a top-up must not be robbed by the renewal."""
    _set_user(credit_balance=40,
              credits_granted_at=datetime.now(timezone.utc) - timedelta(days=GRANT_INTERVAL_DAYS + 1))
    result = _tick()

    assert _user().credit_balance == 40
    assert result["granted"] == 0, "no credits were owed"
    # But the clock still moved, or this user is re-examined every night.
    assert _user().credits_granted_at is not None


def test_nobody_is_paid_twice_in_a_month(a_user):
    _tick()
    assert _user().credit_balance == 3

    # Spend it, then tick again the same day.
    _set_user(credit_balance=0)
    result = _tick()

    assert result["users_due"] == 0
    assert _user().credit_balance == 0, "a second grant inside the month would be free money"


def test_the_allowance_follows_the_paid_plan_not_the_served_one(a_user):
    """While enforcement is off every user is SERVED Pro. Granting on that
    basis would hand every stranger 50 credits a month of real spend."""
    from app.services import plans

    user = _user()
    # What the app serves them...
    assert plans.effective_plan(user) in (plans.PRO, plans.STUDIO)
    # ...is not what they are paid up for.
    assert user.plan == "free"
    assert plans.monthly_credits(user) == 3

    _tick()
    assert _user().credit_balance == 3


def test_a_pro_plan_renews_to_the_pro_allowance(a_user):
    _set_user(plan="pro", credit_balance=0,
              credits_granted_at=datetime.now(timezone.utc) - timedelta(days=GRANT_INTERVAL_DAYS + 1))
    _tick()
    assert _user().credit_balance == 50
    assert "Pro" in _grant_entries()[-1][1]


def test_admins_renew_at_the_studio_allowance(a_user):
    """The owner has to be able to exercise every lane to test it."""
    from app.config import settings

    admin = (settings.ADMIN_EMAILS or [None])[0]
    if not admin:
        pytest.skip("no ADMIN_EMAILS configured in this environment")
    _set_user(email=admin, plan="free", credit_balance=0,
              credits_granted_at=datetime.now(timezone.utc) - timedelta(days=GRANT_INTERVAL_DAYS + 1))
    _tick()
    assert _user().credit_balance == 150


def test_a_brand_new_user_waits_a_month(client, auth_headers):
    """Signup sets the clock, so the next nightly tick must not pay again."""
    client.get("/api/auth/me", headers=auth_headers)
    _set_user(plan="free", email="creator@example.com", credit_balance=1,
              credits_granted_at=datetime.now(timezone.utc))

    result = _tick()
    assert result["users_due"] == 0
    assert _user().credit_balance == 1


def test_credits_endpoint_says_when_it_renews(client, auth_headers, a_user):
    body = client.get("/api/billing/credits", headers=auth_headers).json()
    assert body["monthly_credits"] == 3
    assert body["renews_at"], "running out is a wait, but only if we say until when"
