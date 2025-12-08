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
    cmd = [sys.executable, script_path]

    logger.info(f"Executing command: {' '.join(cmd)}")
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if stdout:
            logger.info(f"Script output: {stdout.decode().strip()}")
        if stderr:
             logger.error(f"Script error: {stderr.decode().strip()}")

        if process.returncode != 0:
            logger.error(f"Job failed with return code {process.returncode}")
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
    cmd = [sys.executable, script_path]

    logger.info(f"Executing command: {' '.join(cmd)}")
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if stdout:
            logger.info(f"Script output: {stdout.decode().strip()}")
        if stderr:
             logger.error(f"Script error: {stderr.decode().strip()}")

        if process.returncode != 0:
             logger.error(f"Job failed with return code {process.returncode}")
    except Exception as e:
        logger.error(f"Failed to execute daily ingest script: {e}")

    logger.info("Daily content ingestion job completed.")

    # Trigger clustering immediately after ingestion
    await run_daily_cluster()

async def start_scheduler():
    # Schedule jobs
    # Schedule jobs
    # Run daily ingest at 23:00
    trigger = CronTrigger(hour=23, minute=0)
    scheduler.add_job(run_daily_ingest, trigger)

    scheduler.start()
    logger.info("Scheduler started.")
