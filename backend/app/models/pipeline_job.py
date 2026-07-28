import uuid
from sqlalchemy import Column, String, Text, DateTime, Uuid, func, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database import Base


class PipelineJob(Base):
    __tablename__ = "pipeline_jobs"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    video_id = Column(Uuid, ForeignKey("videos.id"), nullable=False, index=True)
    user_id = Column(Uuid, ForeignKey("users.id"), nullable=False, index=True)

    celery_task_id = Column(String, nullable=True)
    status = Column(String, default="queued")
    progress = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)

    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    video = relationship("Video", back_populates="pipeline_jobs")
    user = relationship("User", back_populates="pipeline_jobs")
