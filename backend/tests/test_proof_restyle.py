"""Style decisions must be cheap: a free one-scene proof before committing
credits, and free re-renders when only the look changes.

Deliberately touches no database directly — the suite shares one sqlite
file and one user, so fixtures that write to it leak into other modules
and fight the app's connection pool. The pricing rule is a pure function
(services/credits.is_free_restyle) precisely so it can be tested here.
"""
import pytest

from app.services.credits import is_free_restyle


@pytest.fixture()
def mock_generate(monkeypatch):
    async def fake_generate(topic, **kwargs):
        return {
            "title": "t", "description": "d", "tags": [],
            "segments": [
                {"text": "first scene here", "visual_prompt": "a", "duration_estimate": 3.0},
                {"text": "second scene here", "visual_prompt": "b", "duration_estimate": 3.0},
            ],
            "total_duration": 6.0,
        }

    monkeypatch.setattr("app.routers.scripts.script_gen.generate_script", fake_generate)


@pytest.fixture()
def captured_proofs(monkeypatch):
    sent = []

    class _Task:
        id = "task-id"

    monkeypatch.setattr("app.pipeline.proof.render_proof.delay",
                        lambda *a, **k: (sent.append(a), _Task())[1])
    return sent


def _new_video(client, auth_headers):
    return client.post("/api/scripts/generate", headers=auth_headers,
                       json={"custom_prompt": "a video about proofs"}).json()["video_id"]


def _credits(client, auth_headers):
    return client.get("/api/billing/credits", headers=auth_headers).json()["balance"]


# ---------- the look catalogue ----------

def test_look_options_are_server_driven(client, auth_headers):
    body = client.get("/api/pipeline/look-options", headers=auth_headers).json()
    assert {"caption_styles", "caption_animations", "caption_fonts", "visual_styles"} <= set(body)
    animations = {a["key"] for a in body["caption_animations"]}
    assert {"none", "fade", "pop", "highlight", "typewriter"} <= animations
    assert body["free_restyles_per_video"] >= 1
    assert body["defaults"]["caption_style"]


# ---------- the free proof render ----------

def test_proof_is_free_and_saves_the_choices(client, auth_headers, mock_generate, captured_proofs):
    before = _credits(client, auth_headers)
    video_id = _new_video(client, auth_headers)

    resp = client.post("/api/pipeline/proof", headers=auth_headers,
                       json={"video_id": video_id, "scene_index": 1,
                             "caption_style": "neon", "caption_animation": "pop",
                             "caption_font": "impact", "caption_color": "#7C3AED",
                             "visual_style": "explainer"})
    assert resp.status_code == 200
    assert resp.json()["scene_index"] == 1
    assert _credits(client, auth_headers) == before, "a proof must never cost credits"
    assert captured_proofs, "a proof render should be enqueued"

    # The choices persist, so the paid render uses whatever the proof showed.
    script = client.get(f"/api/scripts/{video_id}", headers=auth_headers).json()
    assert script["defaults"]["caption_style"] == "neon"


def test_proof_rejects_nonsense_choices(client, auth_headers, mock_generate, captured_proofs):
    video_id = _new_video(client, auth_headers)
    for payload, expect in (
        ({"caption_animation": "explode"}, "animation"),
        ({"caption_font": "comic"}, "font"),
        ({"caption_color": "purple"}, "#7C3AED"),
        ({"visual_style": "vaporwave"}, "visual style"),
        ({"visual_engine": "veo"}, "engine"),
    ):
        resp = client.post("/api/pipeline/proof", headers=auth_headers,
                           json={"video_id": video_id, **payload})
        assert resp.status_code == 422, payload
        assert expect.split()[0].lower() in resp.json()["detail"].lower()


def test_proof_of_an_unknown_video_is_a_404(client, auth_headers, captured_proofs):
    resp = client.post("/api/pipeline/proof", headers=auth_headers,
                       json={"video_id": "00000000-0000-0000-0000-000000000000"})
    assert resp.status_code == 404


def test_proof_endpoint_reports_nothing_before_one_runs(client, auth_headers, mock_generate):
    video_id = _new_video(client, auth_headers)
    body = client.get(f"/api/pipeline/proof/{video_id}", headers=auth_headers).json()
    assert body["proof"] is None


# ---------- when a re-render is free ----------

def _base(**over):
    args = dict(
        has_render=True, credits_used=1,
        current_engine="pexels", requested_engine="pexels",
        current_voice_provider=None, requested_voice_provider=None,
        restyles_used=0, allowance=3,
    )
    args.update(over)
    return args


def test_restyling_a_finished_video_is_free():
    assert is_free_restyle(**_base()) is True


def test_never_free_before_the_first_paid_render():
    assert is_free_restyle(**_base(has_render=False)) is False
    assert is_free_restyle(**_base(credits_used=0)) is False


def test_free_restyles_run_out():
    assert is_free_restyle(**_base(restyles_used=2)) is True
    assert is_free_restyle(**_base(restyles_used=3)) is False
    assert is_free_restyle(**_base(restyles_used=9)) is False


def test_changing_what_it_is_made_of_costs_again():
    # A different visual engine regenerates every scene — real work.
    assert is_free_restyle(**_base(requested_engine="ai_image")) is False
    # Switching to studio-grade narration is real spend too.
    assert is_free_restyle(**_base(requested_voice_provider="cartesia")) is False
    # Dropping back to the free voice is also a content change.
    assert is_free_restyle(
        **_base(current_voice_provider="cartesia", requested_voice_provider=None)
    ) is False
    # Keeping the same provider is still just a restyle.
    assert is_free_restyle(
        **_base(current_voice_provider="cartesia", requested_voice_provider="cartesia")
    ) is True
