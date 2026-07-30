"""AI image generation via Gemini image models (BYO key aware).

Used by the image-post output type (carousels) and later for thumbnails.
Models are tried in preference order — Google retires/renames image models
frequently, so hardcoding one name is fragile.
"""
import logging

from app.config import settings

logger = logging.getLogger("kliptos.image_gen")

MODEL_PREFERENCE = [
    "gemini-2.5-flash-image",
    "gemini-3.1-flash-image-preview",
    "gemini-3-pro-image-preview",
]

STYLE_SUFFIX = (
    " Vertical portrait composition (4:5), vivid, high detail, social-media ready, "
    "no text, no watermarks, no borders."
)


def _client(user_keys: dict[str, str] | None = None):
    from google import genai

    key = (user_keys or {}).get("gemini") or settings.GEMINI_API_KEY
    if not key:
        raise RuntimeError("No Gemini key available for image generation")
    return genai.Client(api_key=key)


async def generate_image(prompt: str, out_path, user_keys: dict[str, str] | None = None) -> str:
    """Generate one image, write bytes to out_path. Returns the model used."""
    client = _client(user_keys)
    last_error: Exception | None = None
    for model in MODEL_PREFERENCE:
        try:
            resp = await client.aio.models.generate_content(
                model=model,
                contents=prompt + STYLE_SUFFIX,
            )
            for part in resp.candidates[0].content.parts:
                inline = getattr(part, "inline_data", None)
                if inline and inline.data:
                    with open(out_path, "wb") as f:
                        f.write(inline.data)
                    return model
            raise RuntimeError("model returned no image data")
        except Exception as exc:
            logger.warning("image model %s failed: %s", model, exc)
            last_error = exc
    raise RuntimeError(f"all image models failed: {last_error}")
