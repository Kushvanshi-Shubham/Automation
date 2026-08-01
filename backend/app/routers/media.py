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
from app.models.asset import Asset
from app.models.user import User

router = APIRouter(prefix="/media-assets", tags=["Media"], dependencies=[Depends(get_current_user)])

ALLOWED_EXTENSIONS = {".mp4", ".mov", ".webm", ".mkv", ".mp3", ".m4a", ".wav"}
AUDIO_EXTENSIONS = {".mp3", ".m4a", ".wav"}
MAX_SIZE_BYTES = 500 * 1024 * 1024  # 500MB local-first cap
MAX_ASSETS_PER_USER = 10  # until object storage exists


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


@router.post("", response_model=AssetResponse)
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
    with open(dest, "wb") as out:
        while chunk := await file.read(4 * 1024 * 1024):
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
