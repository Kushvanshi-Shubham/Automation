from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID


class ScriptGenerateRequest(BaseModel):
    topic_id: Optional[UUID] = None
    custom_prompt: Optional[str] = None
    tone: str = "engaging and curious"
    duration_seconds: int = Field(default=60, ge=15, le=180)


class ScriptSegment(BaseModel):
    text: str
    visual_prompt: str = ""
    duration_estimate: float = 0.0


class ScriptResponse(BaseModel):
    video_id: UUID
    segments: List[ScriptSegment]
    total_duration: float


class ScriptUpdateRequest(BaseModel):
    segments: List[ScriptSegment]


class ScriptRegenerateRequest(BaseModel):
    segment_index: int
    feedback: str
