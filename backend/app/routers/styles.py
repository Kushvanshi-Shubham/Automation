"""Teach a style — learn a personal format from the creator's own reels.

The creator picks 2-20 of their reference reels (already uploaded and
transcribed via media-assets); a worker distills them into a reusable
script recipe (app.pipeline.style_tasks) that script generation can apply
like a built-in format under the key "user:<id>".
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.middleware.rate_limit import rate_limit
from app.models.asset import Asset
from app.models.user import User
from app.models.user_format import UserFormat

router = APIRouter(prefix="/styles", tags=["Styles"], dependencies=[Depends(get_current_user)])

MAX_STYLES_PER_USER = 5
MIN_REELS, MAX_REELS = 2, 20
OUTPUT_TYPES = {"narrated", "visual"}


class StyleLearnRequest(BaseModel):
    name: str = Field(min_length=2, max_length=60)
    asset_ids: list[UUID] = Field(min_length=MIN_REELS, max_length=MAX_REELS)
    output_type: str = "narrated"  # narrated | visual


@router.post("/learn", dependencies=[Depends(rate_limit("style_learn"))])
async def start_learning(
    req: StyleLearnRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Learn a style from the creator's reference reels (async — poll GET /styles)."""
    from app.services import plans

    plans.require(current_user, "teach_style")
    if req.output_type not in OUTPUT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Output type must be 'narrated' or 'visual'",
        )

    count = await db.scalar(
        select(func.count(UserFormat.id)).where(UserFormat.user_id == current_user.id)
    )
    if (count or 0) >= MAX_STYLES_PER_USER:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Style limit reached — delete one first",
        )

    for asset_id in req.asset_ids:
        asset = await db.get(Asset, asset_id)
        if asset is None or asset.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"Asset {asset_id} doesn't exist in your library",
            )
        if asset.kind != "video":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"'{asset.filename}' is audio-only — reference reels must be video",
            )
        if asset.status != "ready":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"'{asset.filename}' is still being analyzed — wait for it to finish",
            )
        if not asset.transcript:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"'{asset.filename}' has no transcript to learn from",
            )

    uf = UserFormat(
        user_id=current_user.id,
        name=req.name.strip(),
        status="learning",
        output_type=req.output_type,
        source_asset_ids=[str(a) for a in req.asset_ids],
    )
    db.add(uf)
    await db.commit()
    await db.refresh(uf)

    from app.pipeline.style_tasks import learn_style
    learn_style.delay(str(uf.id))

    return {"id": uf.id, "status": uf.status}


@router.get("")
async def list_styles(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rows = (
        await db.execute(
            select(UserFormat)
            .where(UserFormat.user_id == current_user.id)
            .order_by(UserFormat.created_at.desc())
        )
    ).scalars().all()
    return {"items": [
        {
            "id": r.id,
            "name": r.name,
            "status": r.status,
            "error_message": r.error_message,
            "output_type": r.output_type,
            "profile": r.profile,
            "script_recipe": r.script_recipe,
            "created_at": r.created_at,
        }
        for r in rows
    ]}


@router.delete("/{style_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_style(
    style_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    row = await db.get(UserFormat, style_id)
    if row is None or row.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Style not found")
    await db.delete(row)
    await db.commit()
