import uuid
from sqlalchemy import Column, String, Text, DateTime, func, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class PipelineJob(Base):
    __tablename__ = "pipeline_jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_id = Column(UUID(as_uuid=True), ForeignKey("videos.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    celery_task_id = Column(String, nullable=True)
    status = Column(String, default="queued")
    progress = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    video = relationship("Video", back_populates="pipeline_jobs")
    user = relationship("User", back_populates="pipeline_jobs")
