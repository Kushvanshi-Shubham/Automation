from app.services.harvester import (
    _keywords_from_title,
    _score_from_traffic,
    _score_from_upvotes,
    content_hash,
)


def test_content_hash_normalizes():
    assert content_hash("  Hello World ") == content_hash("hello world")
    assert content_hash("a") != content_hash("b")


def test_scores_are_bounded_and_monotonic():
    low = _score_from_traffic("200+")
    high = _score_from_traffic("2,000,000+")
    assert 0 < low < high <= 99
    assert 0 < _score_from_upvotes(50) < _score_from_upvotes(90000) <= 99


def test_keywords_extraction():
    kws = _keywords_from_title("Why intermittent fasting might actually be bad")
    assert "Intermittent" in kws and len(kws) <= 4


def test_refresh_endpoint_dedupes(client, auth_headers, monkeypatch):
    fake_batch = [
        {"title": "AI beats humans at chess again", "source": "trends", "score": 90.0,
         "keywords": ["Chess"], "hook_text": "hook"},
        {"title": "AI beats humans at chess again", "source": "reddit", "score": 80.0,
         "keywords": ["Chess"], "hook_text": "hook"},  # dupe title, different source
        {"title": "New exoplanet discovered", "source": "reddit", "score": 70.0,
         "keywords": ["Exoplanet"], "hook_text": "hook"},
    ]

    async def fake_trends(client_, geo="US"):
        return [t for t in fake_batch if t["source"] == "trends"]

    async def fake_reddit(client_, subreddits=None, limit_per_sub=8):
        return [t for t in fake_batch if t["source"] == "reddit"]

    monkeypatch.setattr("app.services.harvester.fetch_google_trends", fake_trends)
    monkeypatch.setattr("app.services.harvester.fetch_reddit_trending", fake_reddit)

    first = client.post("/api/topics/refresh", headers=auth_headers).json()
    assert first["fetched"] == 3
    assert first["added"] == 2  # duplicate title collapsed

    second = client.post("/api/topics/refresh", headers=auth_headers).json()
    assert second["added"] == 0  # all already in DB

    topics = client.get("/api/topics", headers=auth_headers).json()["items"]
    titles = [t["title"] for t in topics]
    assert "AI beats humans at chess again" in titles
    assert "New exoplanet discovered" in titles
