import uuid
from sqlalchemy import Column, String, Boolean, DateTime, Uuid, func, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Channel(Base):
    __tablename__ = "channels"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid, ForeignKey("users.id"), nullable=False, index=True)
    youtube_channel_id = Column(String, unique=True, nullable=True)
    channel_name = Column(String, nullable=True)
    # Fernet-encrypted at rest — write via app.core.security.encrypt_token only.
    access_token = Column(String, nullable=True)
    refresh_token = Column(String, nullable=True)
    token_expires_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="channels")
    videos = relationship("Video", back_populates="channel")
