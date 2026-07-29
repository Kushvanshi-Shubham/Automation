"""BYO LLM keys: load/store a user's own provider keys (Fernet-encrypted)."""
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decrypt_token
from app.models.api_key import UserApiKey

logger = logging.getLogger("kliptos.user_keys")

SUPPORTED_PROVIDERS = {"gemini", "openai"}


async def get_user_keys(db: AsyncSession, user_id) -> dict[str, str]:
    """{provider: plaintext_key} for one user (undecryptable rows skipped)."""
    rows = (
        await db.execute(select(UserApiKey).where(UserApiKey.user_id == user_id))
    ).scalars().all()
    keys = {}
    for row in rows:
        plain = decrypt_token(row.key_encrypted)
        if plain:
            keys[row.provider] = plain
        else:
            logger.warning("undecryptable key for user %s provider %s", user_id, row.provider)
    return keys


async def validate_key(provider: str, key: str) -> bool:
    """Best-effort live check that a key actually works."""
    try:
        if provider == "gemini":
            from google import genai

            client = genai.Client(api_key=key)
            async for _ in await client.aio.models.list():
                break
            return True
        if provider == "openai":
            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=key, timeout=10)
            await client.models.list()
            return True
    except Exception as exc:
        logger.info("key validation failed for %s: %s", provider, exc)
        return False
    return False
