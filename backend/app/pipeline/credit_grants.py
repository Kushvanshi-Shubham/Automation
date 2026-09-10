"""Celery task: renew each user's monthly credit allowance.

Credits used to be granted exactly once, at signup. Everything else only
ever subtracted, apart from refunds — so a creator made three videos and
then hit a wall with no way past it, because checkout returns 501. That is
not a paywall, it is a dead end, and it applied to every account.

This tops each user back up to their plan's allowance once a month.

Two decisions worth keeping:

**Top up, never add.** A user is raised TO their allowance, so unused free
credits do not stack into a bankable pile — but a balance already above it
(bought as a top-up, or an admin's) is left alone. The task can never
reduce anyone.

**Granted on the plan they PAY for, not the plan they are served.** While
PLAN_ENFORCEMENT_ENABLED is off, plans.effective_plan serves Pro to
everyone so the beta is not crippled. Granting on that basis would hand
every signed-up stranger 50 credits a month of real Vertex and Pexels
spend. See plans.monthly_credits.
"""
import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.credit import CreditLedger
from app.models.user import User
from app.pipeline.celery_app import celery_app
from app.services import plans

logger = logging.getLogger("kliptos.credits")

# A month, near enough. Not calendar-based: a per-user clock means someone
# who signs up on the 30th does not get a second month the next day.
GRANT_INTERVAL_DAYS = 30


async def _run() -> dict:
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=GRANT_INTERVAL_DAYS)
    granted = 0
    credits_added = 0

    async with AsyncSessionLocal() as db:
        rows = (
            await db.execute(
                select(User).where(
                    (User.credits_granted_at.is_(None)) | (User.credits_granted_at <= cutoff)
                )
            )
        ).scalars().all()

        for user in rows:
            allowance = plans.monthly_credits(user)
            # Always move the clock, even when no credits are owed, or a user
            # sitting above their allowance would be re-examined every night.
            user.credits_granted_at = now
            if user.credit_balance >= allowance:
                continue
            top_up = allowance - user.credit_balance
            user.credit_balance = allowance
            db.add(CreditLedger(
                user_id=user.id,
                amount=top_up,
                type="subscription_grant",
                description=f"Monthly {plans.PLANS.get(user.plan or plans.FREE, plans.PLANS[plans.FREE])['label']} allowance",
            ))
            granted += 1
            credits_added += top_up

        await db.commit()

    if granted:
        logger.info("monthly credits: topped up %d users with %d credits", granted, credits_added)
    else:
        logger.info("monthly credits: %d users due, none needed a top-up", len(rows))
    return {"users_due": len(rows), "granted": granted, "credits": credits_added}


@celery_app.task(name="billing.grant_monthly_credits")
def grant_monthly_credits():
    from app.pipeline.tasks import _with_fresh_pool

    return asyncio.run(_with_fresh_pool(_run()))
