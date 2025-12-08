from sqlalchemy import Column, DateTime, func, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base
import uuid

class UserInteraction(Base):
    __tablename__ = "user_interactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    article_id = Column(UUID(as_uuid=True), ForeignKey("articles.id"))
    is_liked = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
