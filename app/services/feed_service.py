from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc, func
from datetime import date, datetime, timedelta
from app.models.synthesized_article import SynthesizedArticle
from app.models.article import Article
from app.services.user_service import UserService
from typing import List
import logging

logger = logging.getLogger(__name__)

class FeedService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_service = UserService(db)

    async def get_personalized_feed(self, user_id, limit=20, skip=0) -> List[SynthesizedArticle]:
        import random

        # Get user preferences
        prefs, _ = await self.user_service.get_user_preferences(user_id)

        from app.models.interaction import UserInteraction

        # Subquery for articles the user has interacted with
        interacted_subquery = select(UserInteraction.synthesized_article_id).where(
            UserInteraction.user_id == user_id
        )

        if not prefs:
            result = await self.db.execute(
                select(SynthesizedArticle)
                .where(SynthesizedArticle.id.not_in(interacted_subquery))
                .order_by(SynthesizedArticle.generated_at.desc())
                .offset(skip)
                .limit(limit)
            )
            return result.scalars().all()

        # Fetch a larger pool for randomness (buckets are 10, 10, and rest)
        # We need enough items to satisfy the request even if we hit the 'rest' bucket often or run out of 'best'
        pool_limit = 50
        stmt = select(SynthesizedArticle).where(
            SynthesizedArticle.id.not_in(interacted_subquery)
        ).order_by(
            SynthesizedArticle.category_scores.cosine_distance(prefs)
        ).offset(skip).limit(pool_limit)

        result = await self.db.execute(stmt)
        ordered_articles = result.scalars().all()

        # Determine buckets (BUCKET_SIZE = 10 from experiment)
        BUCKET_SIZE = 10
        # RANDOMNESS_PROBS = [0.75, 0.20, 0.05]

        best = list(ordered_articles[:BUCKET_SIZE]) # Top 10
        mid = list(ordered_articles[BUCKET_SIZE:2*BUCKET_SIZE]) # Next 10
        rest = list(ordered_articles[2*BUCKET_SIZE:]) # Rest

        feed = []

        # Select 'limit' articles
        for _ in range(limit):
            if not (best or mid or rest):
                break # No more articles available

            r = random.random()

            # Select Target Bucket based on probabilities
            # Adjusted to 70% Best, 20% Mid, 10% Rest to encourage exploration ("every now and then")
            if r < 0.70:
                target_pool = "best"
            elif r < 0.90:
                target_pool = "mid"
            else:
                target_pool = "rest"

            # Resolve Target to Actual Pool (with fallback)
            pool = None
            if target_pool == "best":
                if best: pool = best
                elif mid: pool = mid
                else: pool = rest
            elif target_pool == "mid":
                if mid: pool = mid
                elif best: pool = best # better fallback than rest?
                else: pool = rest
            else: # rest
                if rest: pool = rest
                elif mid: pool = mid
                else: pool = best

            # Final sanity check if specific fallback path failed (e.g. target mid, mid empty, best empty -> only rest)
            if not pool:
                if best: pool = best
                elif mid: pool = mid
                elif rest: pool = rest

            # Pick one randomly from the selected pool
            if pool:
                article = random.choice(pool)
                feed.append(article)
                pool.remove(article)

        return feed

    async def get_top_articles(self, user_id, limit=15) -> List[Article]:
        """
        Fetches the top 'limit' articles based on cosine similarity to user preferences,
        strictly without randomness. Filters by articles published today.
        """
        logger.debug(f"Getting top articles for user {user_id} (Limit: {limit})")
        # Get user preferences
        prefs, _ = await self.user_service.get_user_preferences(user_id)
        
        # Calculate 24-hour cutoff
        cutoff_time = datetime.now() - timedelta(hours=24)

        if not prefs:
            # Fallback to latest published in last 24h
            result = await self.db.execute(
                select(Article)
                .where(Article.published_at >= cutoff_time)
                .order_by(Article.published_at.desc())
                .limit(limit)
            )
            res = result.scalars().all()
            logger.info(f"User {user_id} has no preferences, returning {len(res)} recent articles.")
            return res

        # Strict similarity sort, filtered by last 24h
        stmt = select(Article).where(
            Article.published_at >= cutoff_time
        ).order_by(
            Article.category_scores.cosine_distance(prefs)
        ).limit(limit)

        result = await self.db.execute(stmt)
        articles = result.scalars().all()
        logger.info(f"Found {len(articles)} relevant articles for user {user_id} published in last 24h.")
        return articles
