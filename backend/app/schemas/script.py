from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID

class ScriptGenerateRequest(BaseModel):
    topic_id: Optional[UUID] = None
    custom_prompt: Optional[str] = None
    duration_seconds: int = 60

class ScriptSegment(BaseModel):
    text: str
    visual_prompt: str
    duration_estimate: float

class ScriptResponse(BaseModel):
    video_id: UUID
    segments: List[ScriptSegment]
    total_duration: float

class ScriptRegenerateRequest(BaseModel):
    segment_index: int
    feedback: str
