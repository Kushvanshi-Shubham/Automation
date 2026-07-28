def test_list_videos_paginated_shape(client, auth_headers):
    resp = client.get("/api/videos", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body["items"], list)
    assert body["total"] == len(body["items"])  # single page in tests


def test_get_missing_video_404(client, auth_headers):
    resp = client.get("/api/videos/00000000-0000-0000-0000-000000000000", headers=auth_headers)
    assert resp.status_code == 404


def test_unbuilt_features_return_501_not_fake_success(client, auth_headers):
    resp = client.post("/api/topics/custom?prompt=test", headers=auth_headers)
    assert resp.status_code == 501
    resp = client.post(
        "/api/pipeline/start",
        headers=auth_headers,
        json={"video_id": "00000000-0000-0000-0000-000000000000", "visual_engine": "pexels"},
    )
    assert resp.status_code == 501
