from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import encrypt_token
from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.api_key import UserApiKey
from app.models.user import User
from app.services.user_keys import SUPPORTED_PROVIDERS, validate_key

router = APIRouter(prefix="/settings/api-keys", tags=["Settings"], dependencies=[Depends(get_current_user)])


class ApiKeyUpsert(BaseModel):
    provider: str
    key: str = Field(min_length=10, max_length=400)


@router.get("")
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """The user's stored providers, masked — plaintext is never returned."""
    rows = (
        await db.execute(select(UserApiKey).where(UserApiKey.user_id == current_user.id))
    ).scalars().all()
    return {
        "items": [
            {"provider": r.provider, "masked": f"••••{r.key_encrypted[-4:]}", "created_at": r.created_at}
            for r in rows
        ]
    }


@router.put("")
async def upsert_api_key(
    req: ApiKeyUpsert,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if req.provider not in SUPPORTED_PROVIDERS:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Unsupported provider")

    if not await validate_key(req.provider, req.key.strip()):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"That {req.provider} key didn't work — check it and try again",
        )

    row = (
        await db.execute(
            select(UserApiKey).where(
                UserApiKey.user_id == current_user.id, UserApiKey.provider == req.provider
            )
        )
    ).scalar_one_or_none()
    if row is None:
        row = UserApiKey(user_id=current_user.id, provider=req.provider)
        db.add(row)
    row.key_encrypted = encrypt_token(req.key.strip())
    await db.commit()
    return {"status": "saved", "provider": req.provider}


@router.delete("/{provider}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    provider: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    row = (
        await db.execute(
            select(UserApiKey).where(UserApiKey.user_id == current_user.id, UserApiKey.provider == provider)
        )
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No key stored for that provider")
    await db.delete(row)
    await db.commit()
