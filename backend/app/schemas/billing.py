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

class CreditLedgerResponse(BaseModel):
    id: UUID
    amount: int
    type: str
    description: Optional[str]
    created_at: Optional[datetime]
    model_config = ConfigDict(from_attributes=True)
