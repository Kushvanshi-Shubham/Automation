import uuid
from sqlalchemy import Column, String, Text, DateTime, Uuid, func, ForeignKey
from app.database import Base


class Publish(Base):
    """One row per (video, platform) publish attempt — the multi-platform ledger.

    YouTube currently also writes legacy columns on Video; new platforms
    (Instagram onward) live here exclusively.
    """
    __tablename__ = "publishes"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    video_id = Column(Uuid, ForeignKey("videos.id"), nullable=False, index=True)
    user_id = Column(Uuid, ForeignKey("users.id"), nullable=False, index=True)
    platform = Column(String, nullable=False)  # instagram | youtube | ...
    status = Column(String, default="publishing")  # publishing | published | failed
    external_id = Column(String, nullable=True)  # IG media id / YT video id
    caption = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    published_at = Column(DateTime(timezone=True), nullable=True)
