"""Feedback notes — "what should be different next time".

Small CRUD; the notes are consumed by app.services.feedback at generation
time. Notes are short standing instructions, not per-video comments.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.middleware.rate_limit import rate_limit
from app.models.feedback_note import FeedbackNote
from app.models.user import User

router = APIRouter(prefix="/feedback-notes", tags=["Feedback"], dependencies=[Depends(get_current_user)])

MAX_NOTES_PER_USER = 30


class NoteCreate(BaseModel):
    note: str = Field(min_length=3, max_length=300)
    format: Optional[str] = None


class NoteResponse(BaseModel):
    id: UUID
    format: Optional[str]
    note: str
    created_at: Optional[datetime]
    model_config = ConfigDict(from_attributes=True)


@router.get("")
async def list_notes(
    format: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """All standing notes; ?format= narrows to that format's notes + global ones."""
    q = (
        select(FeedbackNote)
        .where(FeedbackNote.user_id == current_user.id)
        .order_by(FeedbackNote.created_at.desc())
    )
    rows = (await db.execute(q)).scalars().all()
    if format is not None:
        rows = [r for r in rows if r.format is None or r.format == format]
    return {"items": [NoteResponse.model_validate(r) for r in rows]}


@router.post("", response_model=NoteResponse, dependencies=[Depends(rate_limit("feedback_note"))])
async def create_note(
    req: NoteCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.services.formats import FORMATS

    # "user:<uuid>" = a learned personal style (routers/styles.py)
    if req.format is not None and not req.format.startswith("user:") and req.format not in FORMATS:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Unknown format")

    count = await db.scalar(
        select(func.count(FeedbackNote.id)).where(FeedbackNote.user_id == current_user.id)
    )
    if (count or 0) >= MAX_NOTES_PER_USER:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Note limit reached ({MAX_NOTES_PER_USER}) — delete old notes first",
        )

    row = FeedbackNote(user_id=current_user.id, format=req.format, note=req.note.strip())
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(
    note_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    row = await db.get(FeedbackNote, note_id)
    if row is None or row.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    await db.delete(row)
    await db.commit()
