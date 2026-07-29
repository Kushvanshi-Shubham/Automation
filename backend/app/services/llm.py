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


async def _gemini_json(system: str, user: str, temperature: float, api_key: str | None = None) -> dict:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key or settings.GEMINI_API_KEY)
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


async def _openai_json(system: str, user: str, temperature: float, api_key: str | None = None) -> dict:
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=api_key or settings.OPENAI_API_KEY)
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

_PROVIDER_FUNCS = {"gemini": _gemini_json, "openai": _openai_json}
_PLATFORM_KEYS = {
    "gemini": lambda: settings.GEMINI_API_KEY,
    "openai": lambda: settings.OPENAI_API_KEY,
}
_LABELS = {"gemini": f"Gemini ({GEMINI_MODEL})", "openai": f"OpenAI ({OPENAI_MODEL})"}


def available_models(user_keys: dict[str, str] | None = None) -> list[dict]:
    """Model choices for the UI. A provider is offered when the platform has a
    key OR the user brought their own (own=True marks BYO usage)."""
    user_keys = user_keys or {}
    models = [{"key": "auto", "label": "Auto (best available)", "own": False}]
    for provider in ("gemini", "openai"):
        own = provider in user_keys
        if own or _PLATFORM_KEYS[provider]():
            label = _LABELS[provider] + (" — your key" if own else "")
            models.append({"key": provider, "label": label, "own": own})
    return models


async def generate_json(
    system: str,
    user: str,
    temperature: float = 0.8,
    model: str = "auto",
    user_keys: dict[str, str] | None = None,
) -> dict:
    """Run against the requested provider ('gemini'/'openai'), or try each
    available provider in order for 'auto'. A user's own key (BYO) takes
    precedence over the platform key for that provider. Raises 502/503."""
    user_keys = user_keys or {}
    all_providers: list[tuple[str, str | None]] = []
    for provider in ("gemini", "openai"):
        key = user_keys.get(provider) or _PLATFORM_KEYS[provider]()
        if key:
            all_providers.append((provider, user_keys.get(provider)))

    if model != "auto":
        providers = [(n, k) for n, k in all_providers if n == model]
        if not providers:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Model '{model}' is not configured (add your own key in Settings)",
            )
    else:
        providers = all_providers

    if not providers:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No LLM provider configured (set GEMINI_API_KEY or OPENAI_API_KEY)",
        )

    last_error: Exception | None = None
    for name, own_key in providers:
        try:
            return await _PROVIDER_FUNCS[name](system, user, temperature, api_key=own_key)
        except json.JSONDecodeError as exc:
            logger.warning("%s returned unparseable JSON: %s", name, exc)
            last_error = exc
        except Exception as exc:
            logger.warning("%s generation failed: %s", name, exc)
            last_error = exc

    logger.error("all LLM providers failed: %s", last_error)
    raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Script generation failed upstream")
