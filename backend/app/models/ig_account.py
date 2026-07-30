import uuid
from sqlalchemy import Column, String, Boolean, DateTime, Uuid, func, ForeignKey
from app.database import Base


class IgAccount(Base):
    __tablename__ = "ig_accounts"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid, ForeignKey("users.id"), nullable=False, index=True)
    ig_user_id = Column(String, unique=True, nullable=False)
    username = Column(String, nullable=True)
    page_id = Column(String, nullable=True)
    # Fernet-encrypted long-lived user token (~60 days) — write via encrypt_token only.
    access_token = Column(String, nullable=True)
    token_expires_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
