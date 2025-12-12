from sqlalchemy import Column, DateTime, func, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base
import uuid

class UserInteraction(Base):
    __tablename__ = "user_interactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    synthesized_article_id = Column(UUID(as_uuid=True), ForeignKey("synthesized_articles.id"), nullable=True)
    is_liked = Column(Boolean, nullable=True, default=None)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    from sqlalchemy import UniqueConstraint
    __table_args__ = (
        UniqueConstraint('user_id', 'synthesized_article_id', name='_user_synth_article_uc'),
    )
