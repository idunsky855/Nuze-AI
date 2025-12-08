from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from datetime import date
from typing import Optional

from app.models.summary import DailySummary
from app.services.feed_service import FeedService
from app.services.nlp_service import NLPService


# TODO: remove if not used or implement
class SummaryService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.feed_service = FeedService(db)
        self.nlp_service = NLPService()

    async def get_daily_summary(self, user_id: str) -> Optional[DailySummary]:
        # Check if summary exists for today
        today = date.today()
        # Note: summary_generated_at is timestamp, we need to check date part.
        # SQLite/Postgres specific date truncation might be needed.
        # For simplicity, let's just check if we have one generated > today midnight.

        # Postgres: func.date(DailySummary.summary_generated_at) == today
        stmt = select(DailySummary).where(
            DailySummary.user_id == user_id,
            func.date(DailySummary.summary_generated_at) == today
        )
        result = await self.db.execute(stmt)
        summary = result.scalar_one_or_none()

        if summary:
            return summary

        # Generate new summary
        return await self.generate_daily_summary(user_id)

    async def generate_daily_summary(self, user_id: str) -> DailySummary:
        # 1. Get top relevant articles (e.g. top 5)
        articles = await self.feed_service.get_personalized_feed(user_id, limit=5)

        if not articles:
            return None

        article_texts = [f"Title: {a.title}\nContent: {a.content}" for a in articles]
        article_ids = [a.id for a in articles]

        # 2. Summarize
        summary_text = self.nlp_service.summarize_articles(article_texts)

        # 3. Store
        summary = DailySummary(
            user_id=user_id,
            article_ids=article_ids,
            summary_text=summary_text
        )
        self.db.add(summary)
        await self.db.commit()
        await self.db.refresh(summary)

        return summary
