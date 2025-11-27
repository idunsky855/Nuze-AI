from sqlalchemy import Column, String, DateTime, func, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from pgvector.sqlalchemy import Vector
from app.database import Base
import uuid

class Article(Base):
    __tablename__ = "articles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    source_url = Column(String, unique=True)
    publisher = Column(String)
    published_at = Column(DateTime(timezone=True))
    language = Column(String, default='en')
    scraped_at = Column(DateTime(timezone=True), server_default=func.now())
    # Category scores vector (dimension 10)
    category_scores = Column(Vector(10))
    metadata_ = Column("metadata", JSONB) # 'metadata' is reserved in SQLAlchemy Base
