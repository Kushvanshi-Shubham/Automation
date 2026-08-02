import asyncio


def test_recommend_formats_failsafe_without_llm():
    """Test env has no LLM keys — recommendation must return empty dicts, not crash."""
    from app.services.harvester import recommend_formats

    out = asyncio.run(recommend_formats(["some trending topic", "another one"]))
    assert out == [{}, {}]


def test_topics_expose_best_format(client, auth_headers, monkeypatch):
    batch = [
        {"title": "New KATSEYE song is everywhere", "source": "youtube", "category": "music",
         "score": 95.0, "keywords": [], "hook_text": "h",
         "best_format": "visual", "format_reason": "music-led emotional trend"},
    ]

    async def fake_yt(client_, region="US", limit=15):
        return batch

    async def fake_none(client_, *a, **k):
        return []

    async def fake_formats(titles):
        return [{}] * len(titles)  # already provided in batch

    monkeypatch.setattr("app.services.harvester.fetch_google_trends", fake_none)
    monkeypatch.setattr("app.services.harvester.fetch_reddit_trending", fake_none)
    monkeypatch.setattr("app.services.harvester.fetch_youtube_trending", fake_yt)
    monkeypatch.setattr("app.services.harvester.recommend_formats", fake_formats)

    assert client.post("/api/topics/refresh", headers=auth_headers).json()["added"] == 1

    items = client.get("/api/topics?category=music", headers=auth_headers).json()["items"]
    row = next(t for t in items if "KATSEYE" in t["title"])
    # Legacy engine value in the DB surfaces as its format key.
    assert row["best_format"] == "music_visual"
    assert "music-led" in row["format_reason"]


def test_recommend_formats_uses_format_keys(monkeypatch):
    from app.services import harvester

    async def fake_generate(system, user, temperature=0.0, model="auto", user_keys=None):
        # The prompt must offer format keys, not raw engines
        assert "reddit_story" in system and "music_visual" in system
        assert "- narrated:" not in system
        return {"formats": [
            {"format": "gaming_update", "why": "patch notes hype"},
            {"format": "narrated", "why": "legacy engine name is invalid now"},
            {"format": "shayari", "why": "emotional hindi audience"},
        ]}

    monkeypatch.setattr("app.services.llm.generate_json", fake_generate)
    out = asyncio.run(harvester.recommend_formats(["t1", "t2", "t3"]))
    assert out[0] == {"best_format": "gaming_update", "format_reason": "patch notes hype"}
    assert out[1] == {}  # invalid keys are dropped, not stored
    assert out[2]["best_format"] == "shayari"
