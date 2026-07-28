from fastapi import APIRouter, Depends
from app.schemas.topic import TopicListResponse
from typing import Any

router = APIRouter(prefix="/topics", tags=["Topics"])

@router.get("", response_model=TopicListResponse)
async def get_topics() -> Any:
    """Get list of trending topics."""
    return {"items": []}

@router.post("/refresh")
async def refresh_topics() -> Any:
    """Trigger background task to discover new topics."""
    return {"status": "started"}

@router.post("/custom")
async def custom_topic(prompt: str) -> Any:
    """Create a custom topic from prompt."""
    return {"status": "created"}
