"""YouTube channel connection (OAuth) and video upload.

Tokens are Fernet-encrypted at rest (app.core.security). Uploads run inside
Celery workers; the API only creates auth URLs and handles the OAuth callback.
"""
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode

import httpx
from jose import JWTError, jwt

from app.config import settings
from app.core.security import decrypt_token, encrypt_token

logger = logging.getLogger("kliptos.youtube")

OAUTH_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
OAUTH_TOKEN_URL = "https://oauth2.googleapis.com/token"
OAUTH_REVOKE_URL = "https://oauth2.googleapis.com/revoke"
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
]
STATE_PURPOSE = "yt_connect"


def redirect_uri() -> str:
    return f"{settings.API_PUBLIC_URL}/api/channels/callback"


async def verify_state(state: str) -> str | None:
    """Single-use server-stored nonce (consumed on first verification)."""
    from app.services.oauth_state import consume_state

    return await consume_state(state, STATE_PURPOSE)


async def build_auth_url(user_id: str) -> str:
    from app.services.oauth_state import create_state

    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": redirect_uri(),
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "prompt": "consent",  # force refresh_token issuance on reconnect
        "state": await create_state(user_id, STATE_PURPOSE),
    }
    return f"{OAUTH_AUTH_URL}?{urlencode(params)}"


async def exchange_code(code: str) -> dict:
    """Authorization code -> {access_token, refresh_token, expires_in}."""
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            OAUTH_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": redirect_uri(),
                "grant_type": "authorization_code",
            },
        )
        resp.raise_for_status()
        return resp.json()


async def fetch_channel_info(access_token: str) -> dict | None:
    """The user's own channel: {id, title}."""
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            "https://www.googleapis.com/youtube/v3/channels",
            params={"part": "snippet", "mine": "true"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        resp.raise_for_status()
        items = resp.json().get("items", [])
    if not items:
        return None
    return {"id": items[0]["id"], "title": items[0]["snippet"]["title"]}


async def revoke(refresh_token_encrypted: str) -> None:
    token = decrypt_token(refresh_token_encrypted)
    if not token:
        return
    async with httpx.AsyncClient(timeout=15) as client:
        try:
            await client.post(OAUTH_REVOKE_URL, params={"token": token})
        except httpx.HTTPError as exc:
            logger.warning("token revoke failed: %s", exc)


# ---------------------------------------------------------------------------
# Upload (sync — runs in Celery workers)
# ---------------------------------------------------------------------------

def _credentials(channel):
    from google.oauth2.credentials import Credentials

    return Credentials(
        token=decrypt_token(channel.access_token) if channel.access_token else None,
        refresh_token=decrypt_token(channel.refresh_token) if channel.refresh_token else None,
        token_uri=OAUTH_TOKEN_URL,
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        scopes=SCOPES,
    )


# Assignable YouTube video categories (subset that accepts uploads)
YT_CATEGORIES = {
    "1": "Film & Animation",
    "10": "Music",
    "17": "Sports",
    "20": "Gaming",
    "22": "People & Blogs",
    "23": "Comedy",
    "24": "Entertainment",
    "25": "News & Politics",
    "26": "Howto & Style",
    "27": "Education",
    "28": "Science & Technology",
}


def upload_video_file(
    channel,
    file_path: Path,
    title: str,
    description: str,
    tags: list[str] | None,
    privacy: str = "unlisted",
    publish_at: str | None = None,
    category_id: str = "24",
) -> str:
    """Resumable upload; returns the YouTube video id.

    publish_at (ISO 8601 UTC) requires privacy='private' per YouTube rules —
    the video goes public automatically at that time.
    """
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    creds = _credentials(channel)
    youtube = build("youtube", "v3", credentials=creds, cache_discovery=False)

    status: dict = {"privacyStatus": "private" if publish_at else privacy,
                    "selfDeclaredMadeForKids": False}
    if publish_at:
        status["publishAt"] = publish_at

    body = {
        "snippet": {
            "title": (title or "Untitled Short")[:95],
            "description": (description or "")[:4900],
            "tags": (tags or [])[:30],
            "categoryId": category_id if category_id in YT_CATEGORIES else "24",
        },
        "status": status,
    }

    media = MediaFileUpload(str(file_path), mimetype="video/mp4", resumable=True, chunksize=4 * 1024 * 1024)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        progress, response = request.next_chunk()
        if progress:
            logger.info("upload progress: %d%%", int(progress.progress() * 100))

    video_id = response["id"]
    logger.info("uploaded to YouTube: %s", video_id)
    return video_id
