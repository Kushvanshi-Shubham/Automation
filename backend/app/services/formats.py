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
        # What AI-generated scenes should look like for THIS format.
        "visual_style": "documentary",
        # Narration pace; drives both the script budget and the TTS rate.
        "words_per_second": 2.5,
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
        # What AI-generated scenes should look like for THIS format.
        "visual_style": "bold",
        # Narration pace; drives both the script budget and the TTS rate.
        "words_per_second": 2.5,
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
        # What AI-generated scenes should look like for THIS format.
        "visual_style": "cinematic",
        # Narration pace; drives both the script budget and the TTS rate.
        "words_per_second": 2.5,
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
        # What AI-generated scenes should look like for THIS format.
        "visual_style": "documentary",
        # Narration pace; drives both the script budget and the TTS rate.
        "words_per_second": 2.8,
        "available": True,
        "script_recipe": (
            "FORMAT: breaking-news explainer. Hook = the headline stated as urgently as the facts "
            "allow ('X just happened.'). Then: what changed, the 2-3 details that matter, what it "
            "means for the viewer, what happens next. Short punchy sentences (max ~15 words). "
            "Zero speculation presented as fact — label rumors as rumors."
        ),
        "background_query": None,
        "caption_style": "impact",
        "editing": {
            # News pushes in. Stillness reads as "nothing is happening".
            "motion": "punch",
            "transition": "cut",
            "words_per_cue": 3,
        },
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
        "style": "motivational",
        # What AI-generated scenes should look like for THIS format.
        "visual_style": "cinematic",
        # Narration pace; drives both the script budget and the TTS rate.
        "words_per_second": 2.0,
        "available": True,
        "script_recipe": (
            "FORMAT: motivational short. 5-8 segments, each ONE powerful line of on-screen text "
            "(under 10 words), all serving a single theme. Speak directly to the viewer ('you'). "
            "Build: challenge -> reframe -> push -> final line that hits hardest. No cliches like "
            "'rise and grind'. visual_prompt = the concrete thing THIS line points at — the "
            "alarm clock, the empty gym at 5am, the unopened message — shot cinematically. "
            "Only when a line is pure abstraction, fall back to moody aspirational footage."
        ),
        "background_query": None,
        "caption_style": "minimal",
        "editing": {
            # Slower than the default but not as still as poetry.
            "motion": "drift",
            # Was "soft" 0.2s. Pulled after the owner rejected the same dip in
            # shayari — the machinery stays and is tested, but no format ships
            # it until someone has watched one and liked it.
            "transition": "cut",
            "fade": 0.0,
            "pause_after": 0.4,
            "words_per_cue": 4,
        },
        "voice_id": None,
        "language": None,
        "music_mood": "calm",
        "tone": "calm and powerful",
        "moods": {
            "discipline": {"label": "Discipline", "prompt": "Angle: discipline over motivation. Concrete daily actions, no inspiration talk.", "music_mood": "uplifting"},
            "comeback": {"label": "Comeback", "prompt": "Angle: recovering from a real setback. Honest about the low point.", "music_mood": "uplifting"},
            "calm": {"label": "Calm resolve", "prompt": "Angle: quiet steadiness rather than intensity. Lower the volume, not the stakes.", "music_mood": "calm"},
        },
        "controls": ["captions", "aspect", "scenes"],
    },
    "music_visual": {
        "label": "Music / Trend Visual",
        "emoji": "🎵",
        "desc": "On-screen text + vibe footage — attach the trending sound when posting",
        "when": "music releases, aesthetic moments, hype trends where vibe beats narration",
        "output_type": "visual",
        "style": "lyrical",
        # What AI-generated scenes should look like for THIS format.
        "visual_style": "cinematic",
        # Narration pace; drives both the script budget and the TTS rate.
        "words_per_second": 1.6,
        "available": True,
        "script_recipe": None,  # the visual output type already carries its recipe
        "background_query": None,
        "caption_style": "neon",
        "voice_id": None,
        "language": None,
        "music_mood": "energetic",
        "tone": "hype and energetic",
        "moods": {
            "hype": {"label": "Hype / Party", "prompt": "Mood: hype. Short punchy lines, present tense, built to be repeated.", "music_mood": "energetic"},
            "chill": {"label": "Chill / Lo-fi", "prompt": "Mood: chill. Unhurried, spacious lines. Nothing shouts.", "music_mood": "calm"},
            "romantic": {"label": "Romantic", "prompt": "Mood: romantic. Intimate, second person, softer imagery.", "music_mood": "tender"},
            "sad": {"label": "Sad / Emotional", "prompt": "Mood: sad. Sparse lines with space between them. Understated.", "music_mood": "melancholy"},
        },
        "controls": ["captions", "aspect", "scenes"],
    },
    "shayari": {
        "label": "Shayari / Poetry",
        "emoji": "🌙",
        "desc": "Original Hindi shayari, slow narration over aesthetic footage",
        "when": "poetry, romance, melancholy, Hindi-audience emotional topics",
        # Text-led, NOT narrated. Owner: "narration is not good for shayari."
        # He is right and the research agrees: the dominant shayari reel is the
        # couplet set as typography over a still, carried by music, with no
        # voice at all. Every tutorial is "insert your text, pick a font, pick
        # a track". And the thing a machine cannot fake is exactly recitation —
        # a TTS sher is the worst of both, neither a human voice nor clean
        # type. Set as type it competes on craft we can actually control.
        # Narration stays possible (Cartesia has four Hindi voices) but it is
        # an opt-in, not what the format is.
        "output_type": "visual",
        "style": "poetry",
        # What AI-generated scenes should look like for THIS format.
        "visual_style": "cinematic",
        # Narration pace; drives both the script budget and the TTS rate.
        "words_per_second": 1.2,
        "available": True,
        "script_recipe": (
            "FORMAT: shayari (Urdu-flavored Hindi poetry). Write an ORIGINAL shayari in Devanagari. "
            "Each segment is ONE complete sher: TWO lines, on two separate lines, 6-10 words each — "
            "about 12-20 words per segment. A one-line segment is wrong. Theme from the topic: love, "
            "loss, ambition, or life. Nothing is spoken aloud: the sher is SET ON SCREEN and the "
            "viewer reads it while music plays, so duration_estimate is READING time — about 4 "
            "seconds plus one per 4 words, and never pad a line to fill it. End with the strongest "
            "couplet. "
            "visual_prompt = the image the couplet itself carries, shot slow and still. A sher "
            "almost always names one — the rain, the cup, the road, the empty chair — so use "
            "that one rather than a generic mood shot."
        ),
        "background_query": None,
        "caption_style": "minimal",
        "voice_id": "hi-IN-MadhurNeural",
        "language": "Hindi",
        "music_mood": "calm",
        "tone": "soulful and poetic",
        "editing": {
            # A sher is meant to land in silence, not be chased by a moving
            # camera. Drift is slow enough that you notice the line, not the shot.
            "motion": "drift",
            # Owner, on the first slow render: "too slow, the gap is weird —
            # if you download audio of shayari you will understand it."
            #
            # Both halves of that were the same mistake. The pause in shayari
            # is in the VOICE, not the picture: the reciter stops between the
            # misras and between shers while the scene simply holds. We had it
            # backwards — a dragged -45% voice that never stopped, over a
            # picture that dipped to black, which reads as a glitch.
            "transition": "cut",
            "fade": 0.0,
            # Bases, not final values — services/rhythm.py varies each one by
            # ending, line length, position and mood. The measured median of
            # a real pause is 0.53s, and these are only the STRUCTURAL gaps
            # (line and sher boundaries), so they sit near that median rather
            # than at the p90 the long tail comes from.
            "line_pause": 0.45,   # between the two misras of one sher
            "pause_after": 0.9,   # between one sher and the next
            # Spoken at a measured pace, NOT slowed. words_per_second stays
            # 1.2 so the couplets stay short; the silence fills the rest.
            "speech_wps": 2.2,
            # Shayari is read a LINE at a time. Three-word chunks cut a couplet
            # into pieces and destroy the shape the whole form depends on.
            "words_per_cue": 7,
            # The sher appears whole, both misras at once on their own lines,
            # and stays. This is the product now, not a caption.
            "caption_hold": True,
        },
        "moods": {
            "sad": {
                "label": "Sad / Dard",
                "prompt": "Mood: dard. Loss, distance, the ache of something that did not happen. "
                          "Restrained, never self-pitying. No consolation in the last line.",
                "music_mood": "melancholy",
            },
            "love": {
                "label": "Love / Ishq",
                "prompt": "Mood: ishq. Longing and tenderness, addressed to someone. "
                          "Warm rather than tragic. Let the last line turn toward hope.",
                "music_mood": "tender",
            },
            "nostalgic": {
                "label": "Nostalgia / Yaad",
                "prompt": "Mood: yaad. Memory, childhood, a place or a person outgrown. "
                          "Concrete remembered objects carry the feeling.",
                "music_mood": "calm",
            },
            "motivational": {
                "label": "Hausla / Resolve",
                "prompt": "Mood: hausla. Rising after a setback. Defiant, not preachy, "
                          "and never a slogan. Earn the final line.",
                "music_mood": "uplifting",
                "visual_style": "bold",
            },
        },
        # No "voice": the format does not speak. Music does the carrying, so
        # offering a voice picker would be a control with nothing behind it.
        "controls": ["captions", "aspect", "scenes", "music"],
    },
    "gaming_update": {
        "label": "Gaming Update",
        "emoji": "🎮",
        "desc": "Patch notes and game news with hype pacing",
        "when": "game patches, esports, gaming culture and releases",
        "output_type": "narrated",
        "style": "news_update",
        # What AI-generated scenes should look like for THIS format.
        "visual_style": "bold",
        # Narration pace; drives both the script budget and the TTS rate.
        "words_per_second": 2.8,
        "available": True,
        "script_recipe": (
            "FORMAT: gaming update. You're the friend who read the patch notes so the viewer doesn't "
            "have to. Hook = the single biggest change gamers care about. Then the buffs/nerfs/new "
            "content that actually change how people play, with hype but zero filler. Gamer-native "
            "vocabulary (meta, nerfed, buffed) without cringe. visual_prompt = the specific thing THIS line names, shown physically and "
            "without naming the game or any trademark. Only when a line names nothing "
            "depictable, fall back to a gaming setup or an esports crowd."
        ),
        "background_query": None,
        "caption_style": "neon",
        "editing": {
            "motion": "punch",
            "transition": "cut",
            "words_per_cue": 3,
        },
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
        # What AI-generated scenes should look like for THIS format.
        "visual_style": "bold",
        # Narration pace; drives both the script budget and the TTS rate.
        "words_per_second": 2.5,
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

# The two knobs formats genuinely differ on, as a vocabulary the API can
# validate a creator's override against. A format picks one of each; the
# studio lets it be changed afterwards, because the format's choice is a
# starting point, not a verdict — a shayari may want a sadder bed than the
# format assumed.
#
# Music: keys must match runner.MOOD_KEYWORDS, which maps them onto track
# filenames. test_formats pins the two together.
MUSIC_MOODS: dict[str, str] = {
    "calm": "Calm — ambient, unobtrusive",
    "energetic": "Energetic — upbeat and driving",
    "melancholy": "Melancholy — sad, heavy",
    "tender": "Tender — bittersweet, warm",
    "uplifting": "Uplifting — hopeful, inspired",
}

# Narration pace in words per second. Presets rather than a free number:
# tts.rate_for clamps the derived rate to [-45%, +25%] anyway, so values
# outside this range would be silently capped and the creator would think
# the control was broken.
# These set how fast the VOICE speaks, and nothing else. They used to double
# as "how unhurried does this feel", which is why poetry pointed at the
# slowest one — and 1.2 asks edge-tts for -52%, clamped to its -45% floor,
# which sounds like a recording played slowly rather than someone reciting.
# Unhurried now comes from silence between the lines (services/rhythm.py), so
# these labels describe delivery only.
NARRATION_PACES: dict[float, str] = {
    1.2: "Very slow — deliberate, every word weighed",
    1.6: "Slow — lyrical, room to breathe",
    2.0: "Measured — motivational",
    2.2: "Relaxed — poetry and shayari, with pauses between lines",
    2.5: "Natural — storytelling",
    2.8: "Fast — news and updates",
}

# --- Editing grammar -------------------------------------------------------
#
# Until now every format rendered identically: hard cuts, one Ken Burns speed,
# three-word captions. But a shayari and a news update are not the same video
# in different colours. They differ in how long a shot is held, whether shots
# cut or dissolve, how fast the frame moves, and whether a caption pops word
# by word or holds a whole line. That is the part a viewer reads as "this was
# edited by someone who watches this kind of video", and it lives here.
#
# A format names only what differs from EDITING_DEFAULT, and the default IS
# today's behaviour — so a format that says nothing renders exactly as before.

MOTIONS: dict[str, str] = {
    "kenburns": "Steady push, alternating direction - the default shorts look",
    "drift": "Almost imperceptible creep - the frame breathes rather than moves",
    "punch": "Fast push in - urgency, news and gaming",
    "still": "No movement at all",
}

TRANSITIONS: dict[str, str] = {
    "cut": "Hard cut straight from one shot to the next",
    "soft": "A short fade at each shot's edges - reads as a breath, not a blackout",
}

EDITING_DEFAULT: dict = {
    "motion": "kenburns",
    "transition": "cut",
    "fade": 0.0,          # seconds, per edge; only used when transition="soft"
    "words_per_cue": 3,   # captions.MAX_WORDS_PER_CUE
    # Hold the whole segment on screen exactly as written, line breaks kept.
    # For a format with no narration the text is not a caption tracking a
    # voice — it IS the video.
    "caption_hold": False,
    # Silence, in seconds. line_pause sits between the lines of one segment
    # (the two misras of a sher); pause_after sits between segments. This is
    # where a poetic rhythm actually comes from — see tts.py.
    "line_pause": 0.0,
    "pause_after": 0.0,
    # Delivery speed for the VOICE only, separate from words_per_second,
    # which budgets how many words a segment may contain. Keeping them apart
    # is what lets a format write short lines AND speak them naturally.
    "speech_wps": None,
}


def editing_for(fmt: dict | None) -> dict:
    """A format's editing grammar, with anything unspecified filled in."""
    out = dict(EDITING_DEFAULT)
    out.update((fmt or {}).get("editing") or {})
    return out


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
    # A format's look and pace are as much a part of it as its voice. Without
    # these every format fell back to the generic default, so a shayari was
    # rendered as corporate flat-vector art narrated at news pace.
    if fmt.get("visual_style"):
        out["visual_style"] = fmt["visual_style"]
    if fmt.get("words_per_second"):
        # script_data's words_per_second drives ONE thing: how fast the voice
        # speaks. The writing budget lives in the format's script_recipe text,
        # not here. So a format that separates the two (shayari writes at 1.2
        # w/s but is SPOKEN at 2.2, with silence filling the rest) must seed
        # the creator's pace control with the speaking rate.
        out["words_per_second"] = editing_for(fmt).get("speech_wps") or fmt["words_per_second"]
    # How this format is CUT, not just how it looks. Always emitted (filled
    # from defaults) so the renderer never has to guess what a format wanted.
    out["editing"] = editing_for(fmt)
    return out
