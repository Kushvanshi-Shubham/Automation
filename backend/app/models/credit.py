import uuid
from sqlalchemy import Column, String, Integer, DateTime, Uuid, func, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class CreditLedger(Base):
    __tablename__ = "credit_ledger"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid, ForeignKey("users.id"), nullable=False, index=True)
    amount = Column(Integer, nullable=False)
    # purchase | subscription_grant | video_debit | refund | admin_adjustment
    type = Column(String, nullable=False)
    description = Column(String, nullable=True)
    stripe_session_id = Column(String, nullable=True)
    video_id = Column(Uuid, ForeignKey("videos.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="credits")
