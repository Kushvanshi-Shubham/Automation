"""Niche/category definitions shared by harvester, API, and frontend.

yt_category_id maps to YouTube Data API videoCategoryId for per-niche
trending charts. Not every category supports the mostPopular chart in every
region — harvester skips unsupported ones gracefully.
"""

NICHES: dict[str, dict] = {
    "gaming": {"label": "Gaming", "yt_category_id": "20"},
    "entertainment": {"label": "Entertainment", "yt_category_id": "24"},
    "music": {"label": "Music", "yt_category_id": "10"},
    "sports": {"label": "Sports", "yt_category_id": "17"},
    "tech": {"label": "Tech & Science", "yt_category_id": "28"},
    "education": {"label": "Education", "yt_category_id": "27"},
    "news": {"label": "News & Politics", "yt_category_id": "25"},
    "comedy": {"label": "Comedy & Memes", "yt_category_id": "23"},
}

GENERAL = "general"

VALID_CATEGORIES = set(NICHES) | {GENERAL}


def normalize(category: str | None) -> str:
    c = (category or "").strip().lower()
    return c if c in VALID_CATEGORIES else GENERAL
