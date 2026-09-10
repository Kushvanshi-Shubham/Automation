import uuid
from sqlalchemy import Column, String, Integer, DateTime, Uuid, func
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    google_id = Column(String, unique=True, index=True, nullable=True)
    credit_balance = Column(Integer, default=0, nullable=False)
    # When the monthly allowance was last topped up. Per-user rather than a
    # calendar month, so signing up on the 30th does not earn a second
    # month's credits the next day.
    credits_granted_at = Column(DateTime(timezone=True), nullable=True)
    plan = Column(String, default="free", nullable=False)
    # creator | brand | admin
    role = Column(String, default="creator", nullable=False)
    country = Column(String, nullable=True)
    # First-run answers. niche defaults the trend filter, language defaults
    # the script language; onboarded_at decides whether to ask at all, and
    # is set even when the questions are skipped so nobody is asked twice.
    niche = Column(String, nullable=True)
    language = Column(String, nullable=True)
    onboarded_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    channels = relationship("Channel", back_populates="user")
    videos = relationship("Video", back_populates="user")
    credits = relationship("CreditLedger", back_populates="user")
    pipeline_jobs = relationship("PipelineJob", back_populates="user")
