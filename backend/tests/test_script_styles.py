FAKE = {
    "title": "t", "description": "d", "tags": ["x"],
    "segments": [{"text": "hello world example", "visual_prompt": "vp", "duration_estimate": 2.0}],
    "total_duration": 2.0,
}


def test_unknown_style_rejected(client, auth_headers):
    resp = client.post(
        "/api/scripts/generate",
        headers=auth_headers,
        json={"custom_prompt": "some valid topic prompt", "style": "poetry_slam"},
    )
    assert resp.status_code == 422


def test_style_forwarded_to_generator(client, auth_headers, monkeypatch):
    captured = {}

    async def fake_generate(topic, hook_hint=None, tone="engaging and curious", duration_seconds=60, style="viral_story"):
        captured["style"] = style
        return dict(FAKE)

    monkeypatch.setattr("app.routers.scripts.script_gen.generate_script", fake_generate)
    resp = client.post(
        "/api/scripts/generate",
        headers=auth_headers,
        json={"custom_prompt": "apex legends new season update", "style": "news_update"},
    )
    assert resp.status_code == 200
    assert captured["style"] == "news_update"


def test_custom_script_path(client, auth_headers, monkeypatch):
    captured = {}

    async def fake_format(script_text):
        captured["text"] = script_text
        return dict(FAKE)

    monkeypatch.setattr("app.routers.scripts.script_gen.format_custom_script", fake_format)
    own_script = "This is my own script about my gaming channel. I wrote every word myself and want it unchanged."
    resp = client.post(
        "/api/scripts/generate",
        headers=auth_headers,
        json={"custom_script": own_script},
    )
    assert resp.status_code == 200
    assert captured["text"] == own_script

    video_id = resp.json()["video_id"]
    video = client.get(f"/api/videos/{video_id}", headers=auth_headers).json()
    assert video["status"] == "script_ready"


def test_custom_script_too_short(client, auth_headers):
    resp = client.post("/api/scripts/generate", headers=auth_headers, json={"custom_script": "too short"})
    assert resp.status_code == 422
