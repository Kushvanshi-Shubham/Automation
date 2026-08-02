from datetime import datetime, time, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.topic import Topic
from app.models.user import User
from app.models.video import Video
from app.schemas.script import ScriptGenerateRequest, ScriptResponse, ScriptRegenerateRequest, ScriptUpdateRequest
from app.services import script_gen
from app.services.llm import VALID_MODELS, available_models
from app.services.user_keys import get_user_keys

router = APIRouter(prefix="/scripts", tags=["Scripts"], dependencies=[Depends(get_current_user)])

OUTPUT_TYPES = {"script", "narrated", "visual", "image"}
FREE_SCRIPT_ONLY_PER_DAY = 5

VISUAL_TYPE_NOTE = (
    "IMPORTANT: this script's lines will be displayed as ON-SCREEN TEXT with no narration "
    "(music-driven video). Keep every segment under 12 punchy words, readable at a glance."
)
IMAGE_TYPE_NOTE = (
    "IMPORTANT: this is an IMAGE CAROUSEL post (3-6 slides), not a video. Each segment is one "
    "slide: text = a short punchy slide caption (under 15 words), visual_prompt = a detailed "
    "image description for that slide. The first slide must hook, the last must conclude."
)


@router.get("/formats")
async def list_formats():
    """The format catalog: each format is a full pipeline recipe."""
    from app.services.formats import FORMATS

    return {"items": [
        {"key": k, "label": f["label"], "emoji": f["emoji"], "desc": f["desc"],
         "output_type": f["output_type"], "available": f["available"], "controls": f["controls"]}
        for k, f in FORMATS.items()
    ]}


@router.get("/voices")
async def list_voices():
    """Curated narration voices + supported script languages."""
    from app.services.voices import LANGUAGES, VOICES

    return {"voices": VOICES, "languages": LANGUAGES}


@router.get("/voices/{voice_id}/preview")
async def voice_preview(voice_id: str):
    """Returns the media URL of a short sample for this voice (cached)."""
    from app.services.voices import get_preview

    try:
        url = await get_preview(voice_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown voice")
    return {"preview_url": url}


@router.get("/models")
async def list_models(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """LLM choices for this user: platform models + the user's own keys."""
    user_keys = await get_user_keys(db, current_user.id)
    return {"items": available_models(user_keys)}


async def _get_owned_video(video_id: UUID, db: AsyncSession, user: User) -> Video:
    video = await db.get(Video, video_id)
    if video is None or video.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")
    return video


@router.post("/generate", response_model=ScriptResponse)
async def generate_script(
    req: ScriptGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate a script from a topic, a custom prompt, or the user's own script text."""
    from app.services.formats import DEFAULT_TONE, FORMATS, render_defaults

    fmt = None
    if req.format:
        fmt = FORMATS.get(req.format)
        if fmt is None:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Unknown format")
        if not fmt["available"]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"The {fmt['label']} format isn't available yet",
            )
        # The format IS the recipe: it decides engine, style, and defaults.
        req.output_type = fmt["output_type"]
        req.style = fmt["style"]
        if req.tone == DEFAULT_TONE and fmt.get("tone"):
            req.tone = fmt["tone"]
        if req.language == "English" and fmt.get("language"):
            req.language = fmt["language"]

    if req.style not in script_gen.STYLE_PROMPTS:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Unknown style")
    if req.model not in VALID_MODELS:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Unknown model")
    if req.output_type not in OUTPUT_TYPES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Unknown output type")

    # Script-only is free — rate-limited so it can't be farmed.
    if req.output_type == "script":
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        count_today = await db.scalar(
            select(func.count(Video.id)).where(
                Video.user_id == current_user.id,
                Video.output_type == "script",
                Video.created_at >= today_start,
            )
        )
        if (count_today or 0) >= FREE_SCRIPT_ONLY_PER_DAY:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Free script limit reached ({FREE_SCRIPT_ONLY_PER_DAY}/day) — try again tomorrow",
            )

    user_keys = await get_user_keys(db, current_user.id)

    instructions = req.custom_instructions
    if req.output_type == "visual":
        instructions = f"{VISUAL_TYPE_NOTE}\n{instructions or ''}".strip()
    elif req.output_type == "image":
        instructions = f"{IMAGE_TYPE_NOTE}\n{instructions or ''}".strip()
    if fmt is not None and fmt.get("script_recipe"):
        instructions = f"{fmt['script_recipe']}\n{instructions or ''}".strip()

    hook_hint = None
    if req.custom_script:
        if len(req.custom_script.strip()) < 40:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Your script is too short — write at least a few sentences",
            )
        subject = "user-written script"
        script = await script_gen.format_custom_script(req.custom_script, model=req.model, user_keys=user_keys)
    else:
        if req.topic_id is not None:
            topic = await db.get(Topic, req.topic_id)
            if topic is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")
            subject = topic.title
            hook_hint = topic.hook_text
        elif req.custom_prompt:
            subject = req.custom_prompt.strip()
            if len(subject) < 10:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Custom prompt too short")
        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Provide topic_id, custom_prompt, or custom_script",
            )
        script = await script_gen.generate_script(
            topic=subject,
            hook_hint=hook_hint,
            tone=req.tone,
            duration_seconds=req.duration_seconds,
            style=req.style,
            custom_instructions=instructions,
            model=req.model,
            user_keys=user_keys,
            language=req.language,
        )

    script_data = {
        "subject": subject,
        "tone": req.tone,
        "style": "custom" if req.custom_script else req.style,
        "segments": script["segments"],
        "total_duration": script["total_duration"],
    }
    if fmt is not None:
        script_data["format"] = req.format
        script_data.update(render_defaults(fmt))

    video = Video(
        user_id=current_user.id,
        status="script_ready",
        output_type=req.output_type,
        title=script.get("title"),
        description=script.get("description"),
        tags=script.get("tags"),
        script_data=script_data,
    )
    db.add(video)
    await db.commit()
    await db.refresh(video)

    return {
        "video_id": video.id,
        "segments": script["segments"],
        "total_duration": script["total_duration"],
        "output_type": video.output_type,
        "format": req.format,
        "defaults": render_defaults(fmt) if fmt else None,
    }


@router.get("/{video_id}", response_model=ScriptResponse)
async def get_script(
    video_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    video = await _get_owned_video(video_id, db, current_user)
    data = video.script_data or {}
    defaults = {k: data[k] for k in ("voice_id", "caption_style", "music_mood", "background_query") if data.get(k)}
    return {
        "video_id": video.id,
        "segments": data.get("segments", []),
        "total_duration": data.get("total_duration", 0.0),
        "output_type": video.output_type,
        "format": data.get("format"),
        "defaults": defaults or None,
    }


@router.put("/{video_id}", response_model=ScriptResponse)
async def update_script(
    video_id: UUID,
    req: ScriptUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Save user edits to the script segments."""
    video = await _get_owned_video(video_id, db, current_user)
    segments = [s.model_dump() for s in req.segments]
    total = round(sum(s["duration_estimate"] for s in segments), 1)
    video.script_data = {**(video.script_data or {}), "segments": segments, "total_duration": total}
    await db.commit()
    return {"video_id": video.id, "segments": segments, "total_duration": total, "output_type": video.output_type}


@router.post("/{video_id}/regenerate-segment", response_model=ScriptResponse)
async def regenerate_segment(
    video_id: UUID,
    req: ScriptRegenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    video = await _get_owned_video(video_id, db, current_user)
    data = video.script_data or {}
    segments = data.get("segments", [])
    if not 0 <= req.segment_index < len(segments):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="segment_index out of range")

    new_segment = await script_gen.regenerate_segment(
        topic=data.get("subject", video.title or ""),
        full_script=segments,
        segment_index=req.segment_index,
        feedback=req.feedback,
    )
    segments = [*segments]
    segments[req.segment_index] = new_segment
    total = round(sum(float(s.get("duration_estimate", 0)) for s in segments), 1)
    video.script_data = {**data, "segments": segments, "total_duration": total}
    await db.commit()
    return {"video_id": video.id, "segments": segments, "total_duration": total, "output_type": video.output_type}


@router.get("/{video_id}/segments/{segment_index}/media-options")
async def segment_media_options(
    video_id: UUID,
    segment_index: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Stock media candidates for one scene (video clips, or photos for image posts)."""
    import httpx

    from app.pipeline.visuals import pexels as pexels_service

    video = await _get_owned_video(video_id, db, current_user)
    segments = (video.script_data or {}).get("segments", [])
    if not 0 <= segment_index < len(segments):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="segment_index out of range")

    seg = segments[segment_index]
    query = seg.get("visual_prompt") or seg.get("text") or ""
    media = "photo" if video.output_type == "image" else "video"
    async with httpx.AsyncClient(timeout=30) as client:
        items = await pexels_service.search_candidates(client, query, media=media)
    return {"items": items, "query": query}


@router.post("/{video_id}/preview-voice")
async def preview_voice(video_id: UUID, voice_id: str):
    # Lands with the edge-tts milestone.
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Voice preview not yet available")
