from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.security import encrypt_token
from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.channel import Channel
from app.models.user import User
from app.schemas.channel import ChannelResponse, ConnectUrlResponse
from app.services import youtube

# NOTE: no router-level auth — /callback is hit by Google's redirect (no JWT).
# Every other endpoint declares get_current_user explicitly.
router = APIRouter(prefix="/channels", tags=["Channels"])


@router.get("", response_model=list[ChannelResponse])
async def list_channels(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Channel).where(Channel.user_id == current_user.id, Channel.is_active == True)  # noqa: E712
    )
    return result.scalars().all()


@router.get("/connect", response_model=ConnectUrlResponse)
async def connect_channel(current_user: User = Depends(get_current_user)):
    """Returns the Google consent URL for connecting a YouTube channel."""
    if not (settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET):
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Google OAuth not configured")
    return {"auth_url": await youtube.build_auth_url(str(current_user.id))}


@router.get("/callback")
async def oauth_callback(
    state: str,
    code: str | None = None,
    error: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Google redirects here after consent. Identity comes from the signed state."""
    settings_url = f"{settings.FRONTEND_URL}/dashboard/settings"
    if error or not code:
        return RedirectResponse(f"{settings_url}?yt_error={error or 'cancelled'}")

    user_id = await youtube.verify_state(state)
    if user_id is None:
        return RedirectResponse(f"{settings_url}?yt_error=invalid_state")

    tokens = await youtube.exchange_code(code)
    access_token = tokens.get("access_token")
    refresh_token = tokens.get("refresh_token")
    if not access_token:
        return RedirectResponse(f"{settings_url}?yt_error=token_exchange_failed")

    info = await youtube.fetch_channel_info(access_token)
    if info is None:
        return RedirectResponse(f"{settings_url}?yt_error=no_channel_on_account")

    expires_at = datetime.now(timezone.utc) + timedelta(seconds=int(tokens.get("expires_in", 3600)))

    result = await db.execute(select(Channel).where(Channel.youtube_channel_id == info["id"]))
    channel = result.scalar_one_or_none()
    if channel is None:
        channel = Channel(user_id=UUID(user_id), youtube_channel_id=info["id"])
        db.add(channel)
    elif str(channel.user_id) != user_id:
        return RedirectResponse(f"{settings_url}?yt_error=channel_owned_by_other_account")

    channel.channel_name = info["title"]
    channel.access_token = encrypt_token(access_token)
    if refresh_token:
        channel.refresh_token = encrypt_token(refresh_token)
    channel.token_expires_at = expires_at
    channel.is_active = True
    await db.commit()

    return RedirectResponse(f"{settings_url}?yt_connected={info['title']}")


@router.delete("/{channel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def disconnect_channel(
    channel_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    channel = await db.get(Channel, channel_id)
    if channel is None or channel.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found")
    if channel.refresh_token:
        await youtube.revoke(channel.refresh_token)
    channel.is_active = False
    channel.access_token = None
    channel.refresh_token = None
    await db.commit()
