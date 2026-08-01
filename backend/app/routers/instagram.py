from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.security import encrypt_token
from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.ig_account import IgAccount
from app.models.user import User
from app.services import instagram

# /callback is hit by Meta's redirect (no JWT) — auth is per-endpoint here.
router = APIRouter(prefix="/instagram", tags=["Instagram"])


class IgAccountResponse(BaseModel):
    id: UUID
    ig_user_id: str
    username: str | None
    is_active: bool | None
    model_config = ConfigDict(from_attributes=True)


@router.get("/status")
async def ig_status(current_user: User = Depends(get_current_user)):
    """Feature flag for the UI."""
    return {"enabled": instagram.enabled()}


@router.get("", response_model=list[IgAccountResponse])
async def list_accounts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(IgAccount).where(IgAccount.user_id == current_user.id, IgAccount.is_active == True)  # noqa: E712
    )
    return result.scalars().all()


@router.get("/connect")
async def connect(current_user: User = Depends(get_current_user)):
    if not instagram.enabled():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Instagram is not configured yet (META_APP_ID/SECRET missing)",
        )
    return {"auth_url": await instagram.build_auth_url(str(current_user.id))}


@router.get("/callback")
async def oauth_callback(
    state: str,
    code: str | None = None,
    error: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    settings_url = f"{settings.FRONTEND_URL}/dashboard/settings"
    if error or not code:
        return RedirectResponse(f"{settings_url}?ig_error={error or 'cancelled'}")

    user_id = await instagram.verify_state(state)
    if user_id is None:
        return RedirectResponse(f"{settings_url}?ig_error=invalid_state")

    try:
        token = await instagram.exchange_code(code)
    except Exception:
        return RedirectResponse(f"{settings_url}?ig_error=token_exchange_failed")

    info = await instagram.discover_ig_account(token)
    if info is None:
        return RedirectResponse(
            f"{settings_url}?ig_error=no_business_account_found_link_ig_to_a_facebook_page"
        )

    result = await db.execute(select(IgAccount).where(IgAccount.ig_user_id == info["ig_user_id"]))
    account = result.scalar_one_or_none()
    if account is None:
        account = IgAccount(user_id=UUID(user_id), ig_user_id=info["ig_user_id"])
        db.add(account)
    elif str(account.user_id) != user_id:
        return RedirectResponse(f"{settings_url}?ig_error=account_owned_by_other_user")

    account.username = info["username"]
    account.page_id = info["page_id"]
    account.access_token = encrypt_token(token)
    account.token_expires_at = datetime.now(timezone.utc) + timedelta(days=55)
    account.is_active = True
    await db.commit()

    return RedirectResponse(f"{settings_url}?ig_connected={info['username'] or 'account'}")


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def disconnect(
    account_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    account = await db.get(IgAccount, account_id)
    if account is None or account.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    account.is_active = False
    account.access_token = None
    await db.commit()
