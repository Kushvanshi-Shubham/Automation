"""BYO provider keys: load/store a user's own API keys (Fernet-encrypted).

LLM providers (gemini/openai/huggingface) feed the script lane; heygen is
the AI-presenter lane (avatar videos are always the user's own spend)."""
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decrypt_token
from app.models.api_key import UserApiKey

logger = logging.getLogger("kliptos.user_keys")

SUPPORTED_PROVIDERS = {"gemini", "openai", "huggingface", "heygen"}


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
        if provider == "huggingface":
            import httpx

            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    "https://huggingface.co/api/whoami-v2",
                    headers={"Authorization": f"Bearer {key}"},
                )
            return resp.status_code == 200
        if provider == "heygen":
            import httpx

            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    "https://api.heygen.com/v2/avatars",
                    headers={"X-Api-Key": key},
                )
            return resp.status_code == 200
    except Exception as exc:
        logger.info("key validation failed for %s: %s", provider, exc)
        return False
    return False
