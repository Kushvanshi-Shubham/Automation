"""HeyGen client — the AI-presenter lane (avatar + cloned voice).

SCAFFOLD STATUS: written against the HeyGen v2 API docs; not yet exercised
against a live account (no platform key — presenter is strictly BYO-key).
The render-pipeline integration lands once a real key can verify this
end to end. Flow: create video -> poll status -> download the mp4.

Avatar renders are the user's own HeyGen spend; Kliptos never stores the
resulting media anywhere except the user's normal render output dir.
"""
import asyncio
import logging
from pathlib import Path

import httpx

logger = logging.getLogger("kliptos.heygen")

API_BASE = "https://api.heygen.com"
GENERATE_URL = f"{API_BASE}/v2/video/generate"
STATUS_URL = f"{API_BASE}/v1/video_status.get"

POLL_SECONDS = 5.0
MAX_WAIT_SECONDS = 600.0  # avatar renders routinely take minutes
MAX_SCRIPT_CHARS = 1500


class HeyGenError(Exception):
    """User-facing presenter failure; message is safe to show."""


def _headers(api_key: str) -> dict:
    return {"X-Api-Key": api_key, "Content-Type": "application/json"}


async def list_avatars(api_key: str) -> list[dict]:
    """The user's avatars: [{avatar_id, avatar_name, preview_image_url}]."""
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(f"{API_BASE}/v2/avatars", headers=_headers(api_key))
    if resp.status_code != 200:
        raise HeyGenError("Couldn't reach HeyGen with that key — check it in Settings.")
    data = resp.json().get("data") or {}
    return [
        {
            "avatar_id": a.get("avatar_id"),
            "avatar_name": a.get("avatar_name"),
            "preview_image_url": a.get("preview_image_url"),
        }
        for a in (data.get("avatars") or [])
    ]


async def generate_avatar_video(
    script_text: str,
    avatar_id: str,
    voice_id: str,
    api_key: str,
    out_path: Path,
    width: int = 1080,
    height: int = 1920,
) -> Path:
    """Render an avatar video for script_text and download it to out_path.

    Blocking up to MAX_WAIT_SECONDS (polls). Raises HeyGenError with a
    plain-English message on every failure path.
    """
    text = (script_text or "").strip()[:MAX_SCRIPT_CHARS]
    if not text:
        raise HeyGenError("Nothing for the presenter to say — the script is empty.")

    payload = {
        "video_inputs": [
            {
                "character": {"type": "avatar", "avatar_id": avatar_id, "avatar_style": "normal"},
                "voice": {"type": "text", "input_text": text, "voice_id": voice_id},
            }
        ],
        "dimension": {"width": width, "height": height},
    }

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(GENERATE_URL, headers=_headers(api_key), json=payload)
        if resp.status_code != 200:
            detail = ""
            try:
                detail = (resp.json().get("error") or {}).get("message") or ""
            except Exception:
                pass
            raise HeyGenError(f"HeyGen rejected the render request ({resp.status_code}). {detail}".strip())
        video_id = ((resp.json().get("data") or {}).get("video_id")) or ""
        if not video_id:
            raise HeyGenError("HeyGen didn't return a video id — try again.")

        waited = 0.0
        video_url = None
        while waited < MAX_WAIT_SECONDS:
            await asyncio.sleep(POLL_SECONDS)
            waited += POLL_SECONDS
            status_resp = await client.get(
                STATUS_URL, headers=_headers(api_key), params={"video_id": video_id}
            )
            if status_resp.status_code != 200:
                continue  # transient; keep polling until the deadline
            data = status_resp.json().get("data") or {}
            state = data.get("status")
            if state == "completed":
                video_url = data.get("video_url")
                break
            if state == "failed":
                err = (data.get("error") or {}).get("message") or "unknown error"
                raise HeyGenError(f"HeyGen render failed: {err}")
        if not video_url:
            raise HeyGenError("HeyGen render timed out — check your HeyGen dashboard.")

        download = await client.get(video_url, timeout=120)
        if download.status_code != 200:
            raise HeyGenError("The finished avatar video couldn't be downloaded — try again.")
        out_path.write_bytes(download.content)

    logger.info("heygen avatar video downloaded: %s (%.0fs wait)", out_path, waited)
    return out_path
