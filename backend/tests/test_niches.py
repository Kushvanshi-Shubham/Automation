from app.services.niches import GENERAL, NICHES, normalize


def test_normalize():
    assert normalize("gaming") == "gaming"
    assert normalize("GAMING ") == "gaming"
    assert normalize("astrology") == GENERAL
    assert normalize(None) == GENERAL


def test_niches_endpoint(client, auth_headers):
    resp = client.get("/api/topics/niches", headers=auth_headers)
    assert resp.status_code == 200
    keys = [n["key"] for n in resp.json()["items"]]
    assert "gaming" in keys and len(keys) == len(NICHES)


def test_topics_category_filter(client, auth_headers, monkeypatch):
    batch = [
        {"title": "New GPU benchmark shocks everyone", "source": "youtube", "category": "tech",
         "score": 90.0, "keywords": [], "hook_text": "h"},
        {"title": "Speedrunner breaks impossible record", "source": "youtube", "category": "gaming",
         "score": 88.0, "keywords": [], "hook_text": "h"},
    ]

    async def fake_trends(client_, geo="US"):
        return []

    async def fake_reddit(client_, subreddits=None, limit_per_sub=8):
        return []

    async def fake_youtube(client_, region="US", limit=15):
        return batch

    monkeypatch.setattr("app.services.harvester.fetch_google_trends", fake_trends)
    monkeypatch.setattr("app.services.harvester.fetch_reddit_trending", fake_reddit)
    monkeypatch.setattr("app.services.harvester.fetch_youtube_trending", fake_youtube)

    assert client.post("/api/topics/refresh", headers=auth_headers).json()["added"] == 2

    gaming = client.get("/api/topics?category=gaming", headers=auth_headers).json()["items"]
    assert all(t["category"] == "gaming" for t in gaming)
    assert any("Speedrunner" in t["title"] for t in gaming)
    assert not any("GPU" in t["title"] for t in gaming)

    assert client.get("/api/topics?category=nonsense", headers=auth_headers).status_code == 422


def test_classification_fallback_without_llm(client, auth_headers, monkeypatch):
    """No LLM configured in tests -> uncategorized items become 'general', not an error."""
    batch = [{"title": "Completely uncategorized thing happened", "source": "trends",
              "score": 70.0, "keywords": [], "hook_text": "h"}]

    async def fake_trends(client_, geo="US"):
        return batch

    async def fake_none(client_, *a, **k):
        return []

    monkeypatch.setattr("app.services.harvester.fetch_google_trends", fake_trends)
    monkeypatch.setattr("app.services.harvester.fetch_reddit_trending", fake_none)
    monkeypatch.setattr("app.services.harvester.fetch_youtube_trending", fake_none)

    resp = client.post("/api/topics/refresh", headers=auth_headers)
    assert resp.status_code == 200
    items = client.get("/api/topics?category=general", headers=auth_headers).json()["items"]
    assert any("uncategorized" in t["title"] for t in items)
