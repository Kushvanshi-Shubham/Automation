"""Credit pricing derived from real cost — so a render can never be sold
below what it costs us.

One credit sells for CREDIT_PRICE_USD (₹499/50 ≈ $0.11). An engine's
credit cost is its true marginal cost times MARGIN, rounded up, floor 1.
When a provider's price changes, edit ENGINE_REAL_COST_USD only.
"""
import math

from app.config import settings

# Gross margin multiplier on metered work (2.0 = we keep half the sale).
MARGIN = 2.0

# Honest marginal cost per render, USD. Stock lanes are ~free (Pexels API,
# edge-tts, local Whisper) — the cost there is a fraction of a cent of
# LLM + compute. Premium lanes are what actually burn money.
ENGINE_REAL_COST_USD: dict[str, float] = {
    "pexels": 0.002,        # script tokens + ~3 min CPU + storage
    "stock": 0.002,
    "stock_image": 0.002,
    "ai_image": 0.20,       # ~6 slides of Gemini image generation
    # Not wired yet — costs recorded so pricing is right the day they land.
    "premium_voice": 0.15,  # ElevenLabs/Cartesia, ~60s
    "heygen_avatar": 0.50,  # HeyGen presenter, ~60s
    "veo_fast": 8.50,       # Veo Fast 60s
}


def credits_for_cost(cost_usd: float) -> int:
    """Credits to charge for work that costs us cost_usd."""
    price = settings.CREDIT_PRICE_USD or 0.10
    return max(1, math.ceil(cost_usd * MARGIN / price))


def engine_credit_cost(engine: str) -> int | None:
    """Credit price of a visual engine, or None if we don't offer it."""
    real = ENGINE_REAL_COST_USD.get(engine)
    if real is None:
        return None
    return credits_for_cost(real)


def price_table() -> dict[str, int]:
    """Every engine's credit price — for the UI and the owner's economics."""
    return {name: credits_for_cost(cost) for name, cost in ENGINE_REAL_COST_USD.items()}
