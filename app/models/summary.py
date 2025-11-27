from sqlalchemy import Column, DateTime, func, ForeignKey, ARRAY, Text
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base
import uuid

class DailySummary(Base):
    __tablename__ = "daily_summaries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    article_ids = Column(ARRAY(UUID(as_uuid=True)))
    summary_generated_at = Column(DateTime(timezone=True), server_default=func.now())
    # Adding summary_text as it's in the diagram, though missing in init.sql (we might need to migrate DB or just assume it exists)
    summary_text = Column(Text)
