"""Format registry — the product's core creation concept.

A FORMAT is an editing pipeline recipe, not a visual skin:
    input -> pacing -> asset rules -> caption style -> music -> editable controls

Each format maps onto a render engine (output_type) and layers its own
script recipe, visual sourcing rules, and render defaults on top. The
"Trend -> recommended format -> creator-specific draft" flow stays intact:
formats are what the recommendation ultimately points at.
"""

# Render defaults are stored into script_data at generation time so the
# runner and studio pick them up without extra plumbing. Everything remains
# user-editable in the studio (controls lists what the UI should surface).
FORMATS: dict[str, dict] = {
    "reddit_story": {
        "label": "Reddit Story",
        "emoji": "👽",
        "desc": "First-person storytime over immersive background footage",
        "when": "personal drama, confessions, wild it-happened-to-me stories",
        "output_type": "narrated",
        "style": "viral_story",
        "available": True,
        "script_recipe": (
            "FORMAT: Reddit-style story. Write in FIRST PERSON as if the narrator is reading their "
            "own wild-but-believable story post (confession / AITA / malicious-compliance energy). "
            "Hook = the single most dramatic sentence of the story ('I accidentally...', 'My landlord "
            "didn't know I...'). Conversational, contractions, emotional beats, one mid-story twist, "
            "clean payoff at the end. Never claim it's from Reddit; it's an original story."
        ),
        "background_query": "oddly satisfying parkour gameplay",
        "caption_style": "classic",
        "voice_id": None,
        "language": None,
        "music_mood": "calm",
        "tone": "dramatic and suspenseful",
        "controls": ["voice", "captions", "aspect", "background"],
    },
    "fake_text": {
        "label": "Fake Text Convo",
        "emoji": "💬",
        "desc": "A chat conversation plays out in text bubbles with typing beats",
        "when": "two-person drama or twists that land as a chat screenshot",
        "output_type": "fake_text",
        "style": "viral_story",
        "available": True,
        "script_recipe": (
            "FORMAT: text-message conversation between exactly TWO people. Each segment is ONE chat "
            "message. text = the message exactly as typed (casual, lowercase ok, emoji ok, under 15 "
            "words). Prefix each text with the speaker tag 'A:' or 'B:' (A opens the conversation). "
            "The conversation must escalate: normal opener -> something off -> twist -> screenshot-worthy "
            "final message. 10-16 messages. visual_prompt is ignored for this format; set it to 'chat'."
        ),
        "background_query": "aesthetic blurred city night bokeh",
        "caption_style": "classic",
        "voice_id": None,
        "language": None,
        "music_mood": "calm",
        "tone": "dramatic and suspenseful",
        "controls": ["captions", "aspect", "background"],
    },
    "viral_story": {
        "label": "Viral Story",
        "emoji": "🎬",
        "desc": "“You missed this” — hook-driven narrated storytelling",
        "when": "surprising facts, hidden details, stories where context matters",
        "output_type": "narrated",
        "style": "viral_story",
        "available": True,
        "script_recipe": None,  # this IS the base viral_story style
        "background_query": None,
        "caption_style": "classic",
        "voice_id": None,
        "language": None,
        "music_mood": "calm",
        "tone": "engaging and curious",
        "controls": ["voice", "captions", "aspect", "scenes"],
    },
    "breaking_news": {
        "label": "Breaking-News Explainer",
        "emoji": "🚨",
        "desc": "Urgent, factual — what happened and why it matters",
        "when": "news, world events, releases, results — anything time-sensitive",
        "output_type": "narrated",
        "style": "news_update",
        "available": True,
        "script_recipe": (
            "FORMAT: breaking-news explainer. Hook = the headline stated as urgently as the facts "
            "allow ('X just happened.'). Then: what changed, the 2-3 details that matter, what it "
            "means for the viewer, what happens next. Short punchy sentences (max ~15 words). "
            "Zero speculation presented as fact — label rumors as rumors."
        ),
        "background_query": None,
        "caption_style": "impact",
        "voice_id": None,
        "language": None,
        "music_mood": "energetic",
        "tone": "urgent and factual",
        "controls": ["voice", "captions", "aspect", "scenes"],
    },
    "motivational": {
        "label": "Motivational Quote",
        "emoji": "🔥",
        "desc": "Big on-screen lines over cinematic footage — no narration",
        "when": "mindset, discipline, self-improvement, inspirational themes",
        "output_type": "visual",
        "style": "viral_story",
        "available": True,
        "script_recipe": (
            "FORMAT: motivational short. 5-8 segments, each ONE powerful line of on-screen text "
            "(under 10 words), all serving a single theme. Speak directly to the viewer ('you'). "
            "Build: challenge -> reframe -> push -> final line that hits hardest. No cliches like "
            "'rise and grind'. visual_prompt = cinematic, moody, aspirational footage."
        ),
        "background_query": None,
        "caption_style": "minimal",
        "voice_id": None,
        "language": None,
        "music_mood": "calm",
        "tone": "calm and powerful",
        "controls": ["captions", "aspect", "scenes"],
    },
    "music_visual": {
        "label": "Music / Trend Visual",
        "emoji": "🎵",
        "desc": "On-screen text + vibe footage — attach the trending sound when posting",
        "when": "music releases, aesthetic moments, hype trends where vibe beats narration",
        "output_type": "visual",
        "style": "viral_story",
        "available": True,
        "script_recipe": None,  # the visual output type already carries its recipe
        "background_query": None,
        "caption_style": "neon",
        "voice_id": None,
        "language": None,
        "music_mood": "energetic",
        "tone": "hype and energetic",
        "controls": ["captions", "aspect", "scenes"],
    },
    "shayari": {
        "label": "Shayari / Poetry",
        "emoji": "🌙",
        "desc": "Original Hindi shayari, slow narration over aesthetic footage",
        "when": "poetry, romance, melancholy, Hindi-audience emotional topics",
        "output_type": "narrated",
        "style": "viral_story",
        "available": True,
        "script_recipe": (
            "FORMAT: shayari (Urdu-flavored Hindi poetry). Write an ORIGINAL shayari of 2-4 couplets "
            "(sher). Each segment = one couplet, written in Devanagari. Theme from the topic: love, "
            "loss, ambition, or life. Pacing is SLOW and deliberate — set duration_estimate at ~1.2 "
            "words/second so the narration breathes. End with the strongest couplet. "
            "visual_prompt = slow aesthetic footage (rain on window, sunset, chai, empty roads)."
        ),
        "background_query": None,
        "caption_style": "minimal",
        "voice_id": "hi-IN-MadhurNeural",
        "language": "Hindi",
        "music_mood": "calm",
        "tone": "soulful and poetic",
        "controls": ["voice", "captions", "aspect", "scenes"],
    },
    "gaming_update": {
        "label": "Gaming Update",
        "emoji": "🎮",
        "desc": "Patch notes and game news with hype pacing",
        "when": "game patches, esports, gaming culture and releases",
        "output_type": "narrated",
        "style": "news_update",
        "available": True,
        "script_recipe": (
            "FORMAT: gaming update. You're the friend who read the patch notes so the viewer doesn't "
            "have to. Hook = the single biggest change gamers care about. Then the buffs/nerfs/new "
            "content that actually change how people play, with hype but zero filler. Gamer-native "
            "vocabulary (meta, nerfed, buffed) without cringe. visual_prompt = gaming setups, esports "
            "crowds, RGB keyboards, controller close-ups (no copyrighted game footage)."
        ),
        "background_query": None,
        "caption_style": "neon",
        "voice_id": None,
        "language": None,
        "music_mood": "energetic",
        "tone": "hype and energetic",
        "controls": ["voice", "captions", "aspect", "scenes"],
    },
    "image_carousel": {
        "label": "Image Carousel",
        "emoji": "🖼️",
        "desc": "3–6 slide photo post with punchy captions",
        "when": "lists, tips, rankings, facts that work as swipeable slides",
        "output_type": "image",
        "style": "viral_story",
        "available": True,
        "script_recipe": None,  # the image output type already carries its recipe
        "background_query": None,
        "caption_style": "classic",
        "voice_id": None,
        "language": None,
        "music_mood": None,
        "tone": "engaging and curious",
        "controls": ["aspect", "slides"],
    },
}

DEFAULT_TONE = "engaging and curious"  # matches ScriptGenerateRequest default

# Topics harvested before the format pack stored raw engine names in
# best_format — map them to the closest format key.
LEGACY_FORMAT_MAP = {"narrated": "viral_story", "visual": "music_visual", "image": "image_carousel"}


def render_defaults(fmt: dict) -> dict:
    """The script_data entries a format contributes at generation time."""
    out = {}
    if fmt.get("caption_style"):
        out["caption_style"] = fmt["caption_style"]
    if fmt.get("voice_id"):
        out["voice_id"] = fmt["voice_id"]
    if fmt.get("music_mood"):
        out["music_mood"] = fmt["music_mood"]
    if fmt.get("background_query"):
        out["background_query"] = fmt["background_query"]
    return out
