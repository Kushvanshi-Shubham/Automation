from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.middleware.auth import get_current_user

router = APIRouter(prefix="/uploads", tags=["Uploads"], dependencies=[Depends(get_current_user)])

_not_ready = HTTPException(
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
    detail="YouTube publishing lands in the publish milestone of S1",
)


@router.post("/{video_id}/publish")
async def publish_video(video_id: UUID, channel_id: UUID):
    raise _not_ready


@router.post("/{video_id}/schedule")
async def schedule_video(video_id: UUID, channel_id: UUID, scheduled_time: str):
    raise _not_ready


@router.get("")
async def list_uploads():
    raise _not_ready
