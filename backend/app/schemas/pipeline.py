from pydantic import BaseModel
from uuid import UUID
from typing import Optional, Dict, Any

class PipelineStartRequest(BaseModel):
    # Studio-grade narration: "cartesia" | "elevenlabs" (Pro). None = free
    # edge-tts. voice_id then refers to that provider's voice.
    voice_provider: Optional[str] = None
    # Look of AI-generated scenes: explainer | cinematic | documentary | bold
    visual_style: Optional[str] = None
    # Caption craft — same knobs the free proof render offers.
    caption_animation: Optional[str] = None
    caption_font: Optional[str] = None
    caption_color: Optional[str] = None
    video_id: UUID
    visual_engine: str = "stock"
    voice_id: Optional[str] = None
    caption_style: Optional[str] = None
    aspect_ratio: Optional[str] = None

class PipelineStatusResponse(BaseModel):
    job_id: UUID
    status: str
    progress: Optional[Dict[str, Any]]
    error_message: Optional[str]

class PipelineProgressMessage(BaseModel):
    job_id: UUID
    status: str
    stage: str
    percent: float
