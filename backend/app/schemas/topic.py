from pydantic import BaseModel, ConfigDict
from uuid import UUID
from typing import List, Optional
from datetime import datetime

class TopicResponse(BaseModel):
    id: UUID
    title: str
    source: Optional[str]
    category: Optional[str] = None
    best_format: Optional[str] = None
    format_reason: Optional[str] = None
    keywords: Optional[List[str]]
    score: Optional[float]
    hook_text: Optional[str]
    discovered_at: Optional[datetime]
    model_config = ConfigDict(from_attributes=True)

class TopicListResponse(BaseModel):
    items: List[TopicResponse]
