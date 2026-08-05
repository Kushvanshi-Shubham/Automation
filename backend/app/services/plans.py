"""What each plan actually gives — the difference Pro is selling.

Most of these levers cost us nothing to serve (watermark, resolution,
duration, priority, brand kit); the expensive ones (premium voice, AI
video engines) are metered in credits instead — see services/credits.py.

ENFORCEMENT: off until billing is live (PLAN_ENFORCEMENT_ENABLED). While
off, every signed-in user is served Pro-level features so the beta isn't
crippled by a paywall nobody can pay through yet. Admins always get
Studio so the owner can exercise every lane.
"""
from fastapi import HTTPException, status

from app.config import settings

FREE = "free"
PRO = "pro"
STUDIO = "studio"

PLANS: dict[str, dict] = {
    FREE: {
        "label": "Free",
        "watermark": True,
        "max_height": 1280,          # 720p-class render
        "max_duration_seconds": 45,
        "publish": False,            # download and post it yourself
        "standing_orders": False,
        "teach_style": False,
        "own_footage": False,        # upload + clip yes; scenes from footage no
        "premium_engines": False,
        "brand_kit": False,
        "priority": 0,
    },
    PRO: {
        "label": "Pro",
        "watermark": False,
        "max_height": 1920,          # full 1080x1920
        "max_duration_seconds": 180,
        "publish": True,
        "standing_orders": True,
        "teach_style": True,
        "own_footage": True,
        "premium_engines": False,    # available, but Studio gets them included
        "brand_kit": True,
        "priority": 1,
    },
    STUDIO: {
        "label": "Studio",
        "watermark": False,
        "max_height": 1920,
        "max_duration_seconds": 180,
        "publish": True,
        "standing_orders": True,
        "teach_style": True,
        "own_footage": True,
        "premium_engines": True,
        "brand_kit": True,
        "priority": 2,
    },
}

# What a locked feature says when someone hits it. Plain words + the reason.
UPSELL: dict[str, str] = {
    "publish": "Publishing to YouTube is a Pro feature — on Free you can still download the video and post it yourself.",
    "standing_orders": "Standing orders (autopilot) are a Pro feature.",
    "teach_style": "Teaching Kliptos your own style is a Pro feature.",
    "own_footage": "Using your own footage inside a scene is a Pro feature — on Free you can still cut clips from it.",
    "premium_engines": "Premium AI video engines are a Studio feature.",
    "brand_kit": "Your logo and brand colours are a Pro feature.",
}


def effective_plan(user) -> str:
    """The plan we actually serve this user."""
    admins = {e.lower() for e in (settings.ADMIN_EMAILS or [])}
    if (user.email or "").lower() in admins:
        return STUDIO
    if not settings.PLAN_ENFORCEMENT_ENABLED:
        return PRO  # beta: nobody is paywalled before billing exists
    return user.plan if user.plan in PLANS else FREE


def features(user) -> dict:
    return PLANS[effective_plan(user)]


def allows(user, feature: str) -> bool:
    return bool(features(user).get(feature))


def require(user, feature: str) -> None:
    """Raise a 402 with a plain-English upsell if this plan lacks the feature."""
    if allows(user, feature):
        return
    raise HTTPException(
        status_code=status.HTTP_402_PAYMENT_REQUIRED,
        detail=UPSELL.get(feature, "That feature needs a paid plan."),
    )


def tier_dimensions(width: int, height: int, max_height: int) -> tuple[int, int]:
    """Scale a render down to the plan's ceiling, keeping the aspect and
    even dimensions (h264 requires even width/height)."""
    if height <= max_height:
        return width, height
    scale = max_height / height
    w = max(2, int(round(width * scale / 2)) * 2)
    h = max(2, int(round(height * scale / 2)) * 2)
    return w, h
