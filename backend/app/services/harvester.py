"""Topic harvester: pulls trending topics from Google Trends and Reddit.

Both sources work WITHOUT credentials:
- Google Trends: public RSS feed
- Reddit: public JSON API (rate-limited; praw + creds can replace later)

Hooks are template-generated for now; LLM-written hooks land with the
script-studio milestone (needs OPENAI_API_KEY).
"""
import hashlib
import logging
import math
import re
import xml.etree.ElementTree as ET

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.retry import get_with_retries
from app.models.topic import Topic
from app.services.niches import GENERAL, NICHES, normalize

logger = logging.getLogger("kliptos.harvester")

USER_AGENT = "Kliptos/1.0 (trend discovery; contact: admin@kliptos.app)"
# Public RSS feeds (Google Trends) treat server-shaped agents differently.
BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)
TRENDS_RSS_URL = "https://trends.google.com/trending/rss?geo={geo}"
REDDIT_TOKEN_URL = "https://www.reddit.com/api/v1/access_token"
REDDIT_TOP_URL = "https://oauth.reddit.com/r/{sub}/top?t=day&limit={limit}"
YOUTUBE_TRENDING_URL = "https://www.googleapis.com/youtube/v3/videos"

DEFAULT_SUBREDDITS = [
    "interestingasfuck",
    "todayilearned",
    "Damnthatsinteresting",
    "technology",
    "space",
]

_HT_NS = "{https://trends.google.com/trending/rss}"


def content_hash(title: str) -> str:
    return hashlib.sha256(title.strip().lower().encode()).hexdigest()


def _keywords_from_title(title: str, limit: int = 4) -> list[str]:
    words = re.findall(r"[A-Za-z][A-Za-z0-9'-]{3,}", title)
    seen: list[str] = []
    for w in words:
        cap = w[0].upper() + w[1:]
        if cap not in seen:
            seen.append(cap)
        if len(seen) >= limit:
            break
    return seen


def _hook_for(title: str) -> str:
    return f"Everyone is talking about {title} right now — here's what most people missed."


def _score_from_traffic(traffic_text: str) -> float:
    """'200+' / '1,000+' → log-scaled 0–100."""
    digits = re.sub(r"[^\d]", "", traffic_text or "")
    traffic = int(digits) if digits else 100
    return round(min(99.0, 35.0 + 12.0 * math.log10(max(traffic, 10))), 1)


def _score_from_upvotes(ups: int) -> float:
    return round(min(99.0, 20.0 + 16.0 * math.log10(max(ups, 10))), 1)


async def fetch_google_trends(client: httpx.AsyncClient, geo: str = "US") -> list[dict]:
    # Google throttles datacenter IPs on this feed, so retry rather than
    # dropping the whole source on one 429. A browser UA fares better than
    # a bot-shaped one from a server.
    resp = await get_with_retries(
        client,
        TRENDS_RSS_URL.format(geo=geo),
        headers={"User-Agent": BROWSER_UA},
        label="google-trends",
    )
    resp.raise_for_status()
    root = ET.fromstring(resp.text)
    items = []
    for item in root.iter("item"):
        title = (item.findtext("title") or "").strip()
        if not title:
            continue
        traffic = item.findtext(f"{_HT_NS}approx_traffic") or ""
        items.append(
            {
                "title": title,
                "source": "trends",
                "score": _score_from_traffic(traffic),
                "keywords": _keywords_from_title(title),
                "hook_text": _hook_for(title),
            }
        )
    return items


async def _reddit_app_token(client: httpx.AsyncClient) -> str | None:
    """App-only OAuth token (client_credentials). Reddit blocks unauthenticated
    JSON API calls from servers, so credentials are required for this source."""
    if not (settings.REDDIT_CLIENT_ID and settings.REDDIT_CLIENT_SECRET):
        return None
    resp = await client.post(
        REDDIT_TOKEN_URL,
        auth=(settings.REDDIT_CLIENT_ID, settings.REDDIT_CLIENT_SECRET),
        data={"grant_type": "client_credentials"},
        headers={"User-Agent": settings.REDDIT_USER_AGENT or USER_AGENT},
    )
    resp.raise_for_status()
    return resp.json().get("access_token")


async def fetch_reddit_trending(
    client: httpx.AsyncClient,
    subreddits: list[str] | None = None,
    limit_per_sub: int = 8,
) -> list[dict]:
    token = await _reddit_app_token(client)
    if token is None:
        logger.info("reddit source skipped: REDDIT_CLIENT_ID/SECRET not configured")
        return []
    headers = {
        "User-Agent": settings.REDDIT_USER_AGENT or USER_AGENT,
        "Authorization": f"Bearer {token}",
    }
    items = []
    for sub in subreddits or DEFAULT_SUBREDDITS:
        try:
            resp = await client.get(
                REDDIT_TOP_URL.format(sub=sub, limit=limit_per_sub),
                headers=headers,
                follow_redirects=True,
            )
            resp.raise_for_status()
            posts = resp.json().get("data", {}).get("children", [])
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning("reddit fetch failed for r/%s: %s", sub, exc)
            continue
        for post in posts:
            data = post.get("data", {})
            title = (data.get("title") or "").strip()
            if not title or data.get("over_18"):
                continue
            items.append(
                {
                    "title": title,
                    "source": "reddit",
                    "score": _score_from_upvotes(int(data.get("ups", 0))),
                    "keywords": _keywords_from_title(title) + [sub],
                    "hook_text": _hook_for(title),
                }
            )
    return items


async def _fetch_youtube_chart(
    client: httpx.AsyncClient,
    region: str,
    limit: int,
    category_key: str | None = None,
) -> list[dict]:
    params = {
        "part": "snippet,statistics",
        "chart": "mostPopular",
        "regionCode": region,
        "maxResults": limit,
        "key": settings.YOUTUBE_API_KEY,
    }
    if category_key:
        params["videoCategoryId"] = NICHES[category_key]["yt_category_id"]
    resp = await client.get(YOUTUBE_TRENDING_URL, params=params)
    resp.raise_for_status()
    items = []
    for video in resp.json().get("items", []):
        snippet = video.get("snippet", {})
        title = (snippet.get("title") or "").strip()
        if not title:
            continue
        views = int(video.get("statistics", {}).get("viewCount", 0))
        keywords = _keywords_from_title(title)
        category_tags = (snippet.get("tags") or [])[:2]
        items.append(
            {
                "title": title,
                "source": "youtube",
                "category": category_key or GENERAL,
                "score": round(min(99.0, 15.0 + 12.0 * math.log10(max(views, 1000))), 1),
                "keywords": keywords + [t for t in category_tags if t not in keywords],
                "hook_text": _hook_for(title),
            }
        )
    return items


async def fetch_youtube_trending(
    client: httpx.AsyncClient,
    region: str = "US",
    limit: int = 15,
) -> list[dict]:
    """Overall chart + one chart per niche (videoCategoryId). Each call costs
    1 quota unit. Categories without chart support in the region are skipped."""
    if not settings.YOUTUBE_API_KEY:
        logger.info("youtube source skipped: YOUTUBE_API_KEY not configured")
        return []
    # Niche charts FIRST: dedupe keeps the first occurrence, so a video that is
    # also on the overall chart retains its specific niche.
    items: list[dict] = []
    for key in NICHES:
        try:
            items += await _fetch_youtube_chart(client, region, 8, category_key=key)
        except httpx.HTTPStatusError as exc:
            # 400 = category has no mostPopular chart here — expected for some
            logger.info("youtube niche %s skipped: HTTP %s", key, exc.response.status_code)
    items += await _fetch_youtube_chart(client, region, limit)
    return items


async def classify_titles(titles: list[str]) -> list[str]:
    """LLM-classify uncategorized titles into niches; 'general' on any failure."""
    if not titles:
        return []
    from app.services.llm import generate_json

    allowed = ", ".join(sorted(NICHES))
    numbered = "\n".join(f"{i}. {t}" for i, t in enumerate(titles))
    try:
        data = await generate_json(
            system=(
                "You classify video topics into exactly one category each. "
                f"Allowed categories: {allowed}, general. "
                'Respond ONLY with JSON: {"categories": ["gaming", ...]} — one entry per input, same order.'
            ),
            user=f"Classify these {len(titles)} topics:\n{numbered}",
            temperature=0.0,
        )
        cats = data.get("categories", [])
    except Exception as exc:
        logger.warning("classification failed, defaulting to general: %s", exc)
        return [GENERAL] * len(titles)
    result = [normalize(c) for c in cats]
    # pad/trim defensively — LLM may miscount
    result += [GENERAL] * (len(titles) - len(result))
    return result[: len(titles)]


def _format_prompt() -> tuple[set, str]:
    """Recommendation targets come straight from the format registry, so a new
    format automatically becomes recommendable."""
    from app.services.formats import FORMATS

    keys = {k for k, f in FORMATS.items() if f["available"]}
    lines = "\n".join(f"- {k}: {FORMATS[k]['when']}" for k in FORMATS if k in keys)
    system = (
        "You are a short-form content strategist. For each trending topic, recommend the SINGLE "
        "best format from this catalog:\n"
        f"{lines}\n"
        'Respond ONLY with JSON: {"formats": [{"format": "<key>", "why": "<max 8 words>"}, ...]} '
        "— one entry per input, same order."
    )
    return keys, system


async def recommend_formats(titles: list[str]) -> list[dict]:
    """LLM-recommend the best FORMAT (pipeline recipe key) per topic;
    empty dicts on failure."""
    if not titles:
        return []
    from app.services.llm import generate_json

    valid, system = _format_prompt()
    numbered = "\n".join(f"{i}. {t}" for i, t in enumerate(titles))
    try:
        data = await generate_json(
            system=system,
            user=f"Recommend formats for these {len(titles)} trending topics:\n{numbered}",
            temperature=0.0,
        )
        raw = data.get("formats", [])
    except Exception as exc:
        logger.warning("format recommendation failed: %s", exc)
        return [{}] * len(titles)
    out = []
    for item in raw[: len(titles)]:
        fmt = (item or {}).get("format", "")
        if fmt in valid:
            out.append({"best_format": fmt, "format_reason": str((item or {}).get("why", ""))[:120]})
        else:
            out.append({})
    out += [{}] * (len(titles) - len(out))
    return out


async def harvest_topics(db: AsyncSession, geo: str = "US") -> dict:
    """Fetch all sources, dedupe against DB by content hash, insert new topics."""
    async with httpx.AsyncClient(timeout=15) as client:
        results: list[dict] = []
        errors: dict[str, str] = {}
        try:
            results += await fetch_google_trends(client, geo)
        except Exception as exc:
            logger.warning("google trends fetch failed: %s", exc)
            errors["trends"] = str(exc)
        try:
            results += await fetch_reddit_trending(client)
        except Exception as exc:
            logger.warning("reddit fetch failed: %s", exc)
            errors["reddit"] = str(exc)
        try:
            results += await fetch_youtube_trending(client, region=geo)
        except Exception as exc:
            logger.warning("youtube fetch failed: %s", exc)
            errors["youtube"] = str(exc)

    # LLM-classify items that arrived without a category (Trends RSS, Reddit).
    unclassified = [r for r in results if not r.get("category")]
    if unclassified:
        categories = await classify_titles([r["title"] for r in unclassified])
        for r, cat in zip(unclassified, categories):
            r["category"] = cat

    # Recommend the best output format per topic (the "right trend → right
    # short" moat). Failure-safe: recommendation fields just stay empty.
    formats = await recommend_formats([r["title"] for r in results])
    for r, rec in zip(results, formats):
        r.update(rec)

    hashes = [content_hash(r["title"]) for r in results]
    existing = set(
        (await db.execute(select(Topic.content_hash).where(Topic.content_hash.in_(hashes)))).scalars()
    )

    added = 0
    seen_this_run: set[str] = set()
    for r, h in zip(results, hashes):
        if h in existing or h in seen_this_run:
            continue
        seen_this_run.add(h)
        db.add(Topic(content_hash=h, **r))
        added += 1

    await db.commit()
    return {"fetched": len(results), "added": added, "errors": errors}
