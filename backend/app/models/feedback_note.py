import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, Uuid, func

from app.database import Base


class FeedbackNote(Base):
    """A standing creator note ("captions bigger", "face in first 3 seconds")
    applied to every future script generation — the self-improving loop."""

    __tablename__ = "feedback_notes"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid, ForeignKey("users.id"), nullable=False, index=True)
    # Format key from services/formats.py; NULL = applies to every video
    format = Column(String, nullable=True)
    note = Column(String(300), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
