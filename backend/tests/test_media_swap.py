FAKE = {
    "title": "t", "description": "d", "tags": ["x"],
    "segments": [
        {"text": "scene one", "visual_prompt": "ocean waves aerial", "duration_estimate": 3.0},
        {"text": "scene two", "visual_prompt": "city at night", "duration_estimate": 3.0},
    ],
    "total_duration": 6.0,
}


def _make_video(client, auth_headers, monkeypatch, output_type="narrated"):
    async def fake_generate(topic, **kwargs):
        return dict(FAKE)

    monkeypatch.setattr("app.routers.scripts.script_gen.generate_script", fake_generate)
    return client.post(
        "/api/scripts/generate", headers=auth_headers,
        json={"custom_prompt": "media swap test video", "output_type": output_type},
    ).json()["video_id"]


def test_media_options_endpoint(client, auth_headers, monkeypatch):
    video_id = _make_video(client, auth_headers, monkeypatch)

    async def fake_search(client_, query, media="video", per_page=8):
        assert query == "ocean waves aerial"
        assert media == "video"
        return [{"id": 111, "thumb": "https://x/t.jpg", "kind": "video", "duration": 12}]

    monkeypatch.setattr("app.pipeline.visuals.pexels.search_candidates", fake_search)

    resp = client.get(f"/api/scripts/{video_id}/segments/0/media-options", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["items"][0]["id"] == 111

    assert client.get(
        f"/api/scripts/{video_id}/segments/9/media-options", headers=auth_headers
    ).status_code == 422


def test_media_options_uses_photos_for_image_posts(client, auth_headers, monkeypatch):
    video_id = _make_video(client, auth_headers, monkeypatch, output_type="image")

    captured = {}

    async def fake_search(client_, query, media="video", per_page=8):
        captured["media"] = media
        return []

    monkeypatch.setattr("app.pipeline.visuals.pexels.search_candidates", fake_search)
    client.get(f"/api/scripts/{video_id}/segments/0/media-options", headers=auth_headers)
    assert captured["media"] == "photo"


def test_pinned_media_persists_through_script_update(client, auth_headers, monkeypatch):
    video_id = _make_video(client, auth_headers, monkeypatch)

    segments = list(FAKE["segments"])
    segments[0] = {**segments[0], "media_id": 424242, "media_thumb": "https://x/pin.jpg"}
    resp = client.put(
        f"/api/scripts/{video_id}", headers=auth_headers, json={"segments": segments}
    )
    assert resp.status_code == 200
    saved = resp.json()["segments"]
    assert saved[0]["media_id"] == 424242
    assert saved[0]["media_thumb"] == "https://x/pin.jpg"
    assert saved[1]["media_id"] is None

    fetched = client.get(f"/api/scripts/{video_id}", headers=auth_headers).json()
    assert fetched["segments"][0]["media_id"] == 424242
