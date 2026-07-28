def test_categories_endpoint(client, auth_headers):
    resp = client.get("/api/uploads/categories", headers=auth_headers)
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert {"id": "20", "label": "Gaming"} in items
    assert {"id": "24", "label": "Entertainment"} in items


def test_publish_rejects_invalid_category(client, auth_headers, monkeypatch):
    async def fake_generate(topic, **kwargs):
        return {
            "title": "t", "description": "d", "tags": [],
            "segments": [{"text": "hello world", "visual_prompt": "x", "duration_estimate": 2.0}],
            "total_duration": 2.0,
        }

    monkeypatch.setattr("app.routers.scripts.script_gen.generate_script", fake_generate)
    video_id = client.post(
        "/api/scripts/generate", headers=auth_headers,
        json={"custom_prompt": "category validation test"},
    ).json()["video_id"]

    resp = client.post(
        f"/api/uploads/{video_id}/publish",
        headers=auth_headers,
        json={"channel_id": "00000000-0000-0000-0000-000000000000", "privacy": "unlisted", "category_id": "999"},
    )
    assert resp.status_code == 422
    assert "category" in resp.json()["detail"].lower()


def test_metadata_update_roundtrip(client, auth_headers, monkeypatch):
    async def fake_generate(topic, **kwargs):
        return {
            "title": "AI title", "description": "AI desc", "tags": ["ai"],
            "segments": [{"text": "hello world", "visual_prompt": "x", "duration_estimate": 2.0}],
            "total_duration": 2.0,
        }

    monkeypatch.setattr("app.routers.scripts.script_gen.generate_script", fake_generate)
    video_id = client.post(
        "/api/scripts/generate", headers=auth_headers,
        json={"custom_prompt": "metadata roundtrip test"},
    ).json()["video_id"]

    resp = client.put(
        f"/api/videos/{video_id}/metadata",
        headers=auth_headers,
        json={"title": "My edited title", "description": "My edited desc", "tags": ["apex", "gaming"]},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["title"] == "My edited title"
    assert body["tags"] == ["apex", "gaming"]
