import asyncio
import sys
import os
import logging
from sqlalchemy.future import select

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import AsyncSessionLocal
from app.models.synthesized_article import SynthesizedArticle

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backfill_vectors")

async def backfill_category_scores():
    logger.info("Starting backfill of category_scores...")
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(SynthesizedArticle).where(SynthesizedArticle.category_scores.is_(None)))
        articles = result.scalars().all()

        logger.info(f"Found {len(articles)} articles to backfill.")

        count = 0
        category_keys = [
            "Politics & Law", "Economy & Business", "Science & Technology",
            "Health & Wellness", "Education & Society", "Culture & Entertainment",
            "Religion & Belief", "Sports", "World & International Affairs",
            "Opinion & General News"
        ]

        for article in articles:
            if article.analysis:
                try:
                    scores = []
                    valid = True
                    for key in category_keys:
                        val = article.analysis.get(key)
                        if val is None:
                            logger.warning(f"Article {article.id} missing key {key} in analysis.")
                            valid = False
                            break
                        scores.append(float(val))

                    if valid:
                        article.category_scores = scores
                        db.add(article)
                        count += 1
                except Exception as e:
                    logger.error(f"Error processing article {article.id}: {e}")

        await db.commit()
        logger.info(f"Successfully backfilled {count} articles.")

if __name__ == "__main__":
    asyncio.run(backfill_category_scores())
