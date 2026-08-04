import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, Text, Uuid, func, JSON

from app.database import Base


class UserFormat(Base):
    """A style learned from the creator's own reference reels — a personal format."""

    __tablename__ = "user_formats"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid, ForeignKey("users.id"), nullable=False, index=True)

    name = Column(String(60), nullable=False)
    # learning -> ready | failed
    status = Column(String, default="learning", nullable=False)
    error_message = Column(Text, nullable=True)

    # {"summary", "reels", "avg_wps", "hooks"} — the analysis summary, for display
    profile = Column(JSON, nullable=True)
    script_recipe = Column(Text, nullable=True)
    caption_style = Column(String, nullable=True)
    music_mood = Column(String, nullable=True)
    tone = Column(String, nullable=True)
    output_type = Column(String, default="narrated", nullable=False)  # narrated | visual
    # The asset ids (as strings) this style was learned from
    source_asset_ids = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
