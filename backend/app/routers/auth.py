from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.database import get_db
from app.middleware.auth import get_current_user
from app.middleware.rate_limit import rate_limit_ip
from app.models.credit import CreditLedger
from app.models.user import User
from app.schemas.auth import GoogleAuthRequest, TokenResponse
from app.schemas.user import UserResponse
from app.services.google_auth import verify_google_id_token

router = APIRouter(prefix="/auth", tags=["Auth"])

FREE_TIER_SIGNUP_CREDITS = 3


@router.post("/google", response_model=TokenResponse, dependencies=[Depends(rate_limit_ip("auth_google"))])
async def auth_google(request: GoogleAuthRequest, db: AsyncSession = Depends(get_db)):
    """Exchange a Google ID token for a Kliptos access token, creating the user on first login."""
    claims = await verify_google_id_token(request.id_token)
    if claims is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Google token")

    google_id = claims["sub"]
    email = claims["email"]

    result = await db.execute(
        select(User).where((User.google_id == google_id) | (User.email == email))
    )
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            email=email,
            google_id=google_id,
            name=claims.get("name"),
            avatar_url=claims.get("picture"),
            credit_balance=FREE_TIER_SIGNUP_CREDITS,
        )
        db.add(user)
        await db.flush()
        db.add(
            CreditLedger(
                user_id=user.id,
                amount=FREE_TIER_SIGNUP_CREDITS,
                type="subscription_grant",
                description="Free tier signup grant",
            )
        )
    else:
        # Keep profile fresh; link google_id if the account pre-existed by email.
        user.google_id = user.google_id or google_id
        user.name = claims.get("name") or user.name
        user.avatar_url = claims.get("picture") or user.avatar_url

    await db.commit()
    await db.refresh(user)

    return TokenResponse(access_token=create_access_token(str(user.id)), token_type="bearer")


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
