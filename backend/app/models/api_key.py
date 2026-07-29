import uuid
from sqlalchemy import Column, DateTime, String, UniqueConstraint, Uuid, func, ForeignKey
from app.database import Base


class UserApiKey(Base):
    """A user's own LLM provider key (BYO keys). Fernet-encrypted at rest."""
    __tablename__ = "user_api_keys"
    __table_args__ = (UniqueConstraint("user_id", "provider", name="uq_user_provider"),)

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid, ForeignKey("users.id"), nullable=False, index=True)
    # gemini | openai
    provider = Column(String, nullable=False)
    key_encrypted = Column(String, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
