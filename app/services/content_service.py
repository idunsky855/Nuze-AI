from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.article import Article
from app.services.nlp_service import NLPService
from datetime import datetime
import uuid

class ContentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.nlp_service = NLPService()

    async def ingest_article(self, title: str, content: str, source_url: str, publisher: str):
        # Check if exists
        result = await self.db.execute(select(Article).where(Article.source_url == source_url))
        if result.scalar_one_or_none():
            return None # Already exists
        
        # Classify
        category_scores = self.nlp_service.classify_article(content)
        
        article = Article(
            title=title,
            content=content,
            source_url=source_url,
            publisher=publisher,
            published_at=datetime.utcnow(),
            category_scores=category_scores
        )
        self.db.add(article)
        await self.db.commit()
        await self.db.refresh(article)
        return article

    async def get_recent_articles(self, limit=10):
        result = await self.db.execute(select(Article).order_by(Article.published_at.desc()).limit(limit))
        return result.scalars().all()
