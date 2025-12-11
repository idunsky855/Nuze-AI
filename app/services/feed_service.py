from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc
from app.models.synthesized_article import SynthesizedArticle
from app.services.user_service import UserService
from typing import List

class FeedService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_service = UserService(db)

    async def get_personalized_feed(self, user_id, limit=20) -> List[SynthesizedArticle]:
        # Get user preferences
        prefs = await self.user_service.get_user_preferences(user_id)

        if not prefs:
            # Fallback to recent articles if no preferences
            result = await self.db.execute(
                select(SynthesizedArticle).order_by(SynthesizedArticle.generated_at.desc()).limit(limit)
            )
            return result.scalars().all()

        # Vector similarity search
        stmt = select(SynthesizedArticle).order_by(
            SynthesizedArticle.category_scores.cosine_distance(prefs)
        ).limit(limit)

        result = await self.db.execute(stmt)
        return result.scalars().all()
