from pydantic import BaseModel, ConfigDict
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
    model_config = ConfigDict(from_attributes=True)

class TopicListResponse(BaseModel):
    items: List[TopicResponse]
