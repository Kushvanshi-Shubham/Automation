FAKE = {
    "title": "t", "description": "d", "tags": ["x"],
    "segments": [
        {"text": "slide one caption", "visual_prompt": "a red apple", "duration_estimate": 3.0},
        {"text": "slide two caption", "visual_prompt": "a green pear", "duration_estimate": 3.0},
    ],
    "total_duration": 6.0,
}


def _mock(monkeypatch, captured=None):
    async def fake_generate(topic, **kwargs):
        if captured is not None:
            captured.update(kwargs)
        return dict(FAKE)

    monkeypatch.setattr("app.routers.scripts.script_gen.generate_script", fake_generate)


def test_image_type_injects_carousel_instruction(client, auth_headers, monkeypatch):
    captured = {}
    _mock(monkeypatch, captured)
    resp = client.post(
        "/api/scripts/generate",
        headers=auth_headers,
        json={"custom_prompt": "5 facts about coffee", "output_type": "image"},
    )
    assert resp.status_code == 200
    assert "IMAGE CAROUSEL" in (captured.get("custom_instructions") or "")
    assert resp.json()["output_type"] == "image"


def test_engine_type_matching(client, auth_headers, monkeypatch):
    _mock(monkeypatch)
    image_video = client.post(
        "/api/scripts/generate", headers=auth_headers,
        json={"custom_prompt": "engine match test", "output_type": "image"},
    ).json()["video_id"]

    # video engine on an image creation → 422
    resp = client.post(
        "/api/pipeline/start", headers=auth_headers,
        json={"video_id": image_video, "visual_engine": "pexels"},
    )
    assert resp.status_code == 422
    assert "doesn't fit" in resp.json()["detail"]

    narrated_video = client.post(
        "/api/scripts/generate", headers=auth_headers,
        json={"custom_prompt": "engine match test two", "output_type": "narrated"},
    ).json()["video_id"]

    # image engine on a narrated creation → 422
    resp = client.post(
        "/api/pipeline/start", headers=auth_headers,
        json={"video_id": narrated_video, "visual_engine": "ai_image"},
    )
    assert resp.status_code == 422
