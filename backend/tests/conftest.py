import os

from cryptography.fernet import Fernet

# Must be set before any app import — Settings is instantiated at import time.
os.environ["SECRET_KEY"] = "test-secret-key-0123456789abcdef0123456789abcdef"
os.environ["TOKEN_ENCRYPTION_KEY"] = Fernet.generate_key().decode()
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_kliptos.db"
os.environ["GOOGLE_CLIENT_ID"] = "test-client-id.apps.googleusercontent.com"
# Isolate tests from real API keys that may exist in backend/.env
for _key in ("YOUTUBE_API_KEY", "GEMINI_API_KEY", "OPENAI_API_KEY", "PEXELS_API_KEY",
             "REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET"):
    os.environ[_key] = ""

import asyncio  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def create_schema():
    async def _create():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(_create())
    yield
    asyncio.run(engine.dispose())
    if os.path.exists("./test_kliptos.db"):
        os.remove("./test_kliptos.db")


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


GOOGLE_CLAIMS = {
    "sub": "google-user-123",
    "email": "creator@example.com",
    "email_verified": True,
    "name": "Test Creator",
    "picture": "https://example.com/avatar.png",
    "iss": "https://accounts.google.com",
}


@pytest.fixture()
def mock_google(monkeypatch):
    async def fake_verify(token: str):
        return GOOGLE_CLAIMS if token == "valid-google-token" else None

    monkeypatch.setattr("app.routers.auth.verify_google_id_token", fake_verify)


@pytest.fixture()
def auth_headers(client, mock_google):
    resp = client.post("/api/auth/google", json={"id_token": "valid-google-token"})
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
