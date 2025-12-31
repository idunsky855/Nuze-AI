from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import logging
from sqlalchemy.future import select
from app.database import AsyncSessionLocal
from app.models.user import User
from app.services.summary_service import SummaryService

logger = logging.getLogger("nuze-backend")

scheduler = AsyncIOScheduler()

async def run_daily_cluster():
    """JOB: Daily Cluster/Summary Generation"""
    logger.info("Starting daily cluster/summary generation job...")

    import sys
    import os
    import asyncio

    script_path = os.path.join("scripts", "daily_cluster.py")
    cmd = ["uv", "run", script_path]

    logger.info(f"Executing command: {' '.join(cmd)}")
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        async def log_stream(stream, level):
            while True:
                line = await stream.readline()
                if line:
                    logger.log(level, line.decode().strip())
                else:
                    break

        await asyncio.gather(
            log_stream(process.stdout, logging.INFO),
            log_stream(process.stderr, logging.ERROR)
        )

        returncode = await process.wait()

        if returncode != 0:
            logger.error(f"Job failed with return code {returncode}")

    except Exception as e:
        logger.error(f"Failed to execute daily cluster script: {e}")

    logger.info("Daily cluster/summary generation job completed.")

async def run_daily_ingest():
    """JOB: Daily Content Ingestion"""
    logger.info("Starting daily content ingestion job...")

    import sys
    import os
    import asyncio

    script_path = os.path.join("scripts", "daily_ingest.py")
    cmd = ["uv", "run", script_path]

    logger.info(f"Executing command: {' '.join(cmd)}")
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        async def log_stream(stream, level):
            while True:
                line = await stream.readline()
                if line:
                    logger.log(level, line.decode().strip())
                else:
                    break

        await asyncio.gather(
            log_stream(process.stdout, logging.INFO),
            log_stream(process.stderr, logging.ERROR)
        )

        returncode = await process.wait()

        if returncode != 0:
             logger.error(f"Job failed with return code {returncode}")

    except Exception as e:
        logger.error(f"Failed to execute daily ingest script: {e}")

    logger.info("Daily content ingestion job completed.")

    # Trigger clustering immediately after ingestion
    await run_daily_cluster()

async def start_scheduler():
    # Schedule jobs
    # Run daily ingest twice a day at 06:00 and 18:00 UTC
    morning_trigger = CronTrigger(hour=6, minute=0)
    evening_trigger = CronTrigger(hour=18, minute=0)
    
    scheduler.add_job(run_daily_ingest, morning_trigger, id="daily_ingest_morning")
    scheduler.add_job(run_daily_ingest, evening_trigger, id="daily_ingest_evening")

    scheduler.start()
    logger.info("Scheduler started. Jobs scheduled at 06:00 and 18:00 UTC.")
