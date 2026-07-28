FAKE_SCRIPT = {
    "title": "The Fall of Rome in 60 Seconds",
    "description": "Why Rome really fell. #history #rome #shorts",
    "tags": ["rome", "history", "shorts"],
    "segments": [
        {"text": "Rome didn't fall in a day.", "visual_prompt": "ancient roman ruins at dusk", "duration_estimate": 3.0},
        {"text": "It bled out over centuries.", "visual_prompt": "crumbling colosseum timelapse", "duration_estimate": 3.5},
    ],
    "total_duration": 6.5,
}


def _mock_generate(monkeypatch):
    async def fake_generate(topic, hook_hint=None, tone="engaging and curious", duration_seconds=60, style="viral_story"):
        return dict(FAKE_SCRIPT)

    monkeypatch.setattr("app.routers.scripts.script_gen.generate_script", fake_generate)


def test_generate_from_custom_prompt_creates_video(client, auth_headers, monkeypatch):
    _mock_generate(monkeypatch)
    resp = client.post(
        "/api/scripts/generate",
        headers=auth_headers,
        json={"custom_prompt": "Why the Roman Empire collapsed"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["segments"]) == 2
    video_id = body["video_id"]

    video = client.get(f"/api/videos/{video_id}", headers=auth_headers).json()
    assert video["status"] == "script_ready"
    assert video["title"] == FAKE_SCRIPT["title"]


def test_generate_requires_topic_or_prompt(client, auth_headers):
    resp = client.post("/api/scripts/generate", headers=auth_headers, json={})
    assert resp.status_code == 422


def test_update_script_saves_edits(client, auth_headers, monkeypatch):
    _mock_generate(monkeypatch)
    video_id = client.post(
        "/api/scripts/generate",
        headers=auth_headers,
        json={"custom_prompt": "Why the Roman Empire collapsed"},
    ).json()["video_id"]

    edited = {
        "segments": [
            {"text": "Edited hook.", "visual_prompt": "new visual", "duration_estimate": 2.0},
        ]
    }
    resp = client.put(f"/api/scripts/{video_id}", headers=auth_headers, json=edited)
    assert resp.status_code == 200
    assert resp.json()["segments"][0]["text"] == "Edited hook."
    assert resp.json()["total_duration"] == 2.0

    fetched = client.get(f"/api/scripts/{video_id}", headers=auth_headers).json()
    assert fetched["segments"][0]["text"] == "Edited hook."


def test_regenerate_segment_replaces_only_target(client, auth_headers, monkeypatch):
    _mock_generate(monkeypatch)
    video_id = client.post(
        "/api/scripts/generate",
        headers=auth_headers,
        json={"custom_prompt": "Why the Roman Empire collapsed"},
    ).json()["video_id"]

    async def fake_regen(topic, full_script, segment_index, feedback):
        return {"text": "REGENERATED", "visual_prompt": "vp", "duration_estimate": 4.0}

    monkeypatch.setattr("app.routers.scripts.script_gen.regenerate_segment", fake_regen)

    resp = client.post(
        f"/api/scripts/{video_id}/regenerate-segment",
        headers=auth_headers,
        json={"segment_index": 1, "feedback": "make it punchier"},
    )
    assert resp.status_code == 200
    segs = resp.json()["segments"]
    assert segs[0]["text"] == FAKE_SCRIPT["segments"][0]["text"]
    assert segs[1]["text"] == "REGENERATED"

    bad = client.post(
        f"/api/scripts/{video_id}/regenerate-segment",
        headers=auth_headers,
        json={"segment_index": 99, "feedback": "x"},
    )
    assert bad.status_code == 422
