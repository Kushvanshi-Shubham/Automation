"""Verification of Google ID tokens (sent by the Next.js frontend after Google sign-in)."""
import asyncio
import logging
from typing import Any, Optional

from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from app.config import settings

logger = logging.getLogger("kliptos.google_auth")

_transport = google_requests.Request()


def _verify_sync(token: str) -> Optional[dict[str, Any]]:
    if not settings.GOOGLE_CLIENT_ID:
        logger.error("GOOGLE_CLIENT_ID is not set — every sign-in will be rejected")
        return None
    try:
        claims = id_token.verify_oauth2_token(token, _transport, settings.GOOGLE_CLIENT_ID)
    except ValueError as exc:
        # Log the reason, never the token. The usual cause is an audience
        # mismatch: this service's GOOGLE_CLIENT_ID must be byte-identical to
        # the frontend's AUTH_GOOGLE_ID, or google-auth rejects a perfectly
        # good token and the only symptom upstream is a bare 401.
        logger.warning(
            "Google ID token rejected: %s (expected audience ends ...%s)",
            exc, settings.GOOGLE_CLIENT_ID[-28:],
        )
        return None
    if claims.get("iss") not in ("accounts.google.com", "https://accounts.google.com"):
        logger.warning("Google ID token rejected: unexpected issuer %r", claims.get("iss"))
        return None
    if not claims.get("email_verified"):
        logger.warning("Google ID token rejected: email not verified")
        return None
    return claims


async def verify_google_id_token(token: str) -> Optional[dict[str, Any]]:
    """Returns Google claims (sub, email, name, picture) or None. Runs the
    blocking google-auth verification off the event loop."""
    return await asyncio.to_thread(_verify_sync, token)
