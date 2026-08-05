from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.credit import CreditLedger
from app.models.user import User
from app.schemas.billing import CheckoutRequest, CreditBalanceResponse, CreditLedgerResponse

router = APIRouter(prefix="/billing", tags=["Billing"], dependencies=[Depends(get_current_user)])


@router.get("/credits", response_model=CreditBalanceResponse)
async def get_credits(current_user: User = Depends(get_current_user)):
    return CreditBalanceResponse(balance=current_user.credit_balance, plan=current_user.plan)


@router.get("/plan")
async def get_plan(current_user: User = Depends(get_current_user)):
    """What this user's plan includes, and what each engine costs in credits.

    The UI reads this so limits and upsells are never hardcoded in the
    frontend — one source of truth for what Pro actually buys you.
    """
    from app.services import plans
    from app.services.credits import price_table

    feats = plans.features(current_user)
    return {
        "plan": plans.effective_plan(current_user),
        "label": feats["label"],
        "features": {k: v for k, v in feats.items() if k != "label"},
        "engine_credits": price_table(),
        "enforced": settings.PLAN_ENFORCEMENT_ENABLED,
    }


@router.get("/ledger", response_model=list[CreditLedgerResponse])
async def get_ledger(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CreditLedger)
        .where(CreditLedger.user_id == current_user.id)
        .order_by(CreditLedger.created_at.desc())
        .limit(100)
    )
    return result.scalars().all()


@router.get("/economics")
async def platform_economics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Owner-only: credits moved vs. real API cost vs. implied margin."""
    from datetime import datetime, timezone

    from sqlalchemy import func

    from app.config import settings
    from app.services import costs

    if (current_user.email or "").lower() not in settings.ADMIN_EMAILS:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Owner only")

    month_start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    rows = (
        await db.execute(
            select(CreditLedger.type, func.count(CreditLedger.id), func.sum(CreditLedger.amount))
            .where(CreditLedger.created_at >= month_start)
            .group_by(CreditLedger.type)
        )
    ).all()
    credits = {t: {"entries": c, "credits": int(s or 0)} for t, c, s in rows}
    debited = abs(credits.get("video_debit", {}).get("credits", 0))
    refunded = credits.get("refund", {}).get("credits", 0)
    net_spent = debited - refunded

    usage = costs.month_usage()
    est = costs.estimated_cost_usd(usage)
    implied_revenue = round(net_spent * settings.CREDIT_PRICE_USD, 2)

    return {
        "month": month_start.strftime("%Y-%m"),
        "credits": {"debited": debited, "refunded": refunded, "net_spent": net_spent,
                    "granted": credits.get("subscription_grant", {}).get("credits", 0)},
        "usage": usage,
        "estimated_cost_usd": est,
        "credit_price_usd": settings.CREDIT_PRICE_USD,
        "implied_revenue_usd": implied_revenue,  # if every net credit were paid
        "implied_margin_usd": round(implied_revenue - est["total"], 2),
        "note": "Costs are the platform-key unit-cost model (BYO usage excluded). Revenue is implied until billing is live.",
    }


@router.post("/checkout")
async def create_checkout_session(req: CheckoutRequest):
    # Implemented in the Stripe/Razorpay milestone of S1.
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Checkout not yet available")


@router.post("/subscribe")
async def create_subscription(plan_id: str):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Subscriptions not yet available")
