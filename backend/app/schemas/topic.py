from pydantic import BaseModel
from uuid import UUID
from typing import List, Optional
from datetime import datetime

class TopicResponse(BaseModel):
    id: UUID
    title: str
    source: Optional[str]
    keywords: Optional[List[str]]
    score: Optional[float]
    hook_text: Optional[str]
    discovered_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class TopicListResponse(BaseModel):
    items: List[TopicResponse]
