"""Per-user / per-IP rate limiting on expensive routes (Redis counters).

Fixed-window INCR+EXPIRE — coarse but Redis-5 compatible and cheap. Limits
live in LIMITS so tests (and ops) can tune them without touching routes.
Fails OPEN: if Redis is down, requests pass (availability over strictness)
— the event is logged loudly instead.
"""
import logging

from fastapi import Depends, HTTPException, Request, status

from app.middleware.auth import get_current_user
from app.models.user import User
from app.services import progress as progress_service

logger = logging.getLogger("kliptos.ratelimit")

# name -> (max requests, window seconds)
LIMITS: dict[str, tuple[int, int]] = {
    "script_generate": (10, 60),
    "pipeline_start": (8, 60),
    "media_upload": (5, 300),
    "clip_create": (10, 60),
    "topics_refresh": (2, 60),
    "auth_google": (15, 60),
    "series_create": (6, 60),
}


async def _check(key: str, name: str) -> None:
    from app.config import settings

    if not settings.RATE_LIMITS_ENABLED:
        return
    limit, window = LIMITS[name]
    client = progress_service.async_redis()
    try:
        count = await client.incr(key)
        if count == 1:
            await client.expire(key, window)
        if count > limit:
            ttl = await client.ttl(key)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Slow down — too many requests. Try again shortly.",
                headers={"Retry-After": str(max(ttl, 1))},
            )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("rate limiter unavailable (%s) — failing open: %s", name, exc)
    finally:
        try:
            await client.aclose()
        except Exception:
            pass


def rate_limit(name: str):
    """Per-authenticated-user limit (use as a route dependency)."""
    async def dep(current_user: User = Depends(get_current_user)) -> None:
        await _check(f"rl:{name}:{current_user.id}", name)

    return dep


def rate_limit_ip(name: str):
    """Per-IP limit for unauthenticated routes (login)."""
    async def dep(request: Request) -> None:
        # X-Forwarded-For first hop once we're behind a proxy in prod.
        fwd = request.headers.get("x-forwarded-for", "")
        ip = fwd.split(",")[0].strip() if fwd else (request.client.host if request.client else "unknown")
        await _check(f"rl:{name}:ip:{ip}", name)

    return dep
