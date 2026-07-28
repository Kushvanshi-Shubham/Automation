from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.credit import CreditLedger
from app.models.pipeline_job import PipelineJob
from app.models.user import User
from app.models.video import Video
from app.schemas.pipeline import PipelineStartRequest, PipelineStatusResponse

router = APIRouter(prefix="/pipeline", tags=["Pipeline"], dependencies=[Depends(get_current_user)])

# Variable credit pricing per engine — see docs/kliptos-vault/Pricing.md
ENGINE_CREDIT_COST = {"pexels": 1, "stock": 1}


@router.post("/start", response_model=PipelineStatusResponse)
async def start_pipeline(
    req: PipelineStartRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    video = await db.get(Video, req.video_id)
    if video is None or video.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")
    if not (video.script_data or {}).get("segments"):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Video has no script yet")
    if video.status == "rendering":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Video is already rendering")

    engine = req.visual_engine or "pexels"
    cost = ENGINE_CREDIT_COST.get(engine)
    if cost is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Visual engine '{engine}' is not available yet",
        )
    if current_user.credit_balance < cost:
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="Not enough credits")

    # Deduct credits through the ledger before dispatching.
    current_user.credit_balance -= cost
    video.credits_used = cost
    video.visual_engine = engine
    db.add(CreditLedger(user_id=current_user.id, amount=-cost, type="video_debit",
                        description=f"Render ({engine})", video_id=video.id))

    job = PipelineJob(video_id=video.id, user_id=current_user.id, status="queued",
                      progress={"stage": "queued", "percent": 0})
    db.add(job)
    await db.flush()
    job_id = job.id

    from app.pipeline.tasks import run_pipeline
    task = run_pipeline.delay(str(job_id))
    job.celery_task_id = task.id
    await db.commit()

    return {"job_id": job_id, "status": "queued", "progress": {"stage": "queued", "percent": 0}, "error_message": None}


@router.get("/{job_id}", response_model=PipelineStatusResponse)
async def get_pipeline_status(
    job_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    job = await db.get(PipelineJob, job_id)
    if job is None or job.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return {"job_id": job.id, "status": job.status, "progress": job.progress, "error_message": job.error_message}


@router.post("/{job_id}/cancel")
async def cancel_pipeline(job_id: UUID):
    # Safe cancellation (kill ffmpeg mid-render + refund) is a later milestone.
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Cancel not yet available")
