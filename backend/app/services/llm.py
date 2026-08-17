"""Provider-agnostic JSON-mode LLM calls.

Order of preference: Gemini Flash (free tier) → GPT-4o → Hugging Face
(open models via the HF router). All are asked for strict JSON; the caller
gets a parsed dict or an HTTPException.
"""
import json
import logging
import re

from fastapi import HTTPException, status

from app.config import settings

logger = logging.getLogger("kliptos.llm")

# Rolling alias — always resolves to the current flash model, so we never
# break when Google retires a specific version.
GEMINI_MODEL = "gemini-flash-latest"
OPENAI_MODEL = "gpt-4o"
HF_MODEL = "meta-llama/Llama-3.3-70B-Instruct"
HF_ROUTER_URL = "https://router.huggingface.co/v1/chat/completions"


def _lenient_json(text: str) -> dict:
    """Open models sometimes wrap JSON in code fences or prose — extract it."""
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fence:
        text = fence.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end > start:
            return json.loads(text[start:end + 1])
        raise


async def _gemini_json(system: str, user: str, temperature: float, api_key: str | None = None) -> dict:
    from google.genai import types

    from app.services.google_ai import gemini_client

    # Our own calls go via Vertex (Cloud billing, trial credits apply); a
    # creator's BYO key goes to the Developer API on their quota.
    client, _ = gemini_client(api_key)
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


async def _hf_json(system: str, user: str, temperature: float, api_key: str | None = None) -> dict:
    """Open models through the Hugging Face router (OpenAI-compatible)."""
    import httpx

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            HF_ROUTER_URL,
            headers={"Authorization": f"Bearer {api_key or settings.HUGGINGFACE_API_KEY}"},
            json={
                "model": HF_MODEL,
                "messages": [
                    {"role": "system", "content": system + "\nRespond with JSON only — no prose, no code fences."},
                    {"role": "user", "content": user},
                ],
                "temperature": temperature,
                "max_tokens": 4096,
            },
        )
        resp.raise_for_status()
        return _lenient_json(resp.json()["choices"][0]["message"]["content"])


VALID_MODELS = {"auto", "gemini", "openai", "huggingface"}

_PROVIDER_ORDER = ("gemini", "openai", "huggingface")
_PROVIDER_FUNCS = {"gemini": _gemini_json, "openai": _openai_json, "huggingface": _hf_json}
_PLATFORM_KEYS = {
    "gemini": lambda: settings.GEMINI_API_KEY,
    "openai": lambda: settings.OPENAI_API_KEY,
    "huggingface": lambda: settings.HUGGINGFACE_API_KEY,
}
_LABELS = {
    "gemini": f"Gemini ({GEMINI_MODEL})",
    "openai": f"OpenAI ({OPENAI_MODEL})",
    "huggingface": f"Open models (HF · {HF_MODEL.split('/')[-1]})",
}


def available_models(user_keys: dict[str, str] | None = None) -> list[dict]:
    """Model choices for the UI. A provider is offered when the platform has a
    key OR the user brought their own (own=True marks BYO usage)."""
    user_keys = user_keys or {}
    models = [{"key": "auto", "label": "Auto (best available)", "own": False}]
    for provider in _PROVIDER_ORDER:
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
    for provider in _PROVIDER_ORDER:
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

    from app.core.retry import with_retries

    last_error: Exception | None = None
    for name, own_key in providers:
        try:
            # Transient blips (503 overload, timeouts) retry within the SAME
            # provider before we fall through to the next one.
            result = await with_retries(
                lambda n=name, k=own_key: _PROVIDER_FUNCS[n](system, user, temperature, api_key=k),
                attempts=3, base_delay=2.0, label=f"llm:{name}",
            )
            if own_key is None:  # meter only platform-key usage — BYO is the user's spend
                from app.services.costs import track

                track(f"llm:{name}")
            return result
        except json.JSONDecodeError as exc:
            logger.warning("%s returned unparseable JSON: %s", name, exc)
            last_error = exc
        except Exception as exc:
            logger.warning("%s generation failed: %s", name, exc)
            last_error = exc

    logger.error("all LLM providers failed: %s", last_error)
    raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Script generation failed upstream")
