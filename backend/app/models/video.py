import uuid
from sqlalchemy import Column, String, Integer, Text, DateTime, func, ForeignKey, JSON, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.database import Base

PortableJSON = JSON().with_variant(JSONB(), "postgresql")


class Video(Base):
    __tablename__ = "videos"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid, ForeignKey("users.id"), nullable=False, index=True)
    channel_id = Column(Uuid, ForeignKey("channels.id"), nullable=True, index=True)

    status = Column(String, default="draft")
    title = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    tags = Column(PortableJSON, nullable=True)
    script_data = Column(PortableJSON, nullable=True)
    visual_engine = Column(String, nullable=True)

    video_url = Column(String, nullable=True)
    thumbnail_url = Column(String, nullable=True)
    youtube_video_id = Column(String, nullable=True)

    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    credits_used = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="videos")
    channel = relationship("Channel", back_populates="videos")
    pipeline_jobs = relationship("PipelineJob", back_populates="video")
