from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.topic import Topic
from app.schemas.topic import TopicListResponse

router = APIRouter(prefix="/topics", tags=["Topics"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=TopicListResponse)
async def get_topics(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Topic).order_by(Topic.score.desc()).limit(50))
    return {"items": result.scalars().all()}


@router.post("/refresh")
async def refresh_topics():
    # Lands with the trend-harvester milestone of S1.
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Topic harvester not yet available")


@router.post("/custom")
async def custom_topic(prompt: str):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Custom topics not yet available")
