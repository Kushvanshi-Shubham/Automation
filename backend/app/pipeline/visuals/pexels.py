"""Pexels stock video engine — free API, the S1 default visual source."""
import logging
from pathlib import Path

import httpx
from fastapi import HTTPException, status

from app.config import settings

logger = logging.getLogger("kliptos.pexels")

SEARCH_URL = "https://api.pexels.com/videos/search"
TARGET_W, TARGET_H = 1080, 1920


def _pick_file(video: dict) -> dict | None:
    """Choose the best portrait mp4 rendition: smallest that still covers 1080x1920."""
    candidates = [
        f for f in video.get("video_files", [])
        if f.get("file_type") == "video/mp4"
        and (f.get("height") or 0) > (f.get("width") or 0)  # portrait
        and (f.get("height") or 0) >= 1280
    ]
    if not candidates:
        return None
    covering = [f for f in candidates if f["width"] >= TARGET_W and f["height"] >= TARGET_H]
    pool = covering or candidates
    return min(pool, key=lambda f: f["width"] * f["height"])


async def fetch_clip(
    client: httpx.AsyncClient,
    query: str,
    out_path: Path,
    used_ids: set[int],
) -> int:
    """Search Pexels for a portrait clip matching the query and download it.
    Returns the pexels video id (recorded in used_ids to avoid repeats)."""
    if not settings.PEXELS_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Pexels engine not configured (missing PEXELS_API_KEY)",
        )
    resp = await client.get(
        SEARCH_URL,
        params={"query": query, "orientation": "portrait", "per_page": 10, "size": "medium"},
        headers={"Authorization": settings.PEXELS_API_KEY},
    )
    resp.raise_for_status()
    videos = resp.json().get("videos", [])

    for video in videos:
        if video["id"] in used_ids:
            continue
        chosen = _pick_file(video)
        if chosen is None:
            continue
        download = await client.get(chosen["link"], follow_redirects=True)
        download.raise_for_status()
        out_path.write_bytes(download.content)
        used_ids.add(video["id"])
        logger.info("pexels clip %s (%dx%d) for query %r", video["id"], chosen["width"], chosen["height"], query)
        return video["id"]

    raise RuntimeError(f"no usable portrait clip found on Pexels for query: {query!r}")
