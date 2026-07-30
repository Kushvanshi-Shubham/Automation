"""Curated edge-tts voice catalog + preview generation.

edge-tts exposes 400+ neural voices for free; we curate a quality shortlist
per language so the picker stays usable. Previews are synthesized once and
cached under OUTPUT_DIR/voice_previews/.
"""
import logging
from pathlib import Path

from app.config import settings

logger = logging.getLogger("kliptos.voices")

# label, edge-tts voice id, language, gender, vibe
VOICES: list[dict] = [
    # English (US)
    {"id": "en-US-ChristopherNeural", "label": "Christopher", "language": "English (US)", "gender": "male", "vibe": "Deep & confident — the classic shorts voice"},
    {"id": "en-US-GuyNeural", "label": "Guy", "language": "English (US)", "gender": "male", "vibe": "Warm storyteller"},
    {"id": "en-US-EricNeural", "label": "Eric", "language": "English (US)", "gender": "male", "vibe": "Casual & friendly"},
    {"id": "en-US-JennyNeural", "label": "Jenny", "language": "English (US)", "gender": "female", "vibe": "Bright & energetic"},
    {"id": "en-US-AriaNeural", "label": "Aria", "language": "English (US)", "gender": "female", "vibe": "Smooth narrator"},
    # English (UK / AU)
    {"id": "en-GB-RyanNeural", "label": "Ryan", "language": "English (UK)", "gender": "male", "vibe": "British documentary"},
    {"id": "en-GB-SoniaNeural", "label": "Sonia", "language": "English (UK)", "gender": "female", "vibe": "Elegant British"},
    {"id": "en-AU-NatashaNeural", "label": "Natasha", "language": "English (AU)", "gender": "female", "vibe": "Upbeat Aussie"},
    # English (India)
    {"id": "en-IN-PrabhatNeural", "label": "Prabhat", "language": "English (India)", "gender": "male", "vibe": "Clear Indian English"},
    {"id": "en-IN-NeerjaNeural", "label": "Neerja", "language": "English (India)", "gender": "female", "vibe": "Warm Indian English"},
    # Hindi
    {"id": "hi-IN-MadhurNeural", "label": "Madhur", "language": "Hindi", "gender": "male", "vibe": "स्पष्ट और दमदार"},
    {"id": "hi-IN-SwaraNeural", "label": "Swara", "language": "Hindi", "gender": "female", "vibe": "मधुर और आकर्षक"},
    # Spanish / Portuguese (creator-heavy markets)
    {"id": "es-MX-JorgeNeural", "label": "Jorge", "language": "Spanish (MX)", "gender": "male", "vibe": "Narrador cálido"},
    {"id": "pt-BR-AntonioNeural", "label": "Antonio", "language": "Portuguese (BR)", "gender": "male", "vibe": "Narrador brasileiro"},
]

VALID_VOICE_IDS = {v["id"] for v in VOICES}

# What the preview says, per language family
PREVIEW_TEXT = {
    "hi": "नमस्ते! आपके शॉर्ट्स ऐसे सुनाई देंगे। ट्रेंडिंग से वायरल तक, क्लिप्टोस के साथ।",
    "es": "¡Hola! Así sonarán tus videos cortos. De tendencia a viral, con Kliptos.",
    "pt": "Olá! Seus vídeos curtos vão soar assim. Da tendência ao viral, com Kliptos.",
    "default": "Hey! This is how your shorts will sound. From trending topic to viral video, with Kliptos.",
}

LANGUAGES = [
    "English", "Hindi", "Spanish", "Portuguese",
]


def preview_dir() -> Path:
    d = Path(settings.OUTPUT_DIR) / "voice_previews"
    d.mkdir(parents=True, exist_ok=True)
    return d


async def get_preview(voice_id: str) -> str:
    """Synthesize (once) and return the media URL of a voice preview."""
    if voice_id not in VALID_VOICE_IDS:
        raise ValueError("unknown voice")
    out = preview_dir() / f"{voice_id}.mp3"
    if not out.exists() or out.stat().st_size == 0:
        import edge_tts

        lang = voice_id.split("-")[0]
        text = PREVIEW_TEXT.get(lang, PREVIEW_TEXT["default"])
        await edge_tts.Communicate(text, voice_id).save(str(out))
        logger.info("voice preview generated: %s", voice_id)
    return f"/media/voice_previews/{voice_id}.mp3"
