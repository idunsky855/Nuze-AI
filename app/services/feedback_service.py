from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from sqlalchemy.future import select
from app.models.interaction import UserInteraction
from app.models.synthesized_article import SynthesizedArticle
from app.services.user_service import UserService

class FeedbackService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_service = UserService(db)

    async def record_feedback(self, user_id: str, article_id: str, is_liked: bool):
        # 1. Determine article type
        stmt = select(SynthesizedArticle).where(SynthesizedArticle.id == article_id)
        result = await self.db.execute(stmt)
        synth_article = result.scalar_one_or_none()

        if synth_article:
            # Check if interaction already exists
            stmt = select(UserInteraction).where(
                UserInteraction.user_id == user_id,
                UserInteraction.synthesized_article_id == article_id
            )
            result = await self.db.execute(stmt)
            existing_interaction = result.scalar_one_or_none()

            if existing_interaction:
                # Update existing
                if existing_interaction.is_liked == is_liked:
                    # No change, do nothing
                    return existing_interaction

                # Update status
                existing_interaction.is_liked = is_liked
                self.db.add(existing_interaction)
                await self.db.commit()

                # Logic for prefs update on change?
                # If changed to Like, we learn.
                # If changed to Dislike, we just save state (undong learning is complex).
                if is_liked:
                     await self.update_preferences_from_article(user_id, article_id, synth_article)

                return existing_interaction

            # Create new
            interaction = UserInteraction(
                user_id=user_id,
                synthesized_article_id=article_id,
                is_liked=is_liked
            )
        else:
             # If not found in synthesized, we no longer support standard articles
             raise HTTPException(status_code=404, detail="Article not found")

        self.db.add(interaction)

        # 2. Update preferences if liked (New interaction)
        if is_liked:
            # Pass article object to save redundant query if possible, but keeping signature simple
            await self.update_preferences_from_article(user_id, article_id, synth_article)

        await self.db.commit()
        return interaction

    async def update_preferences_from_article(self, user_id: str, article_id: str, article_obj=None):
        # Get article vector if we don't have object
        if not article_obj:
             # Try synth
             stmt = select(SynthesizedArticle).where(SynthesizedArticle.id == article_id)
             res = await self.db.execute(stmt)
             article_obj = res.scalar_one_or_none()

        if not article_obj or article_obj.category_scores is None:
            return

        article_vec = [float(x) for x in article_obj.category_scores]

        # Get user vector
        user_vec = await self.user_service.get_user_preferences(user_id)

        if not user_vec:
            # Initialize with article vector
            new_vec = article_vec
        else:
            # Simple update: move 10% towards article
            new_vec = []
            for u, a in zip(user_vec, article_vec):
                new_vec.append(u * 0.9 + a * 0.1)

        await self.user_service.update_user_preferences(user_id, new_vec)
