"""Instagram Reels publishing via the official Graph API.

Flow: Facebook Login OAuth → long-lived user token → find the IG Business
account behind the user's Page → create a REELS media container (Meta fetches
the video from a PUBLIC URL) → poll until FINISHED → publish.

Works in Meta App Development Mode for the app's own admins/developers/testers;
public users require Meta App Review of instagram_content_publish.
"""
import asyncio
import logging
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx
from jose import JWTError, jwt

from app.config import settings
from app.core.security import decrypt_token

logger = logging.getLogger("kliptos.instagram")

GRAPH = "https://graph.facebook.com/v21.0"
OAUTH_DIALOG = "https://www.facebook.com/v21.0/dialog/oauth"
SCOPES = "instagram_basic,instagram_content_publish,pages_show_list,pages_read_engagement,business_management"
STATE_PURPOSE = "ig_connect"


def enabled() -> bool:
    return bool(settings.META_APP_ID and settings.META_APP_SECRET)


def media_public_base() -> str:
    return (settings.MEDIA_PUBLIC_URL or settings.API_PUBLIC_URL).rstrip("/")


def redirect_uri() -> str:
    return f"{settings.API_PUBLIC_URL}/api/instagram/callback"


async def verify_state(state: str) -> str | None:
    """Single-use server-stored nonce (consumed on first verification)."""
    from app.services.oauth_state import consume_state

    return await consume_state(state, STATE_PURPOSE)


async def build_auth_url(user_id: str) -> str:
    from app.services.oauth_state import create_state

    params = {
        "client_id": settings.META_APP_ID,
        "redirect_uri": redirect_uri(),
        "response_type": "code",
        "scope": SCOPES,
        "state": await create_state(user_id, STATE_PURPOSE),
    }
    return f"{OAUTH_DIALOG}?{urlencode(params)}"


async def exchange_code(code: str) -> str:
    """code → short-lived token → long-lived token (~60 days)."""
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"{GRAPH}/oauth/access_token",
            params={
                "client_id": settings.META_APP_ID,
                "client_secret": settings.META_APP_SECRET,
                "redirect_uri": redirect_uri(),
                "code": code,
            },
        )
        resp.raise_for_status()
        short_token = resp.json()["access_token"]

        resp = await client.get(
            f"{GRAPH}/oauth/access_token",
            params={
                "grant_type": "fb_exchange_token",
                "client_id": settings.META_APP_ID,
                "client_secret": settings.META_APP_SECRET,
                "fb_exchange_token": short_token,
            },
        )
        resp.raise_for_status()
        return resp.json()["access_token"]


async def discover_ig_account(token: str) -> dict | None:
    """First Page with a connected IG Business account → {ig_user_id, username, page_id}."""
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"{GRAPH}/me/accounts",
            params={"fields": "id,name,instagram_business_account", "access_token": token},
        )
        resp.raise_for_status()
        for page in resp.json().get("data", []):
            ig = page.get("instagram_business_account")
            if not ig:
                continue
            info = await client.get(
                f"{GRAPH}/{ig['id']}",
                params={"fields": "username", "access_token": token},
            )
            info.raise_for_status()
            return {
                "ig_user_id": ig["id"],
                "username": info.json().get("username"),
                "page_id": page["id"],
            }
    return None


# ---------------------------------------------------------------------------
# Reels publish (sync — runs in Celery workers)
# ---------------------------------------------------------------------------

def publish_reel(ig_account, video_public_url: str, caption: str) -> str:
    """Create a REELS container, wait for Meta to process it, publish.
    Returns the IG media id. Meta must be able to FETCH video_public_url."""
    token = decrypt_token(ig_account.access_token)
    if not token:
        raise RuntimeError("Instagram token undecryptable — reconnect the account")

    with httpx.Client(timeout=60) as client:
        resp = client.post(
            f"{GRAPH}/{ig_account.ig_user_id}/media",
            data={
                "media_type": "REELS",
                "video_url": video_public_url,
                "caption": caption[:2200],
                "share_to_feed": "true",
                "access_token": token,
            },
        )
        resp.raise_for_status()
        container_id = resp.json()["id"]
        logger.info("ig container created: %s", container_id)

        # Poll processing status (video fetch + transcode on Meta's side)
        for _ in range(60):  # up to ~5 min
            status = client.get(
                f"{GRAPH}/{container_id}",
                params={"fields": "status_code", "access_token": token},
            )
            status.raise_for_status()
            code = status.json().get("status_code")
            if code == "FINISHED":
                break
            if code == "ERROR":
                raise RuntimeError("Instagram could not process the video (is the media URL public?)")
            time.sleep(5)
        else:
            raise RuntimeError("Instagram processing timed out")

        resp = client.post(
            f"{GRAPH}/{ig_account.ig_user_id}/media_publish",
            data={"creation_id": container_id, "access_token": token},
        )
        resp.raise_for_status()
        media_id = resp.json()["id"]
        logger.info("published to instagram: %s", media_id)
        return media_id
