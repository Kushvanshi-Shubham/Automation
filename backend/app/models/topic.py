import uuid
from sqlalchemy import Column, String, Float, DateTime, Uuid, func, JSON
from app.database import Base


class Topic(Base):
    __tablename__ = "topics"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    source = Column(String, nullable=True)
    keywords = Column(JSON, nullable=True)
    score = Column(Float, nullable=True)
    hook_text = Column(String, nullable=True)
    content_hash = Column(String, unique=True, nullable=False)

    discovered_at = Column(DateTime(timezone=True), server_default=func.now())
