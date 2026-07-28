def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_google_login_creates_user_with_signup_credits(client, mock_google):
    resp = client.post("/api/auth/google", json={"id_token": "valid-google-token"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]

    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert me.status_code == 200
    user = me.json()
    assert user["email"] == "creator@example.com"
    assert user["role"] == "creator"
    assert user["plan"] == "free"
    assert user["credit_balance"] == 3


def test_google_login_is_idempotent(client, mock_google):
    first = client.post("/api/auth/google", json={"id_token": "valid-google-token"})
    second = client.post("/api/auth/google", json={"id_token": "valid-google-token"})
    assert first.status_code == 200 and second.status_code == 200

    token = second.json()["access_token"]
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    # Signup grant must not be applied twice.
    assert me.json()["credit_balance"] == 3


def test_invalid_google_token_rejected(client, mock_google):
    resp = client.post("/api/auth/google", json={"id_token": "bogus"})
    assert resp.status_code == 401


def test_me_requires_auth(client):
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/auth/me", headers={"Authorization": "Bearer garbage"}).status_code == 401


def test_protected_routers_require_auth(client):
    for path in ["/api/topics", "/api/videos", "/api/billing/credits", "/api/uploads"]:
        assert client.get(path).status_code == 401, path


def test_credits_endpoint(client, auth_headers):
    resp = client.get("/api/billing/credits", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == {"balance": 3, "plan": "free"}


def test_ledger_shows_signup_grant(client, auth_headers):
    resp = client.get("/api/billing/ledger", headers=auth_headers)
    assert resp.status_code == 200
    entries = resp.json()
    assert len(entries) == 1
    assert entries[0]["amount"] == 3
    assert entries[0]["type"] == "subscription_grant"
