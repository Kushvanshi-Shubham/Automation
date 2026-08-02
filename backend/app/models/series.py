import uuid
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, Uuid, func
from app.database import Base


class Series(Base):
    """Autopilot: recurring creation (and optionally publishing) of shorts."""
    __tablename__ = "series"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid, ForeignKey("users.id"), nullable=False, index=True)

    name = Column(String, nullable=False)
    # niche key (services.niches) — None = all niches
    category = Column(String, nullable=True)
    # optional theme, e.g. "Apex Legends updates" — overrides trend picking
    topic_prompt = Column(Text, nullable=True)

    # format key (services.formats) — the full pipeline recipe for every run;
    # None = custom (style/output_type below apply directly)
    format = Column(String, nullable=True)
    style = Column(String, default="viral_story", nullable=False)
    output_type = Column(String, default="narrated", nullable=False)  # narrated | visual
    language = Column(String, default="English", nullable=False)
    voice_id = Column(String, nullable=True)

    interval_hours = Column(Integer, default=24, nullable=False)
    # auto_publish: render → straight to YouTube; otherwise stop at "ready" for review
    auto_publish = Column(Boolean, default=False, nullable=False)
    channel_id = Column(Uuid, ForeignKey("channels.id"), nullable=True)
    publish_privacy = Column(String, default="unlisted", nullable=False)

    is_active = Column(Boolean, default=True, nullable=False)
    last_run_at = Column(DateTime(timezone=True), nullable=True)
    next_run_at = Column(DateTime(timezone=True), nullable=True, index=True)
    last_error = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
