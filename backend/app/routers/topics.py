from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.topic import Topic
from app.schemas.topic import TopicListResponse
from app.services.harvester import harvest_topics
from app.services.niches import NICHES, VALID_CATEGORIES

router = APIRouter(prefix="/topics", tags=["Topics"], dependencies=[Depends(get_current_user)])


@router.get("/niches")
async def list_niches():
    """Available niche filters (server-driven so UI stays in sync)."""
    return {"items": [{"key": k, "label": v["label"]} for k, v in NICHES.items()]}


@router.get("", response_model=TopicListResponse)
async def get_topics(category: str | None = None, db: AsyncSession = Depends(get_db)):
    query = select(Topic).order_by(Topic.score.desc()).limit(60)
    if category:
        if category not in VALID_CATEGORIES:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Unknown category")
        query = query.where(Topic.category == category)
    result = await db.execute(query)
    return {"items": result.scalars().all()}


@router.post("/refresh")
async def refresh_topics(db: AsyncSession = Depends(get_db)):
    """Harvest fresh topics from Google Trends + Reddit (deduped by content hash)."""
    return await harvest_topics(db)


@router.post("/custom")
async def custom_topic(prompt: str):
    # Lands with the script-studio milestone (LLM-expanded custom topics).
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Custom topics not yet available")
