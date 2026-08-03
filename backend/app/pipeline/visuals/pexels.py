"""Pexels stock video engine — free API, the S1 default visual source."""
import logging
from pathlib import Path

import httpx
from fastapi import HTTPException, status

from app.config import settings
from app.core.retry import get_with_retries
from app.services.costs import track

logger = logging.getLogger("kliptos.pexels")

SEARCH_URL = "https://api.pexels.com/videos/search"
PHOTO_SEARCH_URL = "https://api.pexels.com/v1/search"
TARGET_W, TARGET_H = 1080, 1920


def _orientation_ok(f: dict, orientation: str) -> bool:
    w, h = f.get("width") or 0, f.get("height") or 0
    if orientation == "portrait":
        return h > w
    if orientation == "landscape":
        return w > h
    return True  # square target: any orientation crops fine


def _pick_file(video: dict, target_w: int = TARGET_W, target_h: int = TARGET_H,
               orientation: str = "portrait") -> dict | None:
    """Best mp4 rendition for the target frame: smallest that still covers it.
    Prefers matching orientation but falls back to any decent rendition —
    the crop filter covers any input, orientation only affects framing."""
    mp4s = [
        f for f in video.get("video_files", [])
        if f.get("file_type") == "video/mp4"
        and max(f.get("height") or 0, f.get("width") or 0) >= 1280
    ]
    candidates = [f for f in mp4s if _orientation_ok(f, orientation)] or mp4s
    if not candidates:
        return None
    covering = [f for f in candidates if f["width"] >= target_w and f["height"] >= target_h]
    pool = covering or candidates
    return min(pool, key=lambda f: f["width"] * f["height"])


async def fetch_clip(
    client: httpx.AsyncClient,
    query: str,
    out_path: Path,
    used_ids: set[int],
    orientation: str = "portrait",
    target_w: int = TARGET_W,
    target_h: int = TARGET_H,
) -> int:
    """Search Pexels for a clip matching the query + target orientation.
    Returns the pexels video id (recorded in used_ids to avoid repeats)."""
    if not settings.PEXELS_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Pexels engine not configured (missing PEXELS_API_KEY)",
        )
    resp = await get_with_retries(
        client, SEARCH_URL, label="pexels search",
        params={"query": query, "orientation": orientation, "per_page": 10, "size": "medium"},
        headers={"Authorization": settings.PEXELS_API_KEY},
    )
    resp.raise_for_status()
    videos = resp.json().get("videos", [])

    for video in videos:
        if video["id"] in used_ids:
            continue
        chosen = _pick_file(video, target_w, target_h, orientation)
        if chosen is None:
            continue
        download = await get_with_retries(client, chosen["link"], label="pexels download", follow_redirects=True)
        download.raise_for_status()
        out_path.write_bytes(download.content)
        used_ids.add(video["id"])
        logger.info("pexels clip %s (%dx%d) for query %r", video["id"], chosen["width"], chosen["height"], query)
        track("pexels_clip")
        return video["id"]

    raise RuntimeError(f"no usable {orientation} clip found on Pexels for query: {query!r}")


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
        resp = await get_with_retries(
            client, PHOTO_SEARCH_URL, label="pexels photo search",
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
    resp = await get_with_retries(
        client, SEARCH_URL, label="pexels search",
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


async def fetch_clip_by_id(
    client: httpx.AsyncClient,
    video_id: int,
    out_path: Path,
    orientation: str = "portrait",
    target_w: int = TARGET_W,
    target_h: int = TARGET_H,
) -> int:
    """Download a specific (user-pinned) Pexels video."""
    resp = await get_with_retries(
        client, f"https://api.pexels.com/videos/videos/{video_id}", label="pexels video detail",
        headers={"Authorization": settings.PEXELS_API_KEY},
    )
    resp.raise_for_status()
    chosen = _pick_file(resp.json(), target_w, target_h, orientation)
    if chosen is None:
        raise RuntimeError(f"pinned pexels video {video_id} has no usable file")
    download = await get_with_retries(client, chosen["link"], label="pexels download", follow_redirects=True)
    download.raise_for_status()
    out_path.write_bytes(download.content)
    logger.info("pexels pinned clip %s downloaded", video_id)
    track("pexels_clip")
    return video_id


async def fetch_photo_by_id(client: httpx.AsyncClient, photo_id: int, out_path: Path) -> int:
    """Download a specific (user-pinned) Pexels photo."""
    resp = await get_with_retries(
        client, f"https://api.pexels.com/v1/photos/{photo_id}", label="pexels photo detail",
        headers={"Authorization": settings.PEXELS_API_KEY},
    )
    resp.raise_for_status()
    src = resp.json().get("src", {})
    url = src.get("large2x") or src.get("portrait") or src.get("original")
    if not url:
        raise RuntimeError(f"pinned pexels photo {photo_id} has no usable source")
    download = await get_with_retries(client, url, label="pexels download", follow_redirects=True)
    download.raise_for_status()
    out_path.write_bytes(download.content)
    logger.info("pexels pinned photo %s downloaded", photo_id)
    track("pexels_photo")
    return photo_id


async def fetch_photo(
    client: httpx.AsyncClient,
    query: str,
    out_path: Path,
    used_ids: set[int],
    orientation: str = "portrait",
) -> int:
    """Download a stock PHOTO matching the query (for image posts)."""
    if not settings.PEXELS_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Pexels engine not configured (missing PEXELS_API_KEY)",
        )
    resp = await get_with_retries(
        client, PHOTO_SEARCH_URL, label="pexels photo search",
        params={"query": query, "orientation": orientation, "per_page": 10},
        headers={"Authorization": settings.PEXELS_API_KEY},
    )
    resp.raise_for_status()
    for photo in resp.json().get("photos", []):
        if photo["id"] in used_ids:
            continue
        url = photo.get("src", {}).get("large2x") or photo.get("src", {}).get("portrait")
        if not url:
            continue
        download = await get_with_retries(client, url, label="pexels download", follow_redirects=True)
        download.raise_for_status()
        out_path.write_bytes(download.content)
        used_ids.add(photo["id"])
        logger.info("pexels photo %s for query %r", photo["id"], query)
        track("pexels_photo")
        return photo["id"]

    raise RuntimeError(f"no usable {orientation} photo found on Pexels for query: {query!r}")
