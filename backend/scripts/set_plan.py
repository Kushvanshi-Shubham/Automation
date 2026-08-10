"""Set a user's plan and credits — for testing the paywall.

    python scripts/set_plan.py <email> [--plan free|pro|studio] [--credits N]

Works against whatever DATABASE_URL points at, so the same command tunes
the local database or the deployed one:

    # local
    ./.venv/Scripts/python.exe scripts/set_plan.py smoke@kliptos.dev --plan pro --credits 50

    # cloud (PowerShell)
    $env:DATABASE_URL="postgresql+asyncpg://...neon.../neondb?ssl=require"
    ./.venv/Scripts/python.exe scripts/set_plan.py you@example.com --plan free

NOTE: plans only bite when PLAN_ENFORCEMENT_ENABLED=true, and emails in
ADMIN_EMAILS always resolve to Studio regardless of this column.
"""
import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select  # noqa: E402

from app.database import AsyncSessionLocal  # noqa: E402
from app.models.credit import CreditLedger  # noqa: E402
from app.models.user import User  # noqa: E402
from app.services.plans import PLANS  # noqa: E402


async def main(email: str, plan: str | None, credits: int | None) -> int:
    async with AsyncSessionLocal() as db:
        user = (await db.execute(select(User).where(User.email == email.lower()))).scalar_one_or_none()
        if user is None:
            print(f"No user with email {email!r}. Sign in once first so the account exists.")
            return 1

        before = (user.plan, user.credit_balance)
        if plan:
            user.plan = plan
        if credits is not None:
            delta = credits - (user.credit_balance or 0)
            user.credit_balance = credits
            if delta:
                db.add(CreditLedger(
                    user_id=user.id, amount=delta, type="admin_adjustment",
                    description="Manual adjustment (scripts/set_plan.py)",
                ))
        await db.commit()
        print(f"{email}: plan {before[0]} -> {user.plan}, credits {before[1]} -> {user.credit_balance}")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Set a user's plan and credits")
    ap.add_argument("email")
    ap.add_argument("--plan", choices=sorted(PLANS), help="free | pro | studio")
    ap.add_argument("--credits", type=int, help="set the credit balance to this number")
    args = ap.parse_args()
    if not args.plan and args.credits is None:
        ap.error("give --plan and/or --credits")
    raise SystemExit(asyncio.run(main(args.email, args.plan, args.credits)))
