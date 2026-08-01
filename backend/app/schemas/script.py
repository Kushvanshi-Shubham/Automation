from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID


class ScriptGenerateRequest(BaseModel):
    topic_id: Optional[UUID] = None
    custom_prompt: Optional[str] = None
    # Bring-your-own-script: wording preserved, only segmented + visual-prompted.
    custom_script: Optional[str] = None
    # script (free, no render) | narrated (voice) | visual (on-screen text, no voice)
    output_type: str = "narrated"
    # viral_story | news_update | educational | commentary
    style: str = "viral_story"
    tone: str = "engaging and curious"
    duration_seconds: int = Field(default=60, ge=15, le=180)
    # auto | gemini | openai
    model: str = "auto"
    # Script language (also drives the default voice choice in the UI)
    language: str = "English"
    # Extra creator guidance appended to the generation prompt
    custom_instructions: Optional[str] = Field(default=None, max_length=600)


class ScriptSegment(BaseModel):
    text: str
    visual_prompt: str = ""
    duration_estimate: float = 0.0
    # User-pinned stock media for this scene (Pexels id + preview thumbnail)
    media_id: Optional[int] = None
    media_thumb: Optional[str] = None


class ScriptResponse(BaseModel):
    video_id: UUID
    segments: List[ScriptSegment]
    total_duration: float
    output_type: str = "narrated"


class ScriptUpdateRequest(BaseModel):
    segments: List[ScriptSegment]


class ScriptRegenerateRequest(BaseModel):
    segment_index: int
    feedback: str
