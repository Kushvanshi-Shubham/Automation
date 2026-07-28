from fastapi import APIRouter, Depends
from app.schemas.billing import CheckoutRequest, CreditBalanceResponse
from typing import Any

router = APIRouter(prefix="/billing", tags=["Billing"])

@router.post("/checkout")
async def create_checkout_session(req: CheckoutRequest) -> Any:
    """Create Stripe checkout session for buying credits."""
    return {"url": "https://checkout.stripe.com/pay/..."}

@router.get("/credits", response_model=CreditBalanceResponse)
async def get_credits() -> Any:
    """Get current credit balance."""
    return {"balance": 0, "plan": "free"}

@router.post("/subscribe")
async def create_subscription(plan_id: str) -> Any:
    """Subscribe to a monthly plan."""
    return {"url": "https://checkout.stripe.com/subscribe/..."}
