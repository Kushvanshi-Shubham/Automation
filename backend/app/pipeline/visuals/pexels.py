"""Pexels stock video engine — free API, the S1 default visual source."""
import logging
from pathlib import Path

import httpx
from fastapi import HTTPException, status

from app.config import settings

logger = logging.getLogger("kliptos.pexels")

SEARCH_URL = "https://api.pexels.com/videos/search"
PHOTO_SEARCH_URL = "https://api.pexels.com/v1/search"
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


async def search_candidates(
    client: httpx.AsyncClient,
    query: str,
    media: str = "video",
    per_page: int = 8,
) -> list[dict]:
    """Thumbnail candidates for the per-scene media picker."""
    if not settings.PEXELS_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Pexels engine not configured (missing PEXELS_API_KEY)",
        )
    headers = {"Authorization": settings.PEXELS_API_KEY}
    if media == "photo":
        resp = await client.get(
            PHOTO_SEARCH_URL,
            params={"query": query, "orientation": "portrait", "per_page": per_page},
            headers=headers,
        )
        resp.raise_for_status()
        return [
            {"id": p["id"], "thumb": p.get("src", {}).get("medium"), "kind": "photo",
             "photographer": p.get("photographer")}
            for p in resp.json().get("photos", [])
            if p.get("src", {}).get("medium")
        ]
    resp = await client.get(
        SEARCH_URL,
        params={"query": query, "orientation": "portrait", "per_page": per_page, "size": "medium"},
        headers=headers,
    )
    resp.raise_for_status()
    out = []
    for v in resp.json().get("videos", []):
        if _pick_file(v) is None:
            continue
        out.append({"id": v["id"], "thumb": v.get("image"), "kind": "video",
                    "duration": v.get("duration"), "photographer": v.get("user", {}).get("name")})
    return out


async def fetch_clip_by_id(client: httpx.AsyncClient, video_id: int, out_path: Path) -> int:
    """Download a specific (user-pinned) Pexels video."""
    resp = await client.get(
        f"https://api.pexels.com/videos/videos/{video_id}",
        headers={"Authorization": settings.PEXELS_API_KEY},
    )
    resp.raise_for_status()
    chosen = _pick_file(resp.json())
    if chosen is None:
        raise RuntimeError(f"pinned pexels video {video_id} has no usable portrait file")
    download = await client.get(chosen["link"], follow_redirects=True)
    download.raise_for_status()
    out_path.write_bytes(download.content)
    logger.info("pexels pinned clip %s downloaded", video_id)
    return video_id


async def fetch_photo_by_id(client: httpx.AsyncClient, photo_id: int, out_path: Path) -> int:
    """Download a specific (user-pinned) Pexels photo."""
    resp = await client.get(
        f"https://api.pexels.com/v1/photos/{photo_id}",
        headers={"Authorization": settings.PEXELS_API_KEY},
    )
    resp.raise_for_status()
    src = resp.json().get("src", {})
    url = src.get("large2x") or src.get("portrait") or src.get("original")
    if not url:
        raise RuntimeError(f"pinned pexels photo {photo_id} has no usable source")
    download = await client.get(url, follow_redirects=True)
    download.raise_for_status()
    out_path.write_bytes(download.content)
    logger.info("pexels pinned photo %s downloaded", photo_id)
    return photo_id


async def fetch_photo(
    client: httpx.AsyncClient,
    query: str,
    out_path: Path,
    used_ids: set[int],
) -> int:
    """Download a portrait stock PHOTO matching the query (for image posts)."""
    if not settings.PEXELS_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Pexels engine not configured (missing PEXELS_API_KEY)",
        )
    resp = await client.get(
        PHOTO_SEARCH_URL,
        params={"query": query, "orientation": "portrait", "per_page": 10},
        headers={"Authorization": settings.PEXELS_API_KEY},
    )
    resp.raise_for_status()
    for photo in resp.json().get("photos", []):
        if photo["id"] in used_ids:
            continue
        url = photo.get("src", {}).get("large2x") or photo.get("src", {}).get("portrait")
        if not url:
            continue
        download = await client.get(url, follow_redirects=True)
        download.raise_for_status()
        out_path.write_bytes(download.content)
        used_ids.add(photo["id"])
        logger.info("pexels photo %s for query %r", photo["id"], query)
        return photo["id"]

    raise RuntimeError(f"no usable portrait photo found on Pexels for query: {query!r}")
