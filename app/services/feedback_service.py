from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.interaction import UserInteraction
from app.models.article import Article
from app.services.user_service import UserService
from typing import List

class FeedbackService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_service = UserService(db)

    async def record_feedback(self, user_id: str, article_id: str, is_liked: bool):
        # 1. Record interaction
        interaction = UserInteraction(
            user_id=user_id,
            article_id=article_id,
            is_liked=is_liked
        )
        self.db.add(interaction)
        
        # 2. Update preferences if liked
        if is_liked:
            await self.update_preferences_from_article(user_id, article_id)
        
        await self.db.commit()
        return interaction

    async def update_preferences_from_article(self, user_id: str, article_id: str):
        # Get article vector
        result = await self.db.execute(select(Article).where(Article.id == article_id))
        article = result.scalar_one_or_none()
        
        if not article or not article.category_scores:
            return
            
        article_vec = [float(x) for x in article.category_scores]
        
        # Get user vector
        user_vec = await self.user_service.get_user_preferences(user_id)
        
        if not user_vec:
            # Initialize with article vector
            new_vec = article_vec
        else:
            # Simple update: move 10% towards article
            # new = old * 0.9 + article * 0.1
            new_vec = []
            for u, a in zip(user_vec, article_vec):
                new_vec.append(u * 0.9 + a * 0.1)
                
        await self.user_service.update_user_preferences(user_id, new_vec)
