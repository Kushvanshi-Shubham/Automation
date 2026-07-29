from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
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
    if req.style not in script_gen.STYLE_PROMPTS:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Unknown style")
    if req.model not in VALID_MODELS:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Unknown model")

    user_keys = await get_user_keys(db, current_user.id)

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
            custom_instructions=req.custom_instructions,
            model=req.model,
            user_keys=user_keys,
        )

    video = Video(
        user_id=current_user.id,
        status="script_ready",
        title=script.get("title"),
        description=script.get("description"),
        tags=script.get("tags"),
        script_data={
            "subject": subject,
            "tone": req.tone,
            "style": "custom" if req.custom_script else req.style,
            "segments": script["segments"],
            "total_duration": script["total_duration"],
        },
    )
    db.add(video)
    await db.commit()
    await db.refresh(video)

    return {
        "video_id": video.id,
        "segments": script["segments"],
        "total_duration": script["total_duration"],
    }


@router.get("/{video_id}", response_model=ScriptResponse)
async def get_script(
    video_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    video = await _get_owned_video(video_id, db, current_user)
    data = video.script_data or {}
    return {
        "video_id": video.id,
        "segments": data.get("segments", []),
        "total_duration": data.get("total_duration", 0.0),
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
    return {"video_id": video.id, "segments": segments, "total_duration": total}


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
    return {"video_id": video.id, "segments": segments, "total_duration": total}


@router.post("/{video_id}/preview-voice")
async def preview_voice(video_id: UUID, voice_id: str):
    # Lands with the edge-tts milestone.
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Voice preview not yet available")
