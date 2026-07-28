from fastapi import Depends, HTTPException
from app.middleware.auth import get_current_user

def require_credits(amount: int):
    async def dependency(current_user: dict = Depends(get_current_user)):
        # check user has enough credits
        # placeholder implementation
        if current_user.get("credit_balance", 0) < amount:
            pass
        return current_user
    return dependency
