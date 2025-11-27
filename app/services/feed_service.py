from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc
from app.models.article import Article
from app.services.user_service import UserService
from typing import List

class FeedService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_service = UserService(db)

    async def get_personalized_feed(self, user_id, limit=20) -> List[Article]:
        # Get user preferences
        prefs = await self.user_service.get_user_preferences(user_id)
        
        if not prefs:
            # Fallback to recent articles if no preferences
            result = await self.db.execute(
                select(Article).order_by(Article.published_at.desc()).limit(limit)
            )
            return result.scalars().all()
        
        # Vector similarity search
        # Using l2_distance or cosine_distance. pgvector supports <-> (L2), <=> (Cosine), <#> (Inner Product)
        # SQLAlchemy pgvector support: Article.category_scores.l2_distance(prefs)
        
        # Note: We need to ensure the vector extension is installed and types are correct.
        # Assuming prefs is a list of floats.
        
        stmt = select(Article).order_by(
            Article.category_scores.cosine_distance(prefs)
        ).limit(limit)
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
