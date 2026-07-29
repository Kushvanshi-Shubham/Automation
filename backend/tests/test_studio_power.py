FAKE = {
    "title": "t", "description": "d", "tags": ["x"],
    "segments": [{"text": "hello world example", "visual_prompt": "vp", "duration_estimate": 2.0}],
    "total_duration": 2.0,
}


def test_models_endpoint(client, auth_headers):
    resp = client.get("/api/scripts/models", headers=auth_headers)
    assert resp.status_code == 200
    keys = [m["key"] for m in resp.json()["items"]]
    # Test env has no LLM keys configured → only "auto" is offered.
    assert keys == ["auto"]


def test_unknown_model_rejected(client, auth_headers):
    resp = client.post(
        "/api/scripts/generate",
        headers=auth_headers,
        json={"custom_prompt": "some valid topic prompt", "model": "claude"},
    )
    assert resp.status_code == 422


def test_unconfigured_model_503(client, auth_headers):
    # gemini is a valid key but not configured in the test env
    resp = client.post(
        "/api/scripts/generate",
        headers=auth_headers,
        json={"custom_prompt": "some valid topic prompt", "model": "gemini"},
    )
    assert resp.status_code == 503


def test_model_and_instructions_forwarded(client, auth_headers, monkeypatch):
    captured = {}

    async def fake_generate(topic, **kwargs):
        captured.update(
            model=kwargs.get("model"),
            instructions=kwargs.get("custom_instructions"),
            tone=kwargs.get("tone"),
        )
        return dict(FAKE)

    monkeypatch.setattr("app.routers.scripts.script_gen.generate_script", fake_generate)
    resp = client.post(
        "/api/scripts/generate",
        headers=auth_headers,
        json={
            "custom_prompt": "apex legends update video",
            "model": "auto",
            "tone": "hype and energetic",
            "custom_instructions": "always mention my channel name GamerX at the end",
        },
    )
    assert resp.status_code == 200
    assert captured["model"] == "auto"
    assert "GamerX" in captured["instructions"]
    assert captured["tone"] == "hype and energetic"


def test_instructions_length_capped(client, auth_headers):
    resp = client.post(
        "/api/scripts/generate",
        headers=auth_headers,
        json={"custom_prompt": "valid prompt here", "custom_instructions": "x" * 700},
    )
    assert resp.status_code == 422
