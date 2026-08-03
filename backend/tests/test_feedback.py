"""Feedback memory: notes CRUD + injection into script generation."""
import pytest


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


def _cleanup(client, auth_headers):
    for item in client.get("/api/feedback-notes", headers=auth_headers).json()["items"]:
        client.delete(f"/api/feedback-notes/{item['id']}", headers=auth_headers)


def test_note_crud(client, auth_headers):
    resp = client.post("/api/feedback-notes", headers=auth_headers,
                       json={"note": "Make the captions bigger"})
    assert resp.status_code == 200
    note_id = resp.json()["id"]
    assert resp.json()["format"] is None

    resp = client.post("/api/feedback-notes", headers=auth_headers,
                       json={"note": "Face in the first 3 seconds", "format": "reddit_story"})
    assert resp.status_code == 200

    items = client.get("/api/feedback-notes", headers=auth_headers).json()["items"]
    assert len(items) == 2

    # format filter keeps global + matching, drops other formats
    items = client.get("/api/feedback-notes?format=viral_story", headers=auth_headers).json()["items"]
    assert [i["note"] for i in items] == ["Make the captions bigger"]

    assert client.delete(f"/api/feedback-notes/{note_id}", headers=auth_headers).status_code == 204
    _cleanup(client, auth_headers)


def test_note_validation(client, auth_headers):
    assert client.post("/api/feedback-notes", headers=auth_headers,
                       json={"note": "ok note", "format": "not_a_format"}).status_code == 422
    assert client.post("/api/feedback-notes", headers=auth_headers,
                       json={"note": "x"}).status_code == 422


def test_notes_injected_into_generation(client, auth_headers, capture_generate):
    client.post("/api/feedback-notes", headers=auth_headers,
                json={"note": "Never use static screens longer than a second"})
    client.post("/api/feedback-notes", headers=auth_headers,
                json={"note": "Open with a question", "format": "reddit_story"})
    client.post("/api/feedback-notes", headers=auth_headers,
                json={"note": "Gaming notes stay out", "format": "gaming_update"})

    resp = client.post("/api/scripts/generate", headers=auth_headers,
                       json={"custom_prompt": "my landlord painted over my windows",
                             "format": "reddit_story"})
    assert resp.status_code == 200

    instr = capture_generate["custom_instructions"]
    assert "Never use static screens longer than a second" in instr
    assert "Open with a question" in instr
    assert "Gaming notes stay out" not in instr
    # the format recipe still leads the instruction stack
    assert instr.index("standing feedback") > 0
    _cleanup(client, auth_headers)


def test_no_notes_no_block(client, auth_headers, capture_generate):
    resp = client.post("/api/scripts/generate", headers=auth_headers,
                       json={"custom_prompt": "a story about pigeons in delhi"})
    assert resp.status_code == 200
    assert not capture_generate.get("custom_instructions")
