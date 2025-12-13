from sqlalchemy import Column, String, DateTime, func, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import relationship
from app.database import Base
import uuid

class SynthesizedArticle(Base):
    __tablename__ = "synthesized_articles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String)
    content = Column(Text)
    image_url = Column(String)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    generation_prompt = Column(Text)
    notes = Column(Text)
    analysis = Column(JSONB) # Storing the full analysis JSON here
    category_scores = Column(Vector(10))
    metadata_scores = Column(JSONB)

    @property
    def published_at(self):
        return self.generated_at

    @property
    def publisher(self):
        return "Nuze AI"

    # Relationship to sources
    sources = relationship("SynthesizedSource", back_populates="synthesized_article")

class SynthesizedSource(Base):
    __tablename__ = "synthesized_sources"

    synthesized_id = Column(UUID(as_uuid=True), ForeignKey("synthesized_articles.id"), primary_key=True)
    article_id = Column(UUID(as_uuid=True), ForeignKey("articles.id"), primary_key=True)

    synthesized_article = relationship("SynthesizedArticle", back_populates="sources")
