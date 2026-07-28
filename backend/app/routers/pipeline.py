from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.middleware.auth import get_current_user
from app.schemas.pipeline import PipelineStartRequest

router = APIRouter(prefix="/pipeline", tags=["Pipeline"], dependencies=[Depends(get_current_user)])

_not_ready = HTTPException(
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
    detail="Video pipeline lands in the pipeline milestone of S1",
)


@router.post("/start")
async def start_pipeline(req: PipelineStartRequest):
    raise _not_ready


@router.get("/{job_id}")
async def get_pipeline_status(job_id: UUID):
    raise _not_ready


@router.post("/{job_id}/cancel")
async def cancel_pipeline(job_id: UUID):
    raise _not_ready
