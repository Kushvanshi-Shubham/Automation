"""Provider-agnostic JSON-mode LLM calls.

Order of preference: Gemini 2.5 Flash (free tier) → GPT-4o (paid fallback).
Both are asked for strict JSON; the caller gets a parsed dict or an HTTPException.
"""
import json
import logging

from fastapi import HTTPException, status

from app.config import settings

logger = logging.getLogger("kliptos.llm")

# Rolling alias — always resolves to the current flash model, so we never
# break when Google retires a specific version.
GEMINI_MODEL = "gemini-flash-latest"
OPENAI_MODEL = "gpt-4o"


async def _gemini_json(system: str, user: str, temperature: float) -> dict:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    resp = await client.aio.models.generate_content(
        model=GEMINI_MODEL,
        contents=user,
        config=types.GenerateContentConfig(
            system_instruction=system,
            response_mime_type="application/json",
            temperature=temperature,
        ),
    )
    return json.loads(resp.text)


async def _openai_json(system: str, user: str, temperature: float) -> dict:
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    resp = await client.chat.completions.create(
        model=OPENAI_MODEL,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=temperature,
    )
    return json.loads(resp.choices[0].message.content)


VALID_MODELS = {"auto", "gemini", "openai"}


def available_models() -> list[dict]:
    """Model choices the UI can offer, based on configured keys."""
    models = [{"key": "auto", "label": "Auto (best available)"}]
    if settings.GEMINI_API_KEY:
        models.append({"key": "gemini", "label": f"Gemini ({GEMINI_MODEL})"})
    if settings.OPENAI_API_KEY:
        models.append({"key": "openai", "label": f"OpenAI ({OPENAI_MODEL})"})
    return models


async def generate_json(system: str, user: str, temperature: float = 0.8, model: str = "auto") -> dict:
    """Run against the requested provider ('gemini'/'openai'), or try each
    configured provider in order for 'auto'. Raises 502/503 on failure."""
    all_providers = []
    if settings.GEMINI_API_KEY:
        all_providers.append(("gemini", _gemini_json))
    if settings.OPENAI_API_KEY:
        all_providers.append(("openai", _openai_json))

    if model != "auto":
        providers = [(n, f) for n, f in all_providers if n == model]
        if not providers:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Model '{model}' is not configured on this server",
            )
    else:
        providers = all_providers

    if not providers:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No LLM provider configured (set GEMINI_API_KEY or OPENAI_API_KEY)",
        )

    last_error: Exception | None = None
    for name, call in providers:
        try:
            return await call(system, user, temperature)
        except json.JSONDecodeError as exc:
            logger.warning("%s returned unparseable JSON: %s", name, exc)
            last_error = exc
        except Exception as exc:
            logger.warning("%s generation failed: %s", name, exc)
            last_error = exc

    logger.error("all LLM providers failed: %s", last_error)
    raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Script generation failed upstream")
