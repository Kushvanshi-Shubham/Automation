"""Feedback memory — standing creator notes folded into every generation.

The video-editor loop: after each render the creator says what should be
different next time ("captions bigger", "no static screens"). Notes are
stored per format (or globally) and appended to the script-generation
instructions so the system stops repeating corrected mistakes.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.feedback_note import FeedbackNote

# How many notes reach the prompt — newest first, format-specific and global mixed.
MAX_NOTES_IN_PROMPT = 8


async def feedback_block(db: AsyncSession, user_id, format_key: str | None) -> str | None:
    """The prompt block of this user's standing notes, or None if they have none.

    Includes global notes (format IS NULL) plus notes for the given format.
    """
    q = (
        select(FeedbackNote)
        .where(FeedbackNote.user_id == user_id)
        .order_by(FeedbackNote.created_at.desc())
        .limit(50)
    )
    rows = (await db.execute(q)).scalars().all()
    picked = [r for r in rows if r.format is None or r.format == format_key][:MAX_NOTES_IN_PROMPT]
    if not picked:
        return None
    lines = "\n".join(f"- {r.note}" for r in picked)
    return (
        "The creator has given standing feedback on previous videos. "
        "Apply ALL of it to this script:\n" + lines
    )
