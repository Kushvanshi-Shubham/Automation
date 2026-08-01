from pydantic import BaseModel
from uuid import UUID
from typing import Optional, Dict, Any

class PipelineStartRequest(BaseModel):
    video_id: UUID
    visual_engine: str = "stock"
    voice_id: Optional[str] = None
    caption_style: Optional[str] = None

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
