"""HeyGen joins the BYO-key providers (AI-presenter lane scaffold)."""
import pytest


@pytest.fixture()
def accept_keys(monkeypatch):
    async def ok(provider, key):
        return True

    monkeypatch.setattr("app.routers.api_keys.validate_key", ok)


def test_heygen_key_can_be_stored(client, auth_headers, accept_keys):
    resp = client.put("/api/settings/api-keys", headers=auth_headers,
                      json={"provider": "heygen", "key": "hg-test-key-1234567890"})
    assert resp.status_code == 200
    assert resp.json()["provider"] == "heygen"

    items = client.get("/api/settings/api-keys", headers=auth_headers).json()["items"]
    providers = {i["provider"] for i in items}
    assert "heygen" in providers
    # plaintext never comes back
    assert all("hg-test-key" not in (i["masked"] or "") for i in items)

    assert client.delete("/api/settings/api-keys/heygen", headers=auth_headers).status_code == 204


def test_unknown_provider_still_rejected(client, auth_headers, accept_keys):
    resp = client.put("/api/settings/api-keys", headers=auth_headers,
                      json={"provider": "veo3", "key": "whatever-key-123456"})
    assert resp.status_code == 422
