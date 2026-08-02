import shutil
import uuid as uuid_mod
from datetime import datetime
from pathlib import Path
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.middleware.auth import get_current_user
from app.middleware.rate_limit import rate_limit
from app.models.asset import Asset
from app.models.credit import CreditLedger
from app.models.pipeline_job import PipelineJob
from app.models.user import User
from app.models.video import Video

router = APIRouter(prefix="/media-assets", tags=["Media"], dependencies=[Depends(get_current_user)])

ALLOWED_EXTENSIONS = {".mp4", ".mov", ".webm", ".mkv", ".mp3", ".m4a", ".wav"}
AUDIO_EXTENSIONS = {".mp3", ".m4a", ".wav"}
MAX_SIZE_BYTES = 500 * 1024 * 1024  # 500MB local-first cap
MAX_ASSETS_PER_USER = 10  # until object storage exists

CLIP_CREDIT_COST = 1
MIN_CLIP_SECONDS = 5
MAX_CLIP_SECONDS = 90


def _looks_like_media(head: bytes, ext: str) -> bool:
    """Magic-byte sniff of the first upload chunk — the extension alone is
    attacker-controlled. Kept permissive (containers vary); ffprobe in the
    worker is the final arbiter."""
    if len(head) < 12:
        return False
    if ext in (".mp4", ".mov", ".m4a"):
        return head[4:8] == b"ftyp"
    if ext in (".webm", ".mkv"):
        return head[:4] == b"\x1a\x45\xdf\xa3"
    if ext == ".mp3":
        return head[:3] == b"ID3" or (head[0] == 0xFF and (head[1] & 0xE0) == 0xE0)
    if ext == ".wav":
        return head[:4] == b"RIFF" and head[8:12] == b"WAVE"
    return False


class AssetResponse(BaseModel):
    id: UUID
    filename: str
    kind: str
    size_bytes: Optional[int]
    duration: Optional[float]
    status: str
    error_message: Optional[str]
    highlights: Optional[list] = None
    created_at: Optional[datetime]
    model_config = ConfigDict(from_attributes=True)


def _uploads_dir(user_id) -> Path:
    d = Path(settings.OUTPUT_DIR) / "uploads" / str(user_id)
    d.mkdir(parents=True, exist_ok=True)
    return d


@router.post("", response_model=AssetResponse, dependencies=[Depends(rate_limit("media_upload"))])
async def upload_asset(
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload creator-owned long-form media for clip mining (rights-cleared rail)."""
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Unsupported file type '{ext}' — use mp4/mov/webm/mkv or mp3/m4a/wav",
        )
    count = len((await db.execute(select(Asset.id).where(Asset.user_id == current_user.id))).all())
    if count >= MAX_ASSETS_PER_USER:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Upload limit reached ({MAX_ASSETS_PER_USER}) — delete an old upload first",
        )

    asset_id = uuid_mod.uuid4()
    dest = _uploads_dir(current_user.id) / f"{asset_id}{ext}"
    size = 0
    first_chunk = True
    with open(dest, "wb") as out:
        while chunk := await file.read(4 * 1024 * 1024):
            if first_chunk:
                first_chunk = False
                if not _looks_like_media(chunk[:16], ext):
                    out.close()
                    dest.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                        detail="File content doesn't match its extension",
                    )
            size += len(chunk)
            if size > MAX_SIZE_BYTES:
                out.close()
                dest.unlink(missing_ok=True)
                raise HTTPException(
                    status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                    detail="File exceeds the 500MB limit",
                )
            out.write(chunk)

    asset = Asset(
        id=asset_id,
        user_id=current_user.id,
        filename=file.filename or f"upload{ext}",
        kind="audio" if ext in AUDIO_EXTENSIONS else "video",
        path=str(dest),
        size_bytes=size,
        status="uploaded",
    )
    db.add(asset)
    await db.commit()
    await db.refresh(asset)

    from app.pipeline.asset_tasks import process_asset
    process_asset.delay(str(asset.id))

    return asset


@router.get("", response_model=list[AssetResponse])
async def list_assets(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Asset).where(Asset.user_id == current_user.id).order_by(Asset.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset(
    asset_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    asset = await db.get(Asset, asset_id)
    if asset is None or asset.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    return asset


class ClipCreateRequest(BaseModel):
    start: float
    end: float
    title: Optional[str] = None
    caption_style: Optional[str] = None
    aspect_ratio: Optional[str] = None


@router.post("/{asset_id}/clips", dependencies=[Depends(rate_limit("clip_create"))])
async def create_clip(
    asset_id: UUID,
    req: ClipCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Render a highlight from an uploaded asset as a 9:16 short (1 credit):
    trim + center-crop + word-synced captions, original audio kept."""
    asset = await db.get(Asset, asset_id)
    if asset is None or asset.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    if asset.status != "ready":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Asset is still being analyzed" if asset.status in ("uploaded", "processing")
            else "Asset processing failed — re-upload it",
        )
    if asset.kind != "video":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Audio-only uploads can't be clipped into video yet",
        )

    start, end = round(float(req.start), 2), round(float(req.end), 2)
    if start < 0 or end <= start:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Invalid clip range")
    if not (MIN_CLIP_SECONDS <= end - start <= MAX_CLIP_SECONDS):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Clip must be {MIN_CLIP_SECONDS}–{MAX_CLIP_SECONDS} seconds long",
        )
    if asset.duration and start >= asset.duration:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Clip starts past the end of the video")
    if asset.duration and end > asset.duration + 0.5:
        end = round(asset.duration, 2)

    if req.caption_style:
        from app.pipeline.captions import CAPTION_STYLES

        if req.caption_style not in CAPTION_STYLES:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Unknown caption style")

    if req.aspect_ratio:
        from app.pipeline.assembler import ASPECT_RATIOS

        if req.aspect_ratio not in ASPECT_RATIOS:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Unknown aspect ratio")

    if current_user.credit_balance < CLIP_CREDIT_COST:
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="Not enough credits")

    # Fresh video row born in "rendering" — no claim race possible.
    script_data: dict = {"clip": {"asset_id": str(asset.id), "start": start, "end": end}}
    if req.caption_style:
        script_data["caption_style"] = req.caption_style
    if req.aspect_ratio:
        script_data["aspect_ratio"] = req.aspect_ratio
    video = Video(
        user_id=current_user.id,
        title=(req.title or f"Clip from {asset.filename}")[:100],
        status="rendering",
        output_type="clip",
        visual_engine="source",
        credits_used=CLIP_CREDIT_COST,
        script_data=script_data,
    )
    current_user.credit_balance -= CLIP_CREDIT_COST
    db.add(video)
    await db.flush()
    db.add(CreditLedger(user_id=current_user.id, amount=-CLIP_CREDIT_COST, type="video_debit",
                        description="Clip render (your footage)", video_id=video.id))
    job = PipelineJob(video_id=video.id, user_id=current_user.id, status="queued",
                      progress={"stage": "queued", "percent": 0})
    db.add(job)
    await db.flush()
    video_id, job_id = video.id, job.id
    await db.commit()

    # Enqueue only after commit — the job must be durable before the worker sees it.
    from app.pipeline.tasks import run_pipeline
    task = run_pipeline.delay(str(job_id))
    job.celery_task_id = task.id
    await db.commit()

    return {"video_id": video_id, "job_id": job_id, "status": "queued"}


@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_asset(
    asset_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    asset = await db.get(Asset, asset_id)
    if asset is None or asset.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    Path(asset.path).unlink(missing_ok=True)
    await db.delete(asset)
    await db.commit()
