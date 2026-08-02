"""Retry-with-backoff for external calls.

Every third-party API (Pexels, edge-tts, LLMs, Google) can blip — a render
must not fail because of one transient 5xx/timeout. Wrap the call; genuine
errors still surface after the attempts are exhausted.
"""
import asyncio
import logging
from typing import Awaitable, Callable, TypeVar

import httpx

logger = logging.getLogger("kliptos.retry")

T = TypeVar("T")

# Substrings that mark an exception as transient when it isn't an httpx error.
_TRANSIENT_MARKERS = ("503", "502", "429", "unavailable", "overloaded", "timeout", "timed out",
                      "temporarily", "connection reset", "connection aborted")


def is_transient(exc: Exception) -> bool:
    if isinstance(exc, (httpx.TimeoutException, httpx.TransportError)):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in (429, 500, 502, 503, 504)
    return any(m in str(exc).lower() for m in _TRANSIENT_MARKERS)


async def with_retries(
    fn: Callable[[], Awaitable[T]],
    *,
    attempts: int = 3,
    base_delay: float = 1.0,
    label: str = "external call",
) -> T:
    """Run fn; on a transient failure wait base_delay * 2^n and retry."""
    last: Exception | None = None
    for attempt in range(attempts):
        try:
            return await fn()
        except Exception as exc:
            if not is_transient(exc) or attempt == attempts - 1:
                raise
            last = exc
            delay = base_delay * (2 ** attempt)
            logger.warning("%s failed (attempt %d/%d): %s — retrying in %.1fs",
                           label, attempt + 1, attempts, str(exc)[:200], delay)
            await asyncio.sleep(delay)
    raise last  # pragma: no cover — loop always returns or raises


async def get_with_retries(client: httpx.AsyncClient, url: str, *, label: str, **kwargs) -> httpx.Response:
    """GET that retries transient failures AND retriable status codes."""
    async def _do() -> httpx.Response:
        resp = await client.get(url, **kwargs)
        if resp.status_code in (429, 500, 502, 503, 504):
            resp.raise_for_status()
        return resp

    return await with_retries(_do, label=label)
