"""Trend mash-up: two rising trends woven into ONE script.

The point is the connection between them. A script that covers trend A and
then trend B is two videos stapled together, so these tests check the
instruction that forbids it actually reaches the model, and that the
provenance of both trends is recorded.
"""
import pytest

# output_type is "narrated" throughout, never "script": script-only creations
# are capped at FREE_SCRIPT_ONLY_PER_DAY per user per day, and every test here
# shares one user and one sqlite file, so the 6th call would 429 for reasons
# that have nothing to do with mash-ups. Generation is mocked either way.


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
def two_trends(client, auth_headers, monkeypatch):
    """Seed two topics through the harvester and return their ids."""
    batch = [
        {"title": "Everyone is arguing about the new cricket jersey", "source": "youtube",
         "category": "sports", "score": 91.0, "keywords": [], "hook_text": "the jersey nobody asked for",
         "best_format": "viral_story", "format_reason": "argument-driven"},
        {"title": "Onion prices hit a five-year high", "source": "google", "category": "general",
         "score": 88.0, "keywords": [], "hook_text": "your sabzi just got expensive",
         "best_format": "breaking_news", "format_reason": "hard news"},
    ]

    async def fake_yt(client_, region="US", limit=15):
        return batch

    async def fake_none(client_, *a, **k):
        return []

    async def fake_formats(titles):
        return [{}] * len(titles)

    monkeypatch.setattr("app.services.harvester.fetch_google_trends", fake_none)
    monkeypatch.setattr("app.services.harvester.fetch_reddit_trending", fake_none)
    monkeypatch.setattr("app.services.harvester.fetch_youtube_trending", fake_yt)
    monkeypatch.setattr("app.services.harvester.recommend_formats", fake_formats)
    client.post("/api/topics/refresh", headers=auth_headers)

    items = client.get("/api/topics", headers=auth_headers).json()["items"]
    jersey = next(t for t in items if "jersey" in t["title"])
    onion = next(t for t in items if "Onion" in t["title"])
    return jersey, onion


def test_mashup_sends_both_trends_and_the_rules(client, auth_headers, capture_generate, two_trends):
    jersey, onion = two_trends
    resp = client.post("/api/scripts/generate", headers=auth_headers,
                       json={"topic_id": jersey["id"], "mashup_topic_id": onion["id"],
                             "output_type": "narrated"})
    assert resp.status_code == 200, resp.text

    # The lead trend is the topic; the second reaches the model as its own
    # argument rather than being concatenated into the subject line.
    assert capture_generate["topic"] == jersey["title"]
    assert capture_generate["mashup_with"] == onion["title"]
    # The hook still comes from the lead trend.
    assert capture_generate["hook_hint"] == jersey["hook_text"]


def test_mashup_forbids_covering_them_in_turn(client, auth_headers, capture_generate, two_trends):
    """The failure mode is two videos stapled together; the prompt must say so."""
    from app.services.script_gen import MASHUP_RULES

    jersey, onion = two_trends
    client.post("/api/scripts/generate", headers=auth_headers,
                json={"topic_id": jersey["id"], "mashup_topic_id": onion["id"],
                      "output_type": "narrated"})
    assert "Never alternate topic by topic" in MASHUP_RULES
    # And an invented link is worse than admitting there isn't one.
    assert "Do NOT invent a causal link" in MASHUP_RULES


def test_mashup_records_both_trends(client, auth_headers, capture_generate, two_trends):
    jersey, onion = two_trends
    video_id = client.post("/api/scripts/generate", headers=auth_headers,
                           json={"topic_id": jersey["id"], "mashup_topic_id": onion["id"],
                                 "output_type": "narrated"}).json()["video_id"]

    body = client.get(f"/api/scripts/{video_id}", headers=auth_headers).json()
    assert body["mashup"]["titles"] == [jersey["title"], onion["title"]]
    assert body["mashup"]["topic_ids"] == [jersey["id"], onion["id"]]


def test_single_trend_has_no_mashup_block(client, auth_headers, capture_generate, two_trends):
    jersey, _ = two_trends
    video_id = client.post("/api/scripts/generate", headers=auth_headers,
                           json={"topic_id": jersey["id"], "output_type": "narrated"}).json()["video_id"]
    body = client.get(f"/api/scripts/{video_id}", headers=auth_headers).json()
    assert body["mashup"] is None


def test_a_single_trend_is_untouched(client, auth_headers, capture_generate, two_trends):
    """No mashup_topic_id means nothing about the prompt changes."""
    jersey, _ = two_trends
    client.post("/api/scripts/generate", headers=auth_headers,
                json={"topic_id": jersey["id"], "output_type": "narrated"})
    assert capture_generate["mashup_with"] is None


def test_mashing_a_trend_with_itself_is_rejected(client, auth_headers, capture_generate, two_trends):
    jersey, _ = two_trends
    resp = client.post("/api/scripts/generate", headers=auth_headers,
                       json={"topic_id": jersey["id"], "mashup_topic_id": jersey["id"],
                             "output_type": "narrated"})
    assert resp.status_code == 422
    assert "two different trends" in resp.json()["detail"]


def test_unknown_second_trend_is_rejected(client, auth_headers, capture_generate, two_trends):
    jersey, _ = two_trends
    resp = client.post("/api/scripts/generate", headers=auth_headers,
                       json={"topic_id": jersey["id"],
                             "mashup_topic_id": "00000000-0000-0000-0000-000000000000",
                             "output_type": "narrated"})
    assert resp.status_code == 404


def test_mashup_needs_a_first_trend(client, auth_headers, capture_generate, two_trends):
    """A link or a prompt has nothing to weave a second trend INTO."""
    _, onion = two_trends
    resp = client.post("/api/scripts/generate", headers=auth_headers,
                       json={"custom_prompt": "why everything costs more now",
                             "mashup_topic_id": onion["id"], "output_type": "narrated"})
    assert resp.status_code == 422
    assert "pick a first trend" in resp.json()["detail"]
