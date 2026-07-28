from fastapi import APIRouter, Depends
from app.schemas.pipeline import PipelineStartRequest, PipelineStatusResponse
from uuid import UUID
from typing import Any

router = APIRouter(prefix="/pipeline", tags=["Pipeline"])

@router.post("/start", response_model=PipelineStatusResponse)
async def start_pipeline(req: PipelineStartRequest) -> Any:
    """Start the video generation pipeline."""
    return {"job_id": "00000000-0000-0000-0000-000000000000", "status": "queued", "progress": {}, "error_message": None}

@router.get("/{job_id}", response_model=PipelineStatusResponse)
async def get_pipeline_status(job_id: UUID) -> Any:
    """Get pipeline job status."""
    return {"job_id": job_id, "status": "running", "progress": {}, "error_message": None}

@router.post("/{job_id}/cancel")
async def cancel_pipeline(job_id: UUID) -> Any:
    """Cancel a running pipeline job."""
    return {"status": "cancelled"}
