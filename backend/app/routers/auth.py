from fastapi import APIRouter, Depends
from app.schemas.auth import GoogleAuthRequest, TokenResponse
from app.schemas.user import UserResponse
from typing import Any

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/google", response_model=TokenResponse)
async def auth_google(request: GoogleAuthRequest) -> Any:
    """Authenticate with Google OAuth token."""
    return {"access_token": "dummy_token", "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def get_me() -> Any:
    """Get current authenticated user."""
    return {
        "id": "00000000-0000-0000-0000-000000000000",
        "email": "test@example.com",
        "name": "Test User",
        "avatar_url": None,
        "credit_balance": 10,
        "plan": "free",
        "created_at": None,
        "updated_at": None
    }
