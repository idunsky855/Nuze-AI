from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from datetime import date
from typing import Optional

from app.models.summary import DailySummary
from app.services.feed_service import FeedService
from app.services.nlp_service import NLPService


import logging
logger = logging.getLogger(__name__)

# TODO: remove if not used or implement
class SummaryService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.feed_service = FeedService(db)
        self.nlp_service = NLPService()

    async def get_daily_summary(self, user_id: str) -> Optional[DailySummary]:
        logger.info(f"Checking daily summary for user {user_id}")
        # Check if summary exists for today
        today = date.today()
        # Note: summary_generated_at is timestamp, we need to check date part.
        # SQLite/Postgres specific date truncation might be needed.
        # For simplicity, let's just check if we have one generated > today midnight.

        # Postgres: func.date(DailySummary.summary_generated_at) == today
        # We now have a 'date' column
        stmt = select(DailySummary).where(
            DailySummary.user_id == user_id,
            func.date(DailySummary.date) == today
        ).limit(1)
        result = await self.db.execute(stmt)
        summary = result.scalars().first()

        if summary:
            logger.info(f"Found existing summary {summary.id} for user {user_id}")
            return summary

        logger.info(f"No existing summary found for user {user_id}")
        return None

    async def generate_daily_summary(self, user_id: str) -> DailySummary:
        # 1. Get top relevant articles (strict 15)
        articles = await self.feed_service.get_top_articles(user_id, limit=15)

        logger.info(f"Fetched {len(articles)} articles for summary generation (User: {user_id})")

        if not articles:
            logger.warning(f"No articles found for user {user_id}, cannot generate summary.")
            return None

        article_texts = [f"Title: {a.title}\nContent: {a.content}" for a in articles]
        article_ids = [a.id for a in articles]

        # 2. Summarize
        from app.services.user_service import UserService
        user_service = UserService(self.db)
        # Fetch actual preferences to pass to the model
        _, preferences_meta = await user_service.get_user_preferences(user_id)

        summary_json = await self.nlp_service.summarize_articles(article_texts, preferences_meta)

        # Parse strict JSON string to dict for JSONB column
        import json
        try:
            summary_data = json.loads(summary_json)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse summary JSON: {summary_json}")
            summary_data = {"error": "Failed to parse summary", "raw": summary_json}

        # Inject top article image (find first one with an image)
        top_image_url = None
        for article in articles:
            if article.image_url:
                top_image_url = article.image_url
                break

        if top_image_url:
            if isinstance(summary_data, dict):
                summary_data["top_image_url"] = top_image_url

        # 3. Store
        summary = DailySummary(
            user_id=user_id,
            article_ids=article_ids,
            summary_text=summary_data,
            date=date.today()
        )
        self.db.add(summary)
        await self.db.commit()
        await self.db.refresh(summary)

        logger.info(f"Successfully generated summary {summary.id} for user {user_id}")

        return summary
