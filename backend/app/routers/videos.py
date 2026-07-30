from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.models.video import Video
from app.schemas.video import VideoListResponse, VideoMetadataUpdate, VideoResponse

router = APIRouter(prefix="/videos", tags=["Videos"], dependencies=[Depends(get_current_user)])


async def _get_owned_video(video_id: UUID, db: AsyncSession, user: User) -> Video:
    video = await db.get(Video, video_id)
    if video is None or video.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")
    return video


@router.get("", response_model=VideoListResponse)
async def list_videos(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)

    total = await db.scalar(select(func.count(Video.id)).where(Video.user_id == current_user.id))
    result = await db.execute(
        select(Video)
        .where(Video.user_id == current_user.id)
        .order_by(Video.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return {"items": result.scalars().all(), "total": total or 0}


@router.get("/{id}", response_model=VideoResponse)
async def get_video(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    video = await _get_owned_video(id, db, current_user)
    resp = VideoResponse.model_validate(video)
    resp.images = (video.script_data or {}).get("images")
    return resp


@router.put("/{id}/metadata", response_model=VideoResponse)
async def update_video_metadata(
    id: UUID,
    req: VideoMetadataUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    video = await _get_owned_video(id, db, current_user)
    for field, value in req.model_dump(exclude_unset=True).items():
        setattr(video, field, value)
    await db.commit()
    await db.refresh(video)
    return video


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_video(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    video = await _get_owned_video(id, db, current_user)
    await db.delete(video)
    await db.commit()
