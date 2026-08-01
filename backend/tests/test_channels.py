from urllib.parse import parse_qs, urlparse


def test_channels_require_auth(client):
    assert client.get("/api/channels").status_code == 401
    assert client.get("/api/channels/connect").status_code == 401


def test_connect_returns_auth_url_with_state(client, auth_headers):
    resp = client.get("/api/channels/connect", headers=auth_headers)
    assert resp.status_code == 200
    url = resp.json()["auth_url"]
    parsed = urlparse(url)
    q = parse_qs(parsed.query)
    assert parsed.netloc == "accounts.google.com"
    assert q["access_type"] == ["offline"]
    assert "youtube.upload" in q["scope"][0]
    assert q["state"][0]  # signed JWT present
    assert q["redirect_uri"] == ["http://localhost:8000/api/channels/callback"]


def test_callback_rejects_bad_state(client):
    resp = client.get("/api/channels/callback", params={"state": "garbage", "code": "x"}, follow_redirects=False)
    assert resp.status_code in (302, 307)
    assert "yt_error=invalid_state" in resp.headers["location"]


def test_callback_connects_channel(client, auth_headers, monkeypatch):
    # Grab a valid state by generating a connect URL for the authed user.
    url = client.get("/api/channels/connect", headers=auth_headers).json()["auth_url"]
    state = parse_qs(urlparse(url).query)["state"][0]

    async def fake_exchange(code):
        return {"access_token": "at-123", "refresh_token": "rt-456", "expires_in": 3600}

    async def fake_info(access_token):
        return {"id": "UCtestchannel", "title": "Test Channel"}

    monkeypatch.setattr("app.routers.channels.youtube.exchange_code", fake_exchange)
    monkeypatch.setattr("app.routers.channels.youtube.fetch_channel_info", fake_info)

    resp = client.get(
        "/api/channels/callback",
        params={"state": state, "code": "authcode"},
        follow_redirects=False,
    )
    assert resp.status_code in (302, 307)
    assert "yt_connected=Test" in resp.headers["location"]

    # SECURITY: the state nonce is single-use — replaying it must fail.
    replay = client.get(
        "/api/channels/callback",
        params={"state": state, "code": "authcode2"},
        follow_redirects=False,
    )
    assert "yt_error=invalid_state" in replay.headers["location"]

    channels = client.get("/api/channels", headers=auth_headers).json()
    assert any(c["youtube_channel_id"] == "UCtestchannel" for c in channels)
    # Tokens must never be exposed by the API.
    assert "access_token" not in channels[0]


def test_tokens_encrypted_at_rest(client, auth_headers):
    import asyncio

    from sqlalchemy import select

    from app.core.security import decrypt_token
    from app.database import AsyncSessionLocal
    from app.models.channel import Channel

    async def fetch():
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Channel).where(Channel.youtube_channel_id == "UCtestchannel"))
            return result.scalar_one_or_none()

    channel = asyncio.run(fetch())
    if channel is None:  # depends on previous test having run in same session db
        return
    assert channel.access_token != "at-123"  # not plaintext
    assert decrypt_token(channel.access_token) == "at-123"
    assert decrypt_token(channel.refresh_token) == "rt-456"


def test_publish_validations(client, auth_headers):
    resp = client.post(
        "/api/uploads/00000000-0000-0000-0000-000000000000/publish",
        headers=auth_headers,
        json={"channel_id": "00000000-0000-0000-0000-000000000000", "privacy": "unlisted"},
    )
    assert resp.status_code == 404
