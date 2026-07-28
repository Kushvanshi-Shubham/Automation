from fastapi import APIRouter, Depends
from typing import Any

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/overview")
async def get_analytics_overview() -> Any:
    """Get channel performance overview."""
    return {"views": 0, "subscribers": 0, "likes": 0}

@router.get("/videos")
async def get_video_analytics() -> Any:
    """Get analytics per video."""
    return {"items": []}
