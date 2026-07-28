from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.credit import CreditLedger
from app.models.user import User
from app.schemas.billing import CheckoutRequest, CreditBalanceResponse, CreditLedgerResponse

router = APIRouter(prefix="/billing", tags=["Billing"], dependencies=[Depends(get_current_user)])


@router.get("/credits", response_model=CreditBalanceResponse)
async def get_credits(current_user: User = Depends(get_current_user)):
    return CreditBalanceResponse(balance=current_user.credit_balance, plan=current_user.plan)


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


@router.post("/checkout")
async def create_checkout_session(req: CheckoutRequest):
    # Implemented in the Stripe/Razorpay milestone of S1.
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Checkout not yet available")


@router.post("/subscribe")
async def create_subscription(plan_id: str):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Subscriptions not yet available")
