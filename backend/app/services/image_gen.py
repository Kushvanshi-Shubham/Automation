"""AI image generation via Gemini image models (BYO key aware).

Used by the image-post output type (carousels) and later for thumbnails.
Models are tried in preference order — Google retires/renames image models
frequently, so hardcoding one name is fragile.
"""
import logging

from app.config import settings

logger = logging.getLogger("kliptos.image_gen")

# Verified against Vertex 2026-08-17. The "-preview" ids that used to be here
# 404 on Vertex; these four are live. Newest-and-cheapest first, pro last as a
# quality fallback.
MODEL_PREFERENCE = [
    "gemini-3.1-flash-image",
    "gemini-2.5-flash-image",
    "gemini-3-pro-image",
]

# Retired. It appended "Vertical portrait composition (4:5)" to every prompt —
# AFTER scene_prompt had already specified the real aspect, so a 9:16 scene
# carried two contradictory composition instructions, and 4:5 is not even in
# _ASPECT_FRAMING. It survived because it was the ONLY styling the carousel
# path got: that path passed a raw prompt straight to generate_image and never
# called scene_prompt. Both paths go through scene_prompt now, so the suffix
# has no job left.

# Per-aspect framing so a generated scene fills the frame without letterboxing.
_ASPECT_FRAMING = {
    "9:16": "Vertical portrait composition (9:16), full-bleed",
    "1:1": "Square composition (1:1), centred subject",
    "16:9": "Wide cinematic composition (16:9), full-bleed",
}

# Looks for a whole video. "explainer" is the one that suits product films:
# clean, on-brand, no stock-photo cheese.
VISUAL_STYLES = {
    "explainer": (
        "Modern flat vector illustration, clean geometric shapes, generous negative space, "
        "restrained 2-3 colour palette, subtle depth, professional and corporate"
    ),
    "cinematic": (
        "Cinematic photographic still, shallow depth of field, dramatic natural light, "
        "filmic colour grade, photorealistic"
    ),
    "documentary": (
        "Documentary photograph, natural available light, candid framing, realistic, "
        "unstaged, muted colours"
    ),
    "bold": (
        "Bold graphic poster art, high contrast, saturated colour blocking, "
        "strong silhouettes, striking and simple"
    ),
}
DEFAULT_VISUAL_STYLE = "explainer"


def scene_prompt(
    subject: str,
    aspect: str = "9:16",
    style: str = DEFAULT_VISUAL_STYLE,
    says: str | None = None,
) -> str:
    """Prompt for one scene's illustration — framed for the target aspect.

    `says` is the narration this scene accompanies. It is passed as context
    rather than as the subject, because a visual_prompt written for a stock
    library ("gaming setups, RGB keyboards") can be entirely disconnected
    from what the line is about — which is exactly how a video about a
    vehicle patch ended up illustrated with a photo of a keyboard. Giving
    the model the line as well means a thin prompt still lands near the
    subject instead of far from it.

    Text is banned on purpose: captions and headlines are burned in later,
    and generated lettering is almost always misspelled.
    """
    framing = _ASPECT_FRAMING.get(aspect, _ASPECT_FRAMING["9:16"])
    look = VISUAL_STYLES.get(style, VISUAL_STYLES[DEFAULT_VISUAL_STYLE])
    context = ""
    if says and says.strip() and says.strip() != subject.strip():
        # Trimmed: the point is the subject matter, not the full sentence.
        context = f" It illustrates this line: \"{' '.join(says.split())[:160]}\"."
    return (
        f"{subject.strip()}.{context} {look}. {framing}. "
        "Absolutely no text, no words, no letters, no numbers, no logos, no watermarks, no borders."
    )


def _client(user_keys: dict[str, str] | None = None):
    from app.services.google_ai import gemini_client

    client, _ = gemini_client((user_keys or {}).get("gemini"))
    return client


async def generate_image(
    prompt: str,
    out_path,
    user_keys: dict[str, str] | None = None,
    aspect: str = "9:16",
) -> str:
    """Generate one image, write bytes to out_path. Returns the model used."""
    from google.genai import types

    client = _client(user_keys)
    # Asking for the aspect in the prompt does NOT work — the models return
    # 1024x1024 regardless. image_config is what actually reframes the output
    # (verified: 9:16 -> 768x1344), which matters because a square scene would
    # have to be cropped and would cut the subject.
    config = types.GenerateContentConfig(
        image_config=types.ImageConfig(aspect_ratio=aspect)
    )
    last_error: Exception | None = None
    for model in MODEL_PREFERENCE:
        try:
            resp = await client.aio.models.generate_content(
                model=model,
                contents=prompt,
                config=config,
            )
            if not resp.candidates:
                raise RuntimeError("model returned no candidates (likely filtered)")
            for part in resp.candidates[0].content.parts:
                inline = getattr(part, "inline_data", None)
                if inline and inline.data:
                    with open(out_path, "wb") as f:
                        f.write(inline.data)
                    # Counted here, on success only — a filtered or failed
                    # call bills nothing. Without this the economics panel
                    # reported 100% margin no matter what this lane burned,
                    # because it was never counted at all.
                    try:
                        from app.services.costs import track

                        track("ai_image")
                    except Exception:  # accounting must never fail a render
                        pass
                    return model
            raise RuntimeError("model returned no image data")
        except Exception as exc:
            logger.warning("image model %s failed: %s", model, exc)
            last_error = exc
    raise RuntimeError(f"all image models failed: {last_error}")
