import logging
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.middleware.rate_limit import rate_limit
from app.models.credit import CreditLedger
from app.models.pipeline_job import PipelineJob
from app.models.user import User
from app.models.video import Video
from app.schemas.pipeline import PipelineStartRequest, PipelineStatusResponse
from pydantic import BaseModel
from typing import Optional

from app.services.progress import publish_progress
from app.services.user_keys import get_user_keys

logger = logging.getLogger("kliptos.pipeline")

router = APIRouter(prefix="/pipeline", tags=["Pipeline"], dependencies=[Depends(get_current_user)])

# Variable credit pricing per engine — see docs/kliptos-vault/Pricing.md
ENGINE_CREDIT_COST = {"pexels": 1, "stock": 1, "stock_image": 1, "ai_image": 2}
# Re-rendering the SAME content with a different caption look / voice /
# aspect is free this many times per video (real cost ≈ $0.002).
FREE_RESTYLES_PER_VIDEO = 3
# Which engines fit which output type. ai_image on a video type means every
# scene is a generated illustration with pan/zoom instead of stock footage.
TYPE_ENGINES: dict[str, set[str]] = {
    "narrated": {"pexels", "stock", "ai_image"},
    "visual": {"pexels", "stock", "ai_image"},
    "fake_text": {"pexels", "stock"},
    "image": {"stock_image", "ai_image"},
}


@router.get("/caption-styles")
async def list_caption_styles():
    """Available caption looks for the studio picker."""
    from app.pipeline.captions import CAPTION_STYLES

    return {"items": [{"key": k, "label": v["label"], "desc": v["desc"]} for k, v in CAPTION_STYLES.items()]}


@router.get("/look-options")
async def look_options():
    """Everything a creator can change about how a video LOOKS, in one call:
    caption packs, animations, fonts, and AI visual styles."""
    from app.pipeline.captions import (
        CAPTION_ANIMATIONS, CAPTION_FONTS, CAPTION_STYLES,
        DEFAULT_CAPTION_ANIMATION, DEFAULT_CAPTION_FONT, DEFAULT_CAPTION_STYLE,
    )
    from app.services.image_gen import DEFAULT_VISUAL_STYLE, VISUAL_STYLES

    return {
        "caption_styles": [
            {"key": k, "label": v["label"], "desc": v["desc"]} for k, v in CAPTION_STYLES.items()
        ],
        "caption_animations": [
            {"key": k, "label": v["label"], "desc": v["desc"]} for k, v in CAPTION_ANIMATIONS.items()
        ],
        "caption_fonts": [{"key": k, "label": v["label"]} for k, v in CAPTION_FONTS.items()],
        "visual_styles": [{"key": k, "label": k.title()} for k in VISUAL_STYLES],
        "defaults": {
            "caption_style": DEFAULT_CAPTION_STYLE,
            "caption_animation": DEFAULT_CAPTION_ANIMATION,
            "caption_font": DEFAULT_CAPTION_FONT,
            "visual_style": DEFAULT_VISUAL_STYLE,
        },
        "free_restyles_per_video": FREE_RESTYLES_PER_VIDEO,
    }


@router.get("/aspect-ratios")
async def list_aspect_ratios():
    """Available output aspect ratios for the studio picker."""
    from app.pipeline.assembler import ASPECT_RATIOS

    return {"items": [
        {"key": k, "label": v["label"], "desc": v["desc"], "width": v["w"], "height": v["h"]}
        for k, v in ASPECT_RATIOS.items()
    ]}


@router.post("/start", response_model=PipelineStatusResponse, dependencies=[Depends(rate_limit("pipeline_start"))])
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
    if video.output_type == "script":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="This is a script-only creation — there is nothing to render",
        )
    if video.status in ("rendering", "publishing"):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Video is already being processed")

    engine = req.visual_engine or ("stock_image" if video.output_type == "image" else "pexels")
    # Credit price comes from the engine's real cost x margin, so a render
    # can never be sold below what it costs us (services/credits.py).
    from app.services.credits import engine_credit_cost

    scene_count = len((video.script_data or {}).get("segments") or [])
    cost = engine_credit_cost(engine, scenes=scene_count) if engine in ENGINE_CREDIT_COST else None
    if cost is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Visual engine '{engine}' is not available yet",
        )
    if engine not in TYPE_ENGINES.get(video.output_type, set()):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Engine '{engine}' doesn't fit a {video.output_type} creation",
        )

    # Restyling something already paid for is free. Changing the CONTENT
    # (visual engine, or narration provider) is a new render and costs
    # again — a caption tweak costs us a fifth of a cent, so charging for
    # it would just teach creators not to polish their work.
    from app.services.credits import is_free_restyle

    data = video.script_data or {}
    restyle_allowance = int(data.get("restyles_used") or 0)
    is_restyle = is_free_restyle(
        has_render=video.video_url is not None,
        credits_used=video.credits_used or 0,
        current_engine=video.visual_engine,
        requested_engine=engine,
        current_voice_provider=data.get("voice_provider"),
        requested_voice_provider=req.voice_provider,
        restyles_used=restyle_allowance,
        allowance=FREE_RESTYLES_PER_VIDEO,
    )
    if is_restyle:
        cost = 0
    elif current_user.credit_balance < cost:
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="Not enough credits")

    from app.services import plans, premium_voice

    if req.voice_provider:
        # Studio-grade narration: Pro only, and it costs extra credits
        # because it costs us real money (services/credits.py).
        if req.voice_provider not in premium_voice.PROVIDERS:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Unknown narration provider"
            )
        plans.require(current_user, "premium_voice")
        if not req.voice_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Pick a voice for that narration provider",
            )
        user_keys = await get_user_keys(db, current_user.id)
        if not (user_keys.get(req.voice_provider) or premium_voice.platform_key(req.voice_provider)):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"Add your {req.voice_provider.title()} key in Settings to use those voices",
            )
        # The creator's own key is their spend — no surcharge for BYO.
        if not user_keys.get(req.voice_provider):
            from app.services.credits import ENGINE_REAL_COST_USD, credits_for_cost

            cost += credits_for_cost(ENGINE_REAL_COST_USD["premium_voice"])
            if current_user.credit_balance < cost:
                raise HTTPException(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    detail=f"Studio-grade narration needs {cost} credits in total",
                )
        video.script_data = {
            **(video.script_data or {}),
            "voice_provider": req.voice_provider,
            "voice_id": req.voice_id,
        }
    elif req.voice_id:
        from app.services.voices import VALID_VOICE_IDS

        if req.voice_id not in VALID_VOICE_IDS:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Unknown voice")
        video.script_data = {
            **(video.script_data or {}), "voice_id": req.voice_id, "voice_provider": None,
        }

    if req.caption_style:
        from app.pipeline.captions import CAPTION_STYLES

        if req.caption_style not in CAPTION_STYLES:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Unknown caption style")
        video.script_data = {**(video.script_data or {}), "caption_style": req.caption_style}

    if req.aspect_ratio:
        from app.pipeline.assembler import ASPECT_RATIOS

        if req.aspect_ratio not in ASPECT_RATIOS:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Unknown aspect ratio")
        video.script_data = {**(video.script_data or {}), "aspect_ratio": req.aspect_ratio}

    if req.visual_style:
        from app.services.image_gen import VISUAL_STYLES

        if req.visual_style not in VISUAL_STYLES:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Unknown visual style")
        video.script_data = {**(video.script_data or {}), "visual_style": req.visual_style}

    # Freeze this render's quality tier from the plan: the worker reads it
    # from script_data, so a plan change mid-render can't alter the output.
    from app.services import plans

    feats = plans.features(current_user)
    video.script_data = {
        **(video.script_data or {}),
        "tier": {"watermark": feats["watermark"], "height": feats["max_height"]},
    }
    if any(s.get("asset_id") for s in (video.script_data.get("segments") or [])):
        plans.require(current_user, "own_footage")

    # Atomically CLAIM the video (idempotency: double-clicks / concurrent
    # requests both pass the read check above, but only one wins this update).
    claim = await db.execute(
        update(Video)
        .where(Video.id == video.id, Video.status.notin_(["rendering", "publishing"]))
        .values(status="rendering")
    )
    if claim.rowcount == 0:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Video is already being processed")

    # Deduct credits through the ledger, create the job, and COMMIT — the job
    # must be durable before the worker can possibly pick it up. A free
    # restyle skips the debit but still counts against the allowance.
    video.visual_engine = engine
    if is_restyle:
        video.script_data = {**(video.script_data or {}), "restyles_used": restyle_allowance + 1}
    else:
        current_user.credit_balance -= cost
        video.credits_used = cost
        db.add(CreditLedger(user_id=current_user.id, amount=-cost, type="video_debit",
                            description=f"Render ({engine})", video_id=video.id))

    job = PipelineJob(video_id=video.id, user_id=current_user.id, status="queued",
                      progress={"stage": "queued", "percent": 0})
    db.add(job)
    await db.flush()
    job_id = job.id
    await db.commit()

    # Enqueue only after the commit; record the task id in a follow-up write.
    from app.pipeline.tasks import run_pipeline
    task = run_pipeline.delay(str(job_id))
    job.celery_task_id = task.id
    await db.commit()

    return {"job_id": job_id, "status": "queued", "progress": {"stage": "queued", "percent": 0}, "error_message": None}


@router.get("/active")
async def active_jobs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """All of this user's in-flight render jobs with live progress — the
    RAIL conveyor polls this to position every reel on real telemetry."""
    from sqlalchemy import select

    rows = (
        await db.execute(
            select(PipelineJob, Video)
            .join(Video, PipelineJob.video_id == Video.id)
            .where(PipelineJob.user_id == current_user.id, PipelineJob.status.in_(["queued", "running"]))
            .order_by(Video.created_at.desc())
            .limit(20)
        )
    ).all()
    return {
        "items": [
            {
                "job_id": job.id,
                "video_id": video.id,
                "status": job.status,
                "progress": job.progress or {"stage": "queued", "percent": 0},
            }
            for job, video in rows
        ]
    }


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


class ProofRequest(BaseModel):
    video_id: UUID
    scene_index: int = 0
    # Style choices to try out. Saved on the video so the full render uses
    # whatever the creator settled on in the proof.
    voice_id: Optional[str] = None
    voice_provider: Optional[str] = None
    caption_style: Optional[str] = None
    caption_animation: Optional[str] = None
    caption_font: Optional[str] = None
    caption_color: Optional[str] = None
    aspect_ratio: Optional[str] = None
    visual_style: Optional[str] = None
    visual_engine: Optional[str] = None


@router.post("/proof", dependencies=[Depends(rate_limit("pipeline_proof"))])
async def start_proof(
    req: ProofRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Render ONE scene, free, so style decisions cost nothing.

    No credits, no ledger entry, no change to the video's status — the
    output lives under proofs/ and never enters the library.
    """
    from app.pipeline.captions import CAPTION_ANIMATIONS, CAPTION_FONTS, CAPTION_STYLES
    from app.pipeline.assembler import ASPECT_RATIOS
    from app.services.image_gen import VISUAL_STYLES

    video = await db.get(Video, req.video_id)
    if video is None or video.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")
    if not (video.script_data or {}).get("segments"):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Generate a script first")
    if video.output_type == "script":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Script-only creations have nothing to preview",
        )

    allowed = {
        "caption_style": CAPTION_STYLES,
        "caption_animation": CAPTION_ANIMATIONS,
        "caption_font": CAPTION_FONTS,
        "aspect_ratio": ASPECT_RATIOS,
        "visual_style": VISUAL_STYLES,
    }
    updates: dict = {}
    for field, catalogue in allowed.items():
        value = getattr(req, field)
        if value is not None:
            if value not in catalogue:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail=f"Unknown {field.replace('_', ' ')}",
                )
            updates[field] = value
    if req.caption_color:
        from app.pipeline.captions import hex_to_ass

        if hex_to_ass(req.caption_color) is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Colour must look like #7C3AED",
            )
        updates["caption_color"] = req.caption_color
    if req.voice_provider or req.voice_id:
        from app.services import premium_voice
        from app.services.voices import VALID_VOICE_IDS

        if req.voice_provider:
            if req.voice_provider not in premium_voice.PROVIDERS:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Unknown narration provider")
            plans.require(current_user, "premium_voice")
            updates["voice_provider"] = req.voice_provider
        elif req.voice_id and req.voice_id not in VALID_VOICE_IDS:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Unknown voice")
        if req.voice_id:
            updates["voice_id"] = req.voice_id
        if req.voice_provider is None and req.voice_id:
            updates["voice_provider"] = None

    if req.visual_engine:
        if req.visual_engine not in ENGINE_CREDIT_COST:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Unknown visual engine")
        if req.visual_engine not in TYPE_ENGINES.get(video.output_type or "narrated", set()):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"Engine '{req.visual_engine}' doesn't fit a {video.output_type} creation",
            )
        video.visual_engine = req.visual_engine

    if updates:
        video.script_data = {**(video.script_data or {}), **updates}
    await db.commit()

    from app.pipeline.proof import render_proof

    render_proof.delay(str(video.id), req.scene_index)
    return {"video_id": video.id, "scene_index": req.scene_index, "status": "rendering"}


@router.get("/proof/{video_id}")
async def get_proof(
    video_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """The latest proof for this video, if one has finished."""
    video = await db.get(Video, video_id)
    if video is None or video.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")
    return {"proof": (video.script_data or {}).get("proof")}


@router.post("/{job_id}/cancel")
async def cancel_pipeline(
    job_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Give up on a render and get the credit back.

    Used when a job is stuck (no worker available, queue drained) — the
    creator should never be left holding a spent credit and a frozen
    page. A worker already past the ffmpeg stage may still finish; the
    revoke below asks it to stop, and the video simply returns to
    script_ready either way.
    """
    job = await db.get(PipelineJob, job_id)
    if job is None or job.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if job.status in ("completed", "failed"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="That render already finished — nothing to cancel",
        )

    video = await db.get(Video, job.video_id)
    refund = (video.credits_used or 0) if video else 0

    if job.celery_task_id:
        try:  # best effort — the queue may be unreachable
            from app.pipeline.celery_app import celery_app

            celery_app.control.revoke(job.celery_task_id, terminate=True)
        except Exception as exc:
            logger.warning("could not revoke task %s: %s", job.celery_task_id, exc)

    job.status = "failed"
    job.error_message = "Cancelled by the creator"
    job.completed_at = datetime.now(timezone.utc)
    job.progress = {"stage": "cancelled", "percent": 0}
    if video is not None:
        video.status = "script_ready"  # the script survives; render again anytime
        if refund:
            current_user.credit_balance += refund
            db.add(CreditLedger(
                user_id=current_user.id, amount=refund, type="refund",
                description="Render cancelled — credit returned", video_id=video.id,
            ))
            video.credits_used = 0
    await db.commit()

    try:
        publish_progress(str(job_id), status="failed", stage="cancelled", percent=0,
                         error="Cancelled by the creator")
    except Exception:
        pass
    return {"job_id": job.id, "status": "failed", "refunded_credits": refund}
