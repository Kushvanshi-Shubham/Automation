def test_list_videos_paginated_shape(client, auth_headers):
    resp = client.get("/api/videos?page=1&page_size=5", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body["items"], list)
    assert len(body["items"]) <= 5
    assert body["total"] >= len(body["items"])


def test_get_missing_video_404(client, auth_headers):
    resp = client.get("/api/videos/00000000-0000-0000-0000-000000000000", headers=auth_headers)
    assert resp.status_code == 404


def test_unbuilt_features_return_501_not_fake_success(client, auth_headers):
    resp = client.post("/api/topics/custom?prompt=test", headers=auth_headers)
    assert resp.status_code == 501
    # Cancel IS built now (refund + free the video) — see test_cancel_reap.py.
    # An unknown job must 404, never a fake success.
    resp = client.post(
        "/api/pipeline/00000000-0000-0000-0000-000000000000/cancel",
        headers=auth_headers,
    )
    assert resp.status_code == 404


def test_pipeline_start_unknown_video_404(client, auth_headers):
    resp = client.post(
        "/api/pipeline/start",
        headers=auth_headers,
        json={"video_id": "00000000-0000-0000-0000-000000000000", "visual_engine": "pexels"},
    )
    assert resp.status_code == 404


def test_pipeline_start_rejects_unavailable_engine(client, auth_headers, monkeypatch):
    async def fake_generate(topic, **kwargs):
        return {
            "title": "t", "description": "d", "tags": [],
            "segments": [{"text": "hello world", "visual_prompt": "x", "duration_estimate": 2.0}],
            "total_duration": 2.0,
        }

    monkeypatch.setattr("app.routers.scripts.script_gen.generate_script", fake_generate)
    video_id = client.post(
        "/api/scripts/generate", headers=auth_headers,
        json={"custom_prompt": "engine rejection test"},
    ).json()["video_id"]

    resp = client.post(
        "/api/pipeline/start",
        headers=auth_headers,
        json={"video_id": video_id, "visual_engine": "veo"},
    )
    assert resp.status_code == 422
