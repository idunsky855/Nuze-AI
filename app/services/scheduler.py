import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import AsyncSessionLocal
from app.models.user import User
from app.services.summary_service import SummaryService
from app.services.content_service import ContentService

logger = logging.getLogger("nuze-backend")

async def run_daily_jobs():
    logger.info("Starting daily jobs...")
    async with AsyncSessionLocal() as db:
        # 1. Trigger Ingestion (Mock)
        # In a real app, we would call a scraper here
        logger.info("Triggering content ingestion...")
        # content_service = ContentService(db)
        # await content_service.ingest_from_sources() 
        
        # 2. Generate Summaries for all users
        logger.info("Generating daily summaries...")
        result = await db.execute(select(User.id))
        user_ids = result.scalars().all()
        
        summary_service = SummaryService(db)
        for user_id in user_ids:
            try:
                await summary_service.generate_daily_summary(str(user_id))
                logger.info(f"Generated summary for user {user_id}")
            except Exception as e:
                logger.error(f"Failed to generate summary for user {user_id}: {e}")
                
    logger.info("Daily jobs completed.")

async def start_scheduler():
    while True:
        # Run every 24 hours (86400 seconds)
        # For demo, let's say every 1 hour or just run once on startup and then wait
        # We'll wait 60 seconds after startup then run, then wait 24h
        await asyncio.sleep(60) 
        await run_daily_jobs()
        await asyncio.sleep(86400)
