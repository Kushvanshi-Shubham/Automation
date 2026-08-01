"""Single-use OAuth state nonces (fixes account-linking attacks).

The old scheme signed {user_id, purpose} into a JWT: valid for 10 minutes and
REUSABLE — an attacker could mint a link for their own account and trick a
victim into completing consent, linking the victim's channel to the attacker.

New scheme: a random nonce stored server-side in Redis with a 10-minute TTL,
bound to (user_id, purpose) and CONSUMED atomically on first use.
"""
import logging
import secrets

from app.services.progress import async_redis

logger = logging.getLogger("kliptos.oauth_state")

TTL_SECONDS = 600
_PREFIX = "oauth_state:"

# Atomic get-and-delete (GETDEL needs Redis 6.2; EVAL works on our 5.x too)
_CONSUME_LUA = """
local v = redis.call('GET', KEYS[1])
if v then redis.call('DEL', KEYS[1]) end
return v
"""


async def create_state(user_id: str, purpose: str) -> str:
    nonce = secrets.token_urlsafe(32)
    client = async_redis()
    try:
        await client.setex(f"{_PREFIX}{nonce}", TTL_SECONDS, f"{purpose}|{user_id}")
    finally:
        await client.aclose()
    return nonce


async def consume_state(nonce: str, purpose: str) -> str | None:
    """Returns the user_id and invalidates the nonce; None if unknown/used/expired."""
    if not nonce or len(nonce) > 128:
        return None
    client = async_redis()
    try:
        value = await client.eval(_CONSUME_LUA, 1, f"{_PREFIX}{nonce}")
    finally:
        await client.aclose()
    if not value:
        return None
    stored_purpose, _, user_id = str(value).partition("|")
    if stored_purpose != purpose or not user_id:
        logger.warning("oauth state purpose mismatch: wanted %s got %s", purpose, stored_purpose)
        return None
    return user_id
