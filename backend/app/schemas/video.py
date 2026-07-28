from pydantic import BaseModel, ConfigDict
from uuid import UUID
from typing import Optional, List, Dict, Any
from datetime import datetime

class VideoResponse(BaseModel):
    id: UUID
    status: str
    title: Optional[str]
    description: Optional[str]
    tags: Optional[List[str]]
    video_url: Optional[str]
    thumbnail_url: Optional[str]
    scheduled_at: Optional[datetime]
    published_at: Optional[datetime]
    created_at: Optional[datetime]
    model_config = ConfigDict(from_attributes=True)

class VideoListResponse(BaseModel):
    items: List[VideoResponse]
    total: int

class VideoMetadataUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
