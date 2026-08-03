import asyncio

import pytest


@pytest.fixture(autouse=True)
def cleanup_keys(client):
    """Keys are stored on the shared test user — remove them after every test
    so other test modules never see leftover BYO keys."""
    yield
    from sqlalchemy import delete

    from app.database import AsyncSessionLocal
    from app.models.api_key import UserApiKey

    async def wipe():
        async with AsyncSessionLocal() as db:
            await db.execute(delete(UserApiKey))
            await db.commit()

    asyncio.run(wipe())


@pytest.fixture()
def valid_key_check(monkeypatch):
    async def always_valid(provider, key):
        return True

    monkeypatch.setattr("app.routers.api_keys.validate_key", always_valid)


def test_keys_require_auth(client):
    assert client.get("/api/settings/api-keys").status_code == 401


def test_unsupported_provider_rejected(client, auth_headers, valid_key_check):
    resp = client.put(
        "/api/settings/api-keys",
        headers=auth_headers,
        json={"provider": "anthropic", "key": "sk-whatever-123456"},
    )
    assert resp.status_code == 422


def test_invalid_key_rejected(client, auth_headers, monkeypatch):
    async def always_invalid(provider, key):
        return False

    monkeypatch.setattr("app.routers.api_keys.validate_key", always_invalid)
    resp = client.put(
        "/api/settings/api-keys",
        headers=auth_headers,
        json={"provider": "gemini", "key": "AIza-bogus-key-000000"},
    )
    assert resp.status_code == 422
    assert "didn't work" in resp.json()["detail"]


def test_save_list_masked_and_encrypted(client, auth_headers, valid_key_check):
    resp = client.put(
        "/api/settings/api-keys",
        headers=auth_headers,
        json={"provider": "gemini", "key": "AIza-my-secret-key-12345"},
    )
    assert resp.status_code == 200

    listing = client.get("/api/settings/api-keys", headers=auth_headers).json()["items"]
    gemini = next(i for i in listing if i["provider"] == "gemini")
    assert gemini["masked"].startswith("••••")
    assert "AIza-my-secret-key" not in str(listing)  # plaintext never returned

    # Encrypted at rest
    from sqlalchemy import select

    from app.core.security import decrypt_token
    from app.database import AsyncSessionLocal
    from app.models.api_key import UserApiKey

    async def fetch():
        async with AsyncSessionLocal() as db:
            return (await db.execute(select(UserApiKey))).scalars().first()

    row = asyncio.run(fetch())
    assert row.key_encrypted != "AIza-my-secret-key-12345"
    assert decrypt_token(row.key_encrypted) == "AIza-my-secret-key-12345"


def test_models_reflect_user_key(client, auth_headers, valid_key_check):
    # Test env has NO platform keys, but the user saved a gemini key above.
    client.put(
        "/api/settings/api-keys",
        headers=auth_headers,
        json={"provider": "gemini", "key": "AIza-my-secret-key-12345"},
    )
    models = client.get("/api/scripts/models", headers=auth_headers).json()["items"]
    keys = {m["key"]: m for m in models}
    assert "gemini" in keys
    assert keys["gemini"]["own"] is True
    assert "your key" in keys["gemini"]["label"]
    assert "openai" not in keys  # no platform key, no user key


def test_generate_json_prefers_user_key(monkeypatch):
    from app.services import llm

    captured = {}

    async def fake_gemini(system, user, temperature, api_key=None):
        captured["api_key"] = api_key
        return {"ok": True}

    monkeypatch.setattr("app.services.llm._PROVIDER_FUNCS", {"gemini": fake_gemini, "openai": fake_gemini})
    result = asyncio.run(
        llm.generate_json("s", "u", model="gemini", user_keys={"gemini": "user-own-key"})
    )
    assert result == {"ok": True}
    assert captured["api_key"] == "user-own-key"


def test_delete_key(client, auth_headers, valid_key_check):
    client.put(
        "/api/settings/api-keys",
        headers=auth_headers,
        json={"provider": "openai", "key": "sk-proj-abcdef123456"},
    )
    assert client.delete("/api/settings/api-keys/openai", headers=auth_headers).status_code == 204
    assert client.delete("/api/settings/api-keys/openai", headers=auth_headers).status_code == 404


def test_lenient_json_parsing():
    from app.services.llm import _lenient_json

    assert _lenient_json('{"a": 1}') == {"a": 1}
    assert _lenient_json('```json\n{"a": 1}\n```') == {"a": 1}
    assert _lenient_json('Sure! Here is the JSON:\n{"a": 1}\nHope that helps!') == {"a": 1}
    import pytest as _pytest
    with _pytest.raises(Exception):
        _lenient_json("no json here at all")


def test_huggingface_provider_offered_with_byo_key():
    from app.services.llm import available_models

    # No platform keys in the test env: only BYO providers appear
    models = available_models({"huggingface": "hf_usertoken"})
    keys = {m["key"]: m for m in models}
    assert "huggingface" in keys
    assert keys["huggingface"]["own"] is True
    assert "Llama" in keys["huggingface"]["label"]


def test_huggingface_key_validation(monkeypatch):
    import httpx

    from app.services.user_keys import validate_key

    class FakeResponse:
        def __init__(self, code):
            self.status_code = code

    class FakeClient:
        def __init__(self, code):
            self._code = code

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def get(self, url, headers=None):
            assert "whoami" in url
            return FakeResponse(self._code)

    monkeypatch.setattr(httpx, "AsyncClient", lambda timeout=10: FakeClient(200))
    assert asyncio.run(validate_key("huggingface", "hf_good")) is True

    monkeypatch.setattr(httpx, "AsyncClient", lambda timeout=10: FakeClient(401))
    assert asyncio.run(validate_key("huggingface", "hf_bad")) is False


def test_generate_json_falls_through_to_huggingface(monkeypatch):
    """Gemini and OpenAI dead -> the HF provider still answers."""
    from app.services import llm

    async def dead(*a, **k):
        raise ValueError("invalid api key")  # permanent -> no in-provider retry

    async def hf_ok(system, user, temperature, api_key=None):
        assert api_key == "hf_usertoken"
        return {"ok": True}

    monkeypatch.setitem(llm._PROVIDER_FUNCS, "gemini", dead)
    monkeypatch.setitem(llm._PROVIDER_FUNCS, "openai", dead)
    monkeypatch.setitem(llm._PROVIDER_FUNCS, "huggingface", hf_ok)

    out = asyncio.run(llm.generate_json(
        "sys", "user",
        user_keys={"gemini": "g", "openai": "o", "huggingface": "hf_usertoken"},
    ))
    assert out == {"ok": True}
