from pydantic import BaseModel
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
    
    class Config:
        from_attributes = True

class VideoListResponse(BaseModel):
    items: List[VideoResponse]
    total: int

class VideoMetadataUpdate(BaseModel):
    title: Optional[str]
    description: Optional[str]
    tags: Optional[List[str]]
