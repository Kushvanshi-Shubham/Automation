import asyncio
import socket

import httpx
import pytest

from app.config import settings
from app.services import link_ingest
from app.services.link_ingest import (
    LinkIngestError,
    _assert_public_url,
    _youtube_video_id,
    extract_from_url,
)

VID = "dQw4w9WgXcQ"

# Deterministic DNS — tests must never hit the network.
_FAKE_DNS = {
    "example.com": "93.184.216.34",
    "youtube.com": "142.250.72.14",
    "www.youtube.com": "142.250.72.14",
    "m.youtube.com": "142.250.72.14",
    "youtu.be": "142.250.72.14",
    "localhost": "127.0.0.1",
}


def _fake_getaddrinfo(host, port, *args, **kwargs):
    ip = _FAKE_DNS.get(host)
    if ip is None:
        raise socket.gaierror(-2, f"unknown host {host}")
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (ip, port or 0))]


@pytest.fixture()
def fake_dns(monkeypatch):
    monkeypatch.setattr(socket, "getaddrinfo", _fake_getaddrinfo)


def _install_transport(monkeypatch, handler):
    """Route every AsyncClient the module builds through a MockTransport."""
    transport = httpx.MockTransport(handler)
    real_client = httpx.AsyncClient

    def factory(*args, **kwargs):
        kwargs["transport"] = transport
        return real_client(*args, **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", factory)


# ---------------------------------------------------------------- video id

def test_youtube_video_id_variants():
    assert _youtube_video_id(f"https://www.youtube.com/watch?v={VID}") == VID
    assert _youtube_video_id(f"https://youtu.be/{VID}") == VID
    assert _youtube_video_id(f"https://www.youtube.com/shorts/{VID}") == VID
    assert _youtube_video_id(f"https://www.youtube.com/embed/{VID}?autoplay=1") == VID
    assert _youtube_video_id(f"https://m.youtube.com/watch?v={VID}&t=42") == VID


def test_youtube_video_id_invalid():
    assert _youtube_video_id("https://www.youtube.com/feed/subscriptions") is None
    assert _youtube_video_id("https://www.youtube.com/watch?v=too-short") is None
    assert _youtube_video_id("https://www.youtube.com/watch") is None
    assert _youtube_video_id(f"https://example.com/watch?v={VID}") is None
    assert _youtube_video_id(f"https://youtu.be/{VID}xxxx") is None


# ---------------------------------------------------------------- SSRF guard

@pytest.mark.parametrize("url", [
    "ftp://example.com/file.txt",
    "http://localhost/",
    "http://127.0.0.1/",
    "http://192.168.1.1/",
    "http://10.0.0.1/x",
    "http://[::1]/",
    "http://user:pass@example.com/",
    "http://example.com:22/",
])
def test_assert_public_url_rejects(fake_dns, url):
    with pytest.raises(LinkIngestError):
        asyncio.run(_assert_public_url(url))


def test_assert_public_url_accepts_public_host(fake_dns):
    parts = asyncio.run(_assert_public_url("https://example.com/page"))
    assert parts.hostname == "example.com"


def test_assert_public_url_unresolvable(fake_dns):
    with pytest.raises(LinkIngestError, match="could not be reached"):
        asyncio.run(_assert_public_url("https://no-such-host.invalid/"))


# ---------------------------------------------------------------- youtube

def test_extract_youtube_happy_path(fake_dns, monkeypatch):
    monkeypatch.setattr(settings, "YOUTUBE_API_KEY", "test-yt-key")

    class FakeResponse:
        status_code = 200

        def raise_for_status(self):
            pass

        def json(self):
            return {"items": [{"snippet": {
                "title": "How Rockets Land",
                "channelTitle": "Space Channel",
                "description": "A deep dive into propulsive landing.",
                "tags": ["rockets", "space"],
            }}]}

    async def fake_get(client, url, *, label, **kwargs):
        assert "googleapis.com/youtube/v3/videos" in url
        assert kwargs["params"]["id"] == VID
        assert kwargs["params"]["key"] == "test-yt-key"
        return FakeResponse()

    monkeypatch.setattr(link_ingest, "get_with_retries", fake_get)
    out = asyncio.run(extract_from_url(f"https://www.youtube.com/watch?v={VID}"))
    assert out["kind"] == "youtube"
    assert out["source_url"] == f"https://www.youtube.com/watch?v={VID}"
    assert out["title"] == "How Rockets Land"
    assert "Space Channel" in out["text"]
    assert "propulsive landing" in out["text"]
    assert "Tags: rockets, space" in out["text"]


def test_extract_youtube_not_found(fake_dns, monkeypatch):
    monkeypatch.setattr(settings, "YOUTUBE_API_KEY", "test-yt-key")

    class FakeResponse:
        status_code = 200

        def raise_for_status(self):
            pass

        def json(self):
            return {"items": []}

    async def fake_get(client, url, *, label, **kwargs):
        return FakeResponse()

    monkeypatch.setattr(link_ingest, "get_with_retries", fake_get)
    with pytest.raises(LinkIngestError, match="not found"):
        asyncio.run(extract_from_url(f"https://youtu.be/{VID}"))


def test_extract_youtube_unconfigured(fake_dns):
    # conftest blanks YOUTUBE_API_KEY for the whole test env.
    with pytest.raises(LinkIngestError, match="isn't configured"):
        asyncio.run(extract_from_url(f"https://youtu.be/{VID}"))


def test_extract_youtube_requires_video_id(fake_dns):
    with pytest.raises(LinkIngestError, match="specific YouTube video"):
        asyncio.run(extract_from_url("https://www.youtube.com/feed/library"))


# ---------------------------------------------------------------- articles

HTML_PAGE = """
<html><head>
<title>The  Great &amp; Good Article</title>
<script>var secret = "SCRIPT_LEAK";</script>
<style>body { color: red; }</style>
</head>
<body>
<div>navigation junk outside the article</div>
<article>
  <h1>The Great Article</h1>
  <p>Rockets are &amp; will stay hard.</p>
  <p>Second paragraph with more detail.</p>
</article>
</body></html>
"""


def test_extract_article_happy_path(fake_dns, monkeypatch):
    def handler(request):
        assert request.headers["user-agent"] == "Mozilla/5.0 (compatible; KliptosBot/1.0)"
        return httpx.Response(
            200, headers={"content-type": "text/html; charset=utf-8"}, text=HTML_PAGE
        )

    _install_transport(monkeypatch, handler)
    out = asyncio.run(extract_from_url("https://example.com/post"))
    assert out["kind"] == "article"
    assert out["source_url"] == "https://example.com/post"
    assert out["title"] == "The Great & Good Article"
    assert "SCRIPT_LEAK" not in out["text"]
    assert "color: red" not in out["text"]
    assert "Rockets are & will stay hard." in out["text"]
    assert "Second paragraph with more detail." in out["text"]
    # <article> is preferred over surrounding <body> chrome
    assert "navigation junk" not in out["text"]


def test_extract_article_rejects_binary(fake_dns, monkeypatch):
    def handler(request):
        return httpx.Response(200, headers={"content-type": "image/png"}, content=b"\x89PNG")

    _install_transport(monkeypatch, handler)
    with pytest.raises(LinkIngestError, match="readable page"):
        asyncio.run(extract_from_url("https://example.com/logo.png"))


def test_extract_article_http_404(fake_dns, monkeypatch):
    def handler(request):
        return httpx.Response(404, headers={"content-type": "text/html"}, text="gone")

    _install_transport(monkeypatch, handler)
    with pytest.raises(LinkIngestError, match="HTTP 404"):
        asyncio.run(extract_from_url("https://example.com/missing"))


def test_extract_article_redirect_to_private_blocked(fake_dns, monkeypatch):
    def handler(request):
        return httpx.Response(302, headers={"location": "http://127.0.0.1/internal"})

    _install_transport(monkeypatch, handler)
    with pytest.raises(LinkIngestError, match="private network"):
        asyncio.run(extract_from_url("https://example.com/redirect"))


def test_extract_article_too_many_redirects(fake_dns, monkeypatch):
    def handler(request):
        return httpx.Response(302, headers={"location": "https://example.com/again"})

    _install_transport(monkeypatch, handler)
    with pytest.raises(LinkIngestError, match="redirects too many times"):
        asyncio.run(extract_from_url("https://example.com/loop"))


def test_extract_article_text_cap(fake_dns, monkeypatch):
    body = " ".join(f"word{i}" for i in range(2000))  # ~13k chars of text
    page = f"<html><head><title>Long</title></head><body><article><p>{body}</p></article></body></html>"

    def handler(request):
        return httpx.Response(200, headers={"content-type": "text/html"}, text=page)

    _install_transport(monkeypatch, handler)
    out = asyncio.run(extract_from_url("https://example.com/long"))
    assert len(out["text"]) <= 6001
    assert out["text"].endswith("…")
    assert out["text"].startswith("word0 word1")
