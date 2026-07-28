"""Verification of Google ID tokens (sent by the Next.js frontend after Google sign-in)."""
import asyncio
from typing import Any, Optional

from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from app.config import settings

_transport = google_requests.Request()


def _verify_sync(token: str) -> Optional[dict[str, Any]]:
    try:
        claims = id_token.verify_oauth2_token(token, _transport, settings.GOOGLE_CLIENT_ID)
    except ValueError:
        return None
    if claims.get("iss") not in ("accounts.google.com", "https://accounts.google.com"):
        return None
    if not claims.get("email_verified"):
        return None
    return claims


async def verify_google_id_token(token: str) -> Optional[dict[str, Any]]:
    """Returns Google claims (sub, email, name, picture) or None. Runs the
    blocking google-auth verification off the event loop."""
    return await asyncio.to_thread(_verify_sync, token)
