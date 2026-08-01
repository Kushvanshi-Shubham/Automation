import uuid
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, Uuid, func, JSON
from app.database import Base


class Asset(Base):
    """Creator-owned media (the rights-cleared rail): uploaded long-form
    video/audio that Kliptos transcribes and mines for clip highlights."""
    __tablename__ = "assets"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid, ForeignKey("users.id"), nullable=False, index=True)

    filename = Column(String, nullable=False)
    kind = Column(String, default="video")  # video | audio
    path = Column(String, nullable=False)
    size_bytes = Column(Integer, nullable=True)
    duration = Column(Float, nullable=True)

    # uploaded -> processing -> ready | failed
    status = Column(String, default="uploaded", nullable=False)
    error_message = Column(Text, nullable=True)

    # {"segments": [{"start", "end", "text", "words": [{"word","start","end"}]}], "language": "en"}
    transcript = Column(JSON, nullable=True)
    # [{"start", "end", "title", "reason"}]
    highlights = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
