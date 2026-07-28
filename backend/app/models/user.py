import uuid
from sqlalchemy import Column, String, Integer, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    google_id = Column(String, unique=True, index=True, nullable=True)
    credit_balance = Column(Integer, default=0, nullable=False)
    plan = Column(String, default="free", nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    channels = relationship("Channel", back_populates="user")
    videos = relationship("Video", back_populates="user")
    credits = relationship("CreditLedger", back_populates="user")
    pipeline_jobs = relationship("PipelineJob", back_populates="user")
