"""Reference-text extraction from user-pasted links.

Reference-text extraction only — Kliptos never downloads media from
third-party links (creator-owned uploads are the only media ingest).

YouTube links resolve through the official Data API (title, channel,
description, tags); every other link is fetched as a readable page and
reduced to plain text. All outbound fetches pass an SSRF guard first.
"""
import asyncio
import html as html_lib
import ipaddress
import logging
import re
import socket
from urllib.parse import parse_qs, urljoin, urlsplit

import httpx

from app.config import settings
from app.core.retry import get_with_retries

logger = logging.getLogger("kliptos.link_ingest")

USER_AGENT = "Mozilla/5.0 (compatible; KliptosBot/1.0)"
YOUTUBE_VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"
YOUTUBE_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be", "www.youtu.be"}

MAX_TEXT_CHARS = 6000
MAX_TITLE_CHARS = 200
MAX_BODY_BYTES = 2 * 1024 * 1024  # never buffer unbounded bodies
MAX_REDIRECTS = 3
_ALLOWED_PORTS = {80, 443, 8080}
_REDIRECT_CODES = {301, 302, 303, 307, 308}
_READABLE_TYPES = ("text/html", "text/plain", "application/xhtml")

_VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")
_TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
_OG_TITLE_RE = re.compile(
    r"<meta\b[^>]*property=[\"']og:title[\"'][^>]*content=[\"']([^\"']*)[\"']"
    r"|<meta\b[^>]*content=[\"']([^\"']*)[\"'][^>]*property=[\"']og:title[\"']",
    re.IGNORECASE | re.DOTALL,
)
_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
_DROP_BLOCKS_RE = re.compile(r"<(script|style|noscript|svg|head)\b.*?</\1\s*>", re.IGNORECASE | re.DOTALL)
_BLOCK_BREAK_RE = re.compile(r"</(?:p|div|li|h[1-6]|tr|section|blockquote)\s*>|<br\s*/?>", re.IGNORECASE)
_TAG_RE = re.compile(r"<[^>]+>")


class LinkIngestError(Exception):
    """User-facing extraction failure; message is safe to show."""


def _is_public_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    return not (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    )


async def _assert_public_url(url: str):
    """Validate a user-supplied URL against SSRF: scheme, credentials, port,
    and every resolved address must be public. Returns the urlsplit result."""
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https"):
        raise LinkIngestError("Only http(s) links are supported.")
    if parts.username is not None or parts.password is not None:
        raise LinkIngestError("Links with embedded credentials are not allowed.")
    host = parts.hostname
    if not host:
        raise LinkIngestError("That link is missing a hostname.")
    try:
        port = parts.port
    except ValueError:
        raise LinkIngestError("That link uses an unsupported port.")
    if port is not None and port not in _ALLOWED_PORTS:
        raise LinkIngestError("That link uses an unsupported port.")

    try:
        literal = ipaddress.ip_address(host)
    except ValueError:
        literal = None
    if literal is not None:
        if not _is_public_ip(literal):
            raise LinkIngestError("That link points to a private network address.")
        return parts

    try:
        infos = await asyncio.to_thread(
            socket.getaddrinfo, host, port or (443 if parts.scheme == "https" else 80)
        )
    except OSError:
        raise LinkIngestError("That link's server could not be reached.")
    if not infos:
        raise LinkIngestError("That link's server could not be reached.")
    for info in infos:
        addr = info[4][0]
        try:
            resolved = ipaddress.ip_address(addr.split("%")[0])
        except ValueError:
            raise LinkIngestError("That link's server could not be reached.")
        if not _is_public_ip(resolved):
            raise LinkIngestError("That link points to a private network address.")
    return parts


def _youtube_video_id(url: str) -> str | None:
    """Extract the 11-char video id from watch?v=, /shorts/, /embed/, youtu.be/."""
    parts = urlsplit(url)
    host = (parts.hostname or "").lower()
    if host not in YOUTUBE_HOSTS:
        return None
    path = parts.path or ""
    candidate = ""
    if host in ("youtu.be", "www.youtu.be"):
        candidate = path.strip("/").split("/")[0]
    elif path == "/watch":
        candidate = (parse_qs(parts.query).get("v") or [""])[0]
    else:
        m = re.match(r"^/(?:shorts|embed)/([^/?#]+)", path)
        if m:
            candidate = m.group(1)
    return candidate if _VIDEO_ID_RE.match(candidate or "") else None


def _cap_text(text: str) -> str:
    """Cap at MAX_TEXT_CHARS on a word boundary, appending an ellipsis."""
    if len(text) <= MAX_TEXT_CHARS:
        return text
    cut = text[:MAX_TEXT_CHARS]
    boundary = max(cut.rfind(" "), cut.rfind("\n"))
    if boundary > 0:
        cut = cut[:boundary]
    return cut.rstrip() + "…"


def _collapse(text: str) -> str:
    return " ".join(html_lib.unescape(text).split())


def _html_to_text(html: str) -> tuple[str, str]:
    """(title, text) from raw HTML — regex-based, no new dependencies."""
    title = ""
    m = _TITLE_RE.search(html)
    if m:
        title = _collapse(m.group(1))
    if not title:
        m = _OG_TITLE_RE.search(html)
        if m:
            title = _collapse(m.group(1) or m.group(2) or "")

    body = _COMMENT_RE.sub(" ", html)
    body = _DROP_BLOCKS_RE.sub(" ", body)
    # Prefer the (largest) <article>, else <main>, else <body>, else whole doc.
    for tag in ("article", "main", "body"):
        blocks = re.findall(rf"<{tag}\b[^>]*>(.*?)</{tag}\s*>", body, re.IGNORECASE | re.DOTALL)
        if blocks:
            body = max(blocks, key=len)
            break
    body = _BLOCK_BREAK_RE.sub("\n", body)
    body = _TAG_RE.sub(" ", body)

    lines = []
    for raw in body.splitlines():
        line = _collapse(raw)
        if len(line) >= 3:
            lines.append(line)
    return title, "\n".join(lines)


async def _extract_youtube(url: str, video_id: str) -> dict:
    if not settings.YOUTUBE_API_KEY:
        raise LinkIngestError("YouTube link support isn't configured on this server yet.")
    params = {"part": "snippet", "id": video_id, "key": settings.YOUTUBE_API_KEY}
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await get_with_retries(
                client, YOUTUBE_VIDEOS_URL, label="link_ingest:youtube", params=params
            )
            resp.raise_for_status()
            payload = resp.json()
    except httpx.HTTPError as exc:
        logger.warning("youtube metadata fetch failed for %s: %s", video_id, exc)
        raise LinkIngestError("Couldn't reach YouTube — try again in a moment.")

    items = payload.get("items") or []
    if not items:
        raise LinkIngestError("That YouTube video was not found (it may be private).")
    snippet = items[0].get("snippet", {})
    title = (snippet.get("title") or "").strip()

    pieces = [title]
    channel = (snippet.get("channelTitle") or "").strip()
    if channel:
        pieces.append(channel)
    description = (snippet.get("description") or "").strip()
    if description:
        pieces.append(description)
    tags = snippet.get("tags") or []
    if tags:
        pieces.append("Tags: " + ", ".join(tags))

    return {
        "kind": "youtube",
        "source_url": url,
        "title": title[:MAX_TITLE_CHARS],
        "text": _cap_text("\n".join(p for p in pieces if p)),
    }


async def _extract_article(url: str) -> dict:
    current = url
    async with httpx.AsyncClient(
        timeout=20, follow_redirects=False, headers={"User-Agent": USER_AGENT}
    ) as client:
        for hop in range(MAX_REDIRECTS + 1):
            try:
                async with client.stream("GET", current) as resp:
                    if resp.status_code in _REDIRECT_CODES:
                        location = resp.headers.get("location")
                        if not location:
                            raise LinkIngestError(
                                f"That page could not be fetched (HTTP {resp.status_code})."
                            )
                        if hop == MAX_REDIRECTS:
                            raise LinkIngestError("That link redirects too many times.")
                        current = urljoin(current, location)
                        await _assert_public_url(current)  # every hop re-guarded
                        continue
                    if not (200 <= resp.status_code < 300):
                        raise LinkIngestError(
                            f"That page could not be fetched (HTTP {resp.status_code})."
                        )
                    ctype = (resp.headers.get("content-type") or "").lower()
                    if not any(t in ctype for t in _READABLE_TYPES):
                        raise LinkIngestError("That link isn't a readable page.")

                    buf = bytearray()
                    async for chunk in resp.aiter_bytes():
                        buf += chunk
                        if len(buf) >= MAX_BODY_BYTES:
                            break
                    charset = resp.charset_encoding or "utf-8"
            except httpx.HTTPError as exc:
                logger.warning("article fetch failed for %s: %s", current, exc)
                raise LinkIngestError("That link's server could not be reached.")

            try:
                raw = bytes(buf[:MAX_BODY_BYTES]).decode(charset, errors="replace")
            except LookupError:  # bogus charset in the header
                raw = bytes(buf[:MAX_BODY_BYTES]).decode("utf-8", errors="replace")

            if "text/plain" in ctype:
                title = ""
                lines = [_collapse(line) for line in raw.splitlines()]
                text = "\n".join(line for line in lines if len(line) >= 3)
            else:
                title, text = _html_to_text(raw)

            text = _cap_text(text)
            if not text:
                raise LinkIngestError("Couldn't find readable text at that link.")
            return {
                "kind": "article",
                "source_url": url,
                "title": title[:MAX_TITLE_CHARS],
                "text": text,
            }
    raise LinkIngestError("That link redirects too many times.")  # pragma: no cover


async def extract_from_url(url: str) -> dict:
    """Return reference content for a pasted link.

    {"kind": "youtube"|"article", "source_url", "title", "text"} — raises
    LinkIngestError (message safe to show) on any failure; never returns None.
    """
    url = (url or "").strip()
    parts = await _assert_public_url(url)
    host = (parts.hostname or "").lower()
    if host in YOUTUBE_HOSTS:
        video_id = _youtube_video_id(url)
        if not video_id:
            raise LinkIngestError("Paste a link to a specific YouTube video.")
        return await _extract_youtube(url, video_id)
    return await _extract_article(url)
