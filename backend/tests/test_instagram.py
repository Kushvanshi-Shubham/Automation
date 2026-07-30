from urllib.parse import parse_qs, urlparse


def test_ig_requires_auth(client):
    assert client.get("/api/instagram").status_code == 401


def test_ig_disabled_without_meta_app(client, auth_headers):
    # Test env has no META_APP_ID/SECRET
    assert client.get("/api/instagram/status", headers=auth_headers).json()["enabled"] is False
    assert client.get("/api/instagram/connect", headers=auth_headers).status_code == 503

    resp = client.post(
        "/api/uploads/00000000-0000-0000-0000-000000000000/publish-instagram",
        headers=auth_headers,
        json={"caption": "test"},
    )
    assert resp.status_code == 503


def test_ig_connect_flow_when_enabled(client, auth_headers, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "META_APP_ID", "123456")
    monkeypatch.setattr(settings, "META_APP_SECRET", "shhh")

    assert client.get("/api/instagram/status", headers=auth_headers).json()["enabled"] is True

    url = client.get("/api/instagram/connect", headers=auth_headers).json()["auth_url"]
    parsed = urlparse(url)
    q = parse_qs(parsed.query)
    assert parsed.netloc == "www.facebook.com"
    assert "instagram_content_publish" in q["scope"][0]
    state = q["state"][0]

    async def fake_exchange(code):
        return "long-lived-token-xyz"

    async def fake_discover(token):
        return {"ig_user_id": "1789", "username": "kliptos_test", "page_id": "42"}

    monkeypatch.setattr("app.routers.instagram.instagram.exchange_code", fake_exchange)
    monkeypatch.setattr("app.routers.instagram.instagram.discover_ig_account", fake_discover)

    resp = client.get(
        "/api/instagram/callback",
        params={"state": state, "code": "authcode"},
        follow_redirects=False,
    )
    assert resp.status_code in (302, 307)
    assert "ig_connected=kliptos_test" in resp.headers["location"]

    accounts = client.get("/api/instagram", headers=auth_headers).json()
    assert accounts[0]["username"] == "kliptos_test"
    assert "access_token" not in accounts[0]

    # token encrypted at rest
    import asyncio

    from sqlalchemy import select

    from app.core.security import decrypt_token
    from app.database import AsyncSessionLocal
    from app.models.ig_account import IgAccount

    async def fetch():
        async with AsyncSessionLocal() as db:
            return (await db.execute(select(IgAccount))).scalars().first()

    row = asyncio.run(fetch())
    assert row.access_token != "long-lived-token-xyz"
    assert decrypt_token(row.access_token) == "long-lived-token-xyz"


def test_ig_callback_bad_state(client, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "META_APP_ID", "123456")
    monkeypatch.setattr(settings, "META_APP_SECRET", "shhh")
    resp = client.get(
        "/api/instagram/callback",
        params={"state": "garbage", "code": "x"},
        follow_redirects=False,
    )
    assert "ig_error=invalid_state" in resp.headers["location"]
