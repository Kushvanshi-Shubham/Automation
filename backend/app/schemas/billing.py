from pydantic import BaseModel, ConfigDict
from uuid import UUID
from typing import List, Optional
from datetime import datetime

class CheckoutRequest(BaseModel):
    amount_cents: int
    credits: int

class CreditBalanceResponse(BaseModel):
    balance: int
    plan: str
    # What this plan renews to each month, and when. Running out is a wait
    # rather than a dead end, but only if the UI can say when it ends.
    monthly_credits: int = 0
    renews_at: Optional[datetime] = None

class CreditLedgerResponse(BaseModel):
    id: UUID
    amount: int
    type: str
    description: Optional[str]
    created_at: Optional[datetime]
    model_config = ConfigDict(from_attributes=True)
