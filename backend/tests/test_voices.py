def test_voices_catalog(client, auth_headers):
    resp = client.get("/api/scripts/voices", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    ids = [v["id"] for v in body["voices"]]
    assert "en-US-ChristopherNeural" in ids
    assert "hi-IN-MadhurNeural" in ids  # India matters
    assert "Hindi" in body["languages"]


def test_unknown_voice_preview_404(client, auth_headers):
    resp = client.get("/api/scripts/voices/xx-XX-FakeNeural/preview", headers=auth_headers)
    assert resp.status_code == 404


def test_pipeline_rejects_unknown_voice(client, auth_headers, monkeypatch):
    async def fake_generate(topic, **kwargs):
        return {
            "title": "t", "description": "d", "tags": [],
            "segments": [{"text": "hello world", "visual_prompt": "x", "duration_estimate": 2.0}],
            "total_duration": 2.0,
        }

    monkeypatch.setattr("app.routers.scripts.script_gen.generate_script", fake_generate)
    video_id = client.post(
        "/api/scripts/generate", headers=auth_headers,
        json={"custom_prompt": "voice validation test"},
    ).json()["video_id"]

    resp = client.post(
        "/api/pipeline/start", headers=auth_headers,
        json={"video_id": video_id, "visual_engine": "pexels", "voice_id": "xx-XX-FakeNeural"},
    )
    assert resp.status_code == 422


def test_language_forwarded(client, auth_headers, monkeypatch):
    captured = {}

    async def fake_generate(topic, **kwargs):
        captured.update(kwargs)
        return {
            "title": "t", "description": "d", "tags": [],
            "segments": [{"text": "नमस्ते दुनिया", "visual_prompt": "x", "duration_estimate": 2.0}],
            "total_duration": 2.0,
        }

    monkeypatch.setattr("app.routers.scripts.script_gen.generate_script", fake_generate)
    resp = client.post(
        "/api/scripts/generate", headers=auth_headers,
        json={"custom_prompt": "hindi language test", "language": "Hindi"},
    )
    assert resp.status_code == 200
    assert captured["language"] == "Hindi"
