FAKE = {
    "title": "t", "description": "d", "tags": ["x"],
    "segments": [{"text": "hello world example", "visual_prompt": "vp", "duration_estimate": 3.0}],
    "total_duration": 3.0,
}


def _mock(monkeypatch, captured=None):
    async def fake_generate(topic, **kwargs):
        if captured is not None:
            captured.update(kwargs)
        return dict(FAKE)

    monkeypatch.setattr("app.routers.scripts.script_gen.generate_script", fake_generate)


def test_unknown_output_type_rejected(client, auth_headers):
    resp = client.post(
        "/api/scripts/generate",
        headers=auth_headers,
        json={"custom_prompt": "some valid prompt", "output_type": "hologram"},
    )
    assert resp.status_code == 422


def test_output_type_stored_and_returned(client, auth_headers, monkeypatch):
    _mock(monkeypatch)
    resp = client.post(
        "/api/scripts/generate",
        headers=auth_headers,
        json={"custom_prompt": "a music trend visual", "output_type": "visual"},
    )
    assert resp.status_code == 200
    assert resp.json()["output_type"] == "visual"
    video_id = resp.json()["video_id"]

    video = client.get(f"/api/videos/{video_id}", headers=auth_headers).json()
    assert video["output_type"] == "visual"
    script = client.get(f"/api/scripts/{video_id}", headers=auth_headers).json()
    assert script["output_type"] == "visual"


def test_visual_type_injects_onscreen_instruction(client, auth_headers, monkeypatch):
    captured = {}
    _mock(monkeypatch, captured)
    client.post(
        "/api/scripts/generate",
        headers=auth_headers,
        json={"custom_prompt": "a music trend visual", "output_type": "visual"},
    )
    assert "ON-SCREEN TEXT" in (captured.get("custom_instructions") or "")


def test_script_only_cannot_render(client, auth_headers, monkeypatch):
    _mock(monkeypatch)
    video_id = client.post(
        "/api/scripts/generate",
        headers=auth_headers,
        json={"custom_prompt": "script only please", "output_type": "script"},
    ).json()["video_id"]

    resp = client.post(
        "/api/pipeline/start",
        headers=auth_headers,
        json={"video_id": video_id, "visual_engine": "pexels"},
    )
    assert resp.status_code == 422
    assert "script-only" in resp.json()["detail"]


def test_script_only_daily_rate_limit(client, auth_headers, monkeypatch):
    _mock(monkeypatch)
    # one script-only already created in the previous test; allow up to 5 total
    codes = []
    for _ in range(6):
        resp = client.post(
            "/api/scripts/generate",
            headers=auth_headers,
            json={"custom_prompt": "another free script", "output_type": "script"},
        )
        codes.append(resp.status_code)
    assert 429 in codes
    assert codes.count(200) <= 5
