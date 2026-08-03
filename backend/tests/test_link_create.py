"""Create from a link: generate branch + creator-footage segment pins."""
import pytest

from app.services.link_ingest import LinkIngestError


@pytest.fixture()
def capture_generate(monkeypatch):
    captured = {}

    async def fake_generate(topic, **kwargs):
        captured["topic"] = topic
        captured.update(kwargs)
        return {
            "title": "t", "description": "d", "tags": [],
            "segments": [{"text": "hello world", "visual_prompt": "x", "duration_estimate": 2.0}],
            "total_duration": 2.0,
        }

    monkeypatch.setattr("app.routers.scripts.script_gen.generate_script", fake_generate)
    return captured


@pytest.fixture()
def fake_extract(monkeypatch):
    async def _extract(url):
        return {"kind": "article", "source_url": url, "title": "GPU rentals in India",
                "text": "The Indian government is renting out GPUs for about a dollar an hour."}

    monkeypatch.setattr("app.services.link_ingest.extract_from_url", _extract)


def test_generate_from_link(client, auth_headers, capture_generate, fake_extract):
    resp = client.post("/api/scripts/generate", headers=auth_headers,
                       json={"source_url": "https://example.com/post", "format": "breaking_news"})
    assert resp.status_code == 200
    assert capture_generate["topic"] == "GPU rentals in India"
    assert "renting out GPUs" in capture_generate["reference_text"]

    video_id = resp.json()["video_id"]
    script = client.get(f"/api/scripts/{video_id}", headers=auth_headers).json()
    assert script["format"] == "breaking_news"


def test_generate_from_link_with_angle(client, auth_headers, capture_generate, fake_extract):
    resp = client.post("/api/scripts/generate", headers=auth_headers,
                       json={"source_url": "https://example.com/post",
                             "custom_prompt": "focus on what it means for startups"})
    assert resp.status_code == 200
    assert capture_generate["topic"] == "focus on what it means for startups"
    assert capture_generate["reference_text"]


def test_bad_link_is_a_422(client, auth_headers, monkeypatch):
    async def _boom(url):
        raise LinkIngestError("Only http(s) links are supported.")

    monkeypatch.setattr("app.services.link_ingest.extract_from_url", _boom)
    resp = client.post("/api/scripts/generate", headers=auth_headers,
                       json={"source_url": "ftp://example.com"})
    assert resp.status_code == 422
    assert "http(s)" in resp.json()["detail"]


def test_segment_asset_pin_survives_save(client, auth_headers, capture_generate):
    resp = client.post("/api/scripts/generate", headers=auth_headers,
                       json={"custom_prompt": "a story about local footage"})
    video_id = resp.json()["video_id"]

    segments = resp.json()["segments"]
    segments[0]["asset_id"] = "1b4e28ba-2fa1-11d2-883f-0016d3cca427"
    segments[0]["asset_start"] = 12.5
    resp = client.put(f"/api/scripts/{video_id}", headers=auth_headers,
                      json={"segments": segments})
    assert resp.status_code == 200

    script = client.get(f"/api/scripts/{video_id}", headers=auth_headers).json()
    assert script["segments"][0]["asset_id"] == "1b4e28ba-2fa1-11d2-883f-0016d3cca427"
    assert script["segments"][0]["asset_start"] == 12.5
