from sqlalchemy import Column, DateTime, func, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base
import uuid

class UserInteraction(Base):
    __tablename__ = "article_reads" # Using 'article_reads' table from init.sql which seems to map to interactions

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    article_id = Column(UUID(as_uuid=True), ForeignKey("articles.id"), primary_key=True)
    read_at = Column(DateTime(timezone=True), server_default=func.now())
    # The diagram has 'liked' boolean, but init.sql only has 'article_reads'. 
    # I will stick to 'article_reads' for now as per init.sql, or should I create a new table?
    # The diagram shows 'UserInteraction' entity with 'is_liked'.
    # I'll add 'liked' here, but note that it might not exist in the current init.sql.
    # For now, let's assume we can extend the schema or this maps to a new table.
    # Actually, let's create a separate model 'UserInteraction' if 'article_reads' is just for history.
    # But for simplicity, I'll assume we want to track likes.
    
    # Let's define a new table for explicit interactions if needed, or modify this one.
    # Given the diagram shows 'UserInteraction' with 'is_liked', I'll define it as such.
    # If I use a table name not in init.sql, I rely on SQLAlchemy to create it (if I run create_all) 
    # or I should update init.sql.
    # For now, I will map it to a new table 'user_interactions' to avoid conflict with 'article_reads'.
    
    __tablename__ = "user_interactions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    article_id = Column(UUID(as_uuid=True), ForeignKey("articles.id"))
    is_liked = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
