"""Usage counters + unit-cost model — the "are we making money?" layer.

Every external-service call bumps a monthly Redis counter (fail-silent,
sub-ms). The economics endpoint multiplies counts by UNIT_COSTS_USD and
compares against the credit ledger. No migrations, and the cost model is
one dict away from truth when a provider starts charging us.
"""
import logging
from datetime import datetime, timezone

from app.services.progress import _sync_client

logger = logging.getLogger("kliptos.costs")

# Honest CURRENT marginal cost per unit, USD. Update when a paid key lands.
UNIT_COSTS_USD: dict[str, float] = {
    "llm:gemini": 0.0,        # free tier
    "llm:openai": 0.02,       # GPT-4o, ~1.5K in / 1K out per script call
    "llm:huggingface": 0.001,  # HF free monthly credits, then pennies
    "pexels_clip": 0.0,       # free API
    "pexels_photo": 0.0,
    "tts_segment": 0.0,       # edge-tts, free
    "whisper_job": 0.0,       # local CPU
}

SERVICES = list(UNIT_COSTS_USD)


def _month_key(service: str, month: str | None = None) -> str:
    month = month or datetime.now(timezone.utc).strftime("%Y%m")
    return f"cost:{service}:{month}"


def track(service: str, n: float = 1.0) -> None:
    """Bump this month's usage counter. Never raises — metering must not
    break a render."""
    try:
        _sync_client.incrbyfloat(_month_key(service), n)
    except Exception as exc:
        logger.debug("cost tracking unavailable: %s", exc)


def month_usage(month: str | None = None) -> dict[str, float]:
    """{service: count} for one month (zeros included)."""
    out = {}
    for service in SERVICES:
        try:
            val = _sync_client.get(_month_key(service, month))
        except Exception:
            val = None
        out[service] = float(val) if val else 0.0
    return out


def estimated_cost_usd(usage: dict[str, float]) -> dict[str, float]:
    breakdown = {s: round(n * UNIT_COSTS_USD.get(s, 0.0), 4) for s, n in usage.items()}
    breakdown["total"] = round(sum(breakdown.values()), 4)
    return breakdown
