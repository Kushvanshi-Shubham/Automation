import pytest


def test_format_catalog(client, auth_headers):
    resp = client.get("/api/scripts/formats", headers=auth_headers)
    assert resp.status_code == 200
    items = {i["key"]: i for i in resp.json()["items"]}
    assert set(items) == {
        "reddit_story", "fake_text", "viral_story", "breaking_news",
        "motivational", "music_visual", "shayari", "gaming_update", "image_carousel",
    }
    assert all(i["available"] for i in items.values())
    assert items["reddit_story"]["output_type"] == "narrated"
    assert items["fake_text"]["output_type"] == "fake_text"
    assert items["motivational"]["output_type"] == "visual"
    assert items["image_carousel"]["output_type"] == "image"


def test_generate_rejects_bad_formats(client, auth_headers):
    resp = client.post("/api/scripts/generate", headers=auth_headers,
                       json={"custom_prompt": "some topic here", "format": "hollywood_blockbuster"})
    assert resp.status_code == 422


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


def test_reddit_story_format_recipe(client, auth_headers, capture_generate):
    resp = client.post("/api/scripts/generate", headers=auth_headers,
                       json={"custom_prompt": "my landlord painted over my windows", "format": "reddit_story"})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["output_type"] == "narrated"
    assert body["format"] == "reddit_story"
    assert body["defaults"]["caption_style"] == "classic"
    assert body["defaults"]["background_query"]  # single background theme
    assert body["defaults"]["music_mood"] == "calm"
    # The format's recipe reaches the LLM and the tone default applies
    assert "FIRST PERSON" in capture_generate["custom_instructions"]
    assert capture_generate["style"] == "viral_story"
    assert capture_generate["tone"] == "dramatic and suspenseful"

    # Defaults round-trip through GET so the studio can seed its pickers
    script = client.get(f"/api/scripts/{body['video_id']}", headers=auth_headers).json()
    assert script["format"] == "reddit_story"
    assert script["defaults"]["background_query"]


def test_shayari_format_defaults(client, auth_headers, capture_generate):
    resp = client.post("/api/scripts/generate", headers=auth_headers,
                       json={"custom_prompt": "raat aur tanhai par shayari", "format": "shayari"})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["defaults"]["voice_id"] == "hi-IN-MadhurNeural"
    assert capture_generate["language"] == "Hindi"
    # An explicit non-default user language must win over the format default
    resp = client.post("/api/scripts/generate", headers=auth_headers,
                       json={"custom_prompt": "night and solitude poetry", "format": "shayari",
                             "language": "Spanish"})
    assert resp.status_code == 200
    assert capture_generate["language"] == "Spanish"


def test_user_tone_beats_format_tone(client, auth_headers, capture_generate):
    client.post("/api/scripts/generate", headers=auth_headers,
                json={"custom_prompt": "gaming patch notes summary", "format": "gaming_update",
                      "tone": "funny and meme-y"})
    assert capture_generate["tone"] == "funny and meme-y"


def test_fake_text_parse_messages():
    from app.pipeline.fake_text import parse_messages

    segments = [
        {"text": "A: hey, you up?"},
        {"text": "B: yeah why"},
        {"text": "b - check your front door"},   # case + dash tolerated
        {"text": "no prefix falls back to turns"},
    ]
    msgs = parse_messages(segments)
    assert [m["speaker"] for m in msgs] == ["A", "B", "B", "B"]
    assert msgs[0]["text"] == "hey, you up?"
    assert msgs[2]["text"] == "check your front door"


def test_fake_text_timeline_and_ass(tmp_path):
    from app.pipeline.fake_text import build_timeline, write_chat_ass

    msgs = [{"speaker": "A", "text": "hey"}, {"speaker": "B", "text": "what"},
            {"speaker": "A", "text": "look outside right now"}]
    timeline, total = build_timeline(msgs)
    assert len(timeline) == 3
    assert all(e["typing_at"] < e["at"] for e in timeline)          # typing beat first
    assert timeline[0]["at"] < timeline[1]["typing_at"]             # strictly ordered
    assert total > timeline[-1]["at"]                               # tail hold

    path, duration = write_chat_ass(msgs, tmp_path / "chat.ass")
    content = path.read_text(encoding="utf-8")
    assert "Style: BubbleA" in content and "Style: BubbleB" in content
    assert "• • •" in content                                       # typing indicator
    assert "\\pos(" in content
    assert duration == total

    # A 40-message monologue must respect the duration cap
    many = [{"speaker": "AB"[i % 2], "text": "this message has quite a few words in it"} for i in range(40)]
    _, capped = build_timeline(many)
    assert capped <= 85.0


def test_generate_fake_text_format(client, auth_headers, capture_generate):
    resp = client.post("/api/scripts/generate", headers=auth_headers,
                       json={"custom_prompt": "roommate mystery texts", "format": "fake_text"})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["output_type"] == "fake_text"
    assert "TWO people" in capture_generate["custom_instructions"]
    assert body["defaults"]["background_query"]


def test_pick_music_mood(tmp_path, monkeypatch):
    import app.pipeline.runner as runner

    (tmp_path / "carefree_kevin_macleod_ccby.mp3").write_bytes(b"x")
    (tmp_path / "wallpaper_kevin_macleod_ccby.mp3").write_bytes(b"x")
    monkeypatch.setattr(runner, "MUSIC_DIR", tmp_path)

    assert runner._pick_music("calm").stem.startswith("wallpaper")
    assert runner._pick_music("energetic").stem.startswith("carefree")
    assert runner._pick_music(None) is not None       # no mood -> any track
    assert runner._pick_music("dubstep") is not None  # unknown mood -> fallback


def test_every_format_declares_its_own_look_and_pace():
    """A format that doesn't choose falls back to a generic default, which is
    how a shayari ended up as corporate flat-vector art read at news pace."""
    from app.services.formats import FORMATS
    from app.services.script_gen import STYLE_PROMPTS
    from app.services.image_gen import VISUAL_STYLES

    for key, fmt in FORMATS.items():
        assert fmt["style"] in STYLE_PROMPTS, f"{key}: unknown script style"
        assert fmt.get("visual_style") in VISUAL_STYLES, f"{key}: missing/unknown visual_style"
        wps = fmt.get("words_per_second")
        assert wps and 0.8 <= wps <= 4.0, f"{key}: implausible words_per_second {wps!r}"


def test_every_declared_mood_is_usable():
    """Moods steer music and look, so what they name has to exist."""
    from app.services.formats import FORMATS
    from app.services.image_gen import VISUAL_STYLES
    from app.pipeline.runner import MOOD_KEYWORDS

    found = 0
    for key, fmt in FORMATS.items():
        for mood_key, mood in (fmt.get("moods") or {}).items():
            found += 1
            assert mood.get("label"), f"{key}/{mood_key}: no label"
            assert mood.get("prompt"), f"{key}/{mood_key}: no prompt"
            if mood.get("music_mood"):
                assert mood["music_mood"] in MOOD_KEYWORDS, (
                    f"{key}/{mood_key}: music mood {mood['music_mood']!r} has no keywords, "
                    "so it would silently fall back to the whole library"
                )
            if mood.get("visual_style"):
                assert mood["visual_style"] in VISUAL_STYLES, f"{key}/{mood_key}: unknown visual_style"
    assert found >= 8, "expected sub-moods on shayari, music_visual and motivational"


def test_tts_rate_tracks_requested_pace():
    """Formats ask for a pace; without a real rate the request was ignored."""
    from app.pipeline.tts import rate_for

    assert rate_for(1.2) == "-45%"      # shayari: slow and deliberate
    assert rate_for(2.5) is None        # edge-tts default, leave it alone
    assert rate_for(None) is None
    assert rate_for(0) is None
    # clamped, so nothing turns into a slur or a chipmunk
    assert rate_for(0.1) == "-45%"
    assert rate_for(99) == "+25%"


def test_unknown_mood_is_rejected(client, auth_headers, capture_generate):
    resp = client.post("/api/scripts/generate", headers=auth_headers,
                       json={"custom_prompt": "rainy evening", "format": "shayari",
                             "mood": "not-a-real-mood"})
    assert resp.status_code == 422, resp.text
