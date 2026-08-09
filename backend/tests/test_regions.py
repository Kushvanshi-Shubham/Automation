"""Trend harvesting is region-aware (India first) and reports which
source went quiet instead of silently returning half the trends."""
import pytest


@pytest.fixture()
def capture_harvest(monkeypatch):
    seen = {}

    async def fake_harvest(db, geo="US"):
        seen["geo"] = geo
        return {"fetched": 10, "added": 3, "errors": {"trends": "429 Too Many Requests"}}

    monkeypatch.setattr("app.routers.topics.harvest_topics", fake_harvest)
    return seen


def test_regions_are_listed_with_india_default(client, auth_headers):
    body = client.get("/api/topics/regions", headers=auth_headers).json()
    keys = [r["key"] for r in body["items"]]
    assert "IN" in keys and "US" in keys
    assert body["default"] == "IN"


def test_refresh_defaults_to_india(client, auth_headers, capture_harvest):
    resp = client.post("/api/topics/refresh", headers=auth_headers)
    assert resp.status_code == 200
    assert capture_harvest["geo"] == "IN"
    assert resp.json()["geo"] == "IN"


def test_refresh_honours_the_chosen_region(client, auth_headers, capture_harvest):
    resp = client.post("/api/topics/refresh?geo=us", headers=auth_headers)
    assert resp.status_code == 200
    assert capture_harvest["geo"] == "US"  # case-insensitive


def test_unknown_region_rejected(client, auth_headers, capture_harvest):
    assert client.post("/api/topics/refresh?geo=ZZ", headers=auth_headers).status_code == 422


def test_source_failures_reach_the_caller(client, auth_headers, capture_harvest):
    body = client.post("/api/topics/refresh", headers=auth_headers).json()
    assert "trends" in body["errors"]  # the UI turns this into a plain sentence
