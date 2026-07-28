from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.middleware.auth import get_current_user
from app.schemas.script import ScriptGenerateRequest, ScriptRegenerateRequest

router = APIRouter(prefix="/scripts", tags=["Scripts"], dependencies=[Depends(get_current_user)])

_not_ready = HTTPException(
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
    detail="Script generation lands in the script-studio milestone of S1",
)


@router.post("/generate")
async def generate_script(req: ScriptGenerateRequest):
    raise _not_ready


@router.put("/{id}")
async def update_script(id: UUID, data: dict):
    raise _not_ready


@router.post("/{id}/regenerate-segment")
async def regenerate_segment(id: UUID, req: ScriptRegenerateRequest):
    raise _not_ready


@router.post("/{id}/preview-voice")
async def preview_voice(id: UUID, voice_id: str):
    raise _not_ready
