import asyncio
import os
import sys

# Ensure app is in python path
sys.path.append(os.getcwd())

from app.database import AsyncSessionLocal
from app.services.summary_service import SummaryService
from app.services.user_service import UserService
from sqlalchemy.future import select
from app.models.user import User
from app.models.article import Article
from datetime import datetime
import uuid
from sqlalchemy import func, delete

async def main():
    try:
        async with AsyncSessionLocal() as session:
            print("Getting a user...")
            result = await session.execute(select(User).limit(1))
            user = result.scalar_one_or_none()

            if not user:
                print("No users found in DB. Please create a user first.")
                return

            print(f"Testing summary for user: {user.email} ({user.id})")

            # Ensure tables exist (forcing creation if missing)
            from app.database import engine, Base
            print("Ensuring daily_summaries table exists...")
            async with engine.begin() as conn:
                 await conn.run_sync(Base.metadata.create_all)
            print("DB tables ensured.")

            # Clean up existing summary for today to force generation
            from app.models.summary import DailySummary
            await session.execute(
                delete(DailySummary).where(
                    DailySummary.user_id == user.id,
                    func.date(DailySummary.date) == datetime.today().date()
                )
            )
            await session.commit()
            print("Cleared existing summary for clean test.")

            # Create a dummy article ensures we have something to test with
            # from app.models.article import Article # Already imported at top
            # from datetime import datetime # Already imported at top
            # import uuid # Already imported at top

            # Check if we have articles for today
            result = await session.execute(select(Article).where(func.date(Article.published_at) == datetime.today().date()))
            if not result.scalars().first():
                print("Creating dummy article for testing...")
                dummy_article = Article(
                    id=uuid.uuid4(),
                    title="Test Article for Summary",
                    content="This is a test article content to verify the daily summary generation. It should be picked up by the service.",
                    source_url="http://test.com",
                    published_at=datetime.now(),
                    category_scores=[0.1]*10
                )
                session.add(dummy_article)
                await session.commit()
                print("Dummy article created.")

            summary_service = SummaryService(session)
            print("Checking if summary exists (get_daily_summary)...")
            summary = await summary_service.get_daily_summary(str(user.id))

            if summary:
                 print("Summary already exists:")
                 # Handle JSONB - summary_text might be a dict now
                 text_content = summary.summary_text
                 if isinstance(text_content, dict):
                     import json
                     print(json.dumps(text_content, indent=2)[:200] + "...")
                 else:
                     print(str(text_content)[:100] + "...")
            else:
                 print("No summary found. Generating new one...")

                 # Verify we are getting real Articles
                 print("Verifying FeedService returns real Articles...")
                 from app.services.feed_service import FeedService
                 # from app.models.article import Article # Global import
                 feed_service = FeedService(session)
                 articles = await feed_service.get_top_articles(str(user.id), limit=5)
                 print(f"Fetched {len(articles)} articles.")
                 if articles and isinstance(articles[0], Article):
                     print("CONFIRMED: FeedService returned Article objects.")
                 elif articles:
                     print(f"WARNING: Returned object type: {type(articles[0])}")

                 summary = await summary_service.generate_daily_summary(str(user.id))
                 if summary:
                     print("Summary Generated Successfully!")
                     print("---")
                     text_content = summary.summary_text
                     if isinstance(text_content, dict):
                         import json
                         print(json.dumps(text_content, indent=2)[:400] + "...")
                     else:
                         print(str(text_content)[:200] + "...")
                     print("---")
                 else:
                     print("Failed to generate summary.")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
