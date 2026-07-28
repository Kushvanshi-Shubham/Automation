from fastapi import APIRouter, Depends, HTTPException, status

from app.middleware.auth import get_current_user

router = APIRouter(prefix="/analytics", tags=["Analytics"], dependencies=[Depends(get_current_user)])

_not_ready = HTTPException(
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
    detail="Analytics land in S2",
)


@router.get("/overview")
async def get_analytics_overview():
    raise _not_ready


@router.get("/videos")
async def get_video_analytics():
    raise _not_ready
