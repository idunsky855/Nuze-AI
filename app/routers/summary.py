from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.database import get_db
from app.services.summary_service import SummaryService
from app.routers.users import get_current_user_id
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/summary", tags=["summary"])

from typing import List, Optional, Any
# ...
class SummaryResponse(BaseModel):
    id: UUID
    summary_text: Any # JSONB returns dict/list/etc
    generated_at: datetime
    article_ids: List[UUID]
    status: Optional[str] = None

@router.get("/today", response_model=SummaryResponse)
async def get_today_summary(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    logger.info(f"get_today_summary called for user {user_id}")
    try:
        service = SummaryService(db)
        summary = await service.get_daily_summary(user_id)

        if not summary:
            logger.info(f"No summary found for user {user_id} (returning 404)")
            raise HTTPException(status_code=404, detail="No daily summary found.")

        return SummaryResponse(
            id=summary.id,
            summary_text=summary.summary_text,
            generated_at=summary.summary_generated_at,
            article_ids=summary.article_ids,
            status=summary.status
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_today_summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.post("/today", response_model=SummaryResponse)
async def generate_today_summary(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    logger.info(f"generate_today_summary called for user {user_id}")
    try:
        service = SummaryService(db)
        # Check if there's an existing summary
        existing_summary = await service.get_daily_summary(user_id)
        
        if existing_summary:
            if existing_summary.status == "pending":
                # Check if it's stale (older than 10 minutes)
                from datetime import datetime, timedelta
                stale_threshold = datetime.utcnow() - timedelta(minutes=10)
                if existing_summary.summary_generated_at.replace(tzinfo=None) < stale_threshold:
                    # Stale pending - treat as failed, delete and allow retry
                    logger.warning(f"Stale pending summary for user {user_id} (>10 min). Deleting.")
                    await db.delete(existing_summary)
                    await db.commit()
                else:
                    # Still generating - return 202 Accepted
                    raise HTTPException(status_code=202, detail="Summary generation already in progress")
            elif existing_summary.status == "completed":
                # Already done - just return it
                return SummaryResponse(
                    id=existing_summary.id,
                    summary_text=existing_summary.summary_text,
                    generated_at=existing_summary.summary_generated_at,
                    article_ids=existing_summary.article_ids,
                    status=existing_summary.status
                )
            else:
                # Failed - delete and retry
                logger.info(f"Previous summary failed for user {user_id}. Deleting for retry.")
                await db.delete(existing_summary)
                await db.commit()

        # Create a pending placeholder before starting generation
        from app.models.summary import DailySummary
        from datetime import date
        pending_summary = DailySummary(
            user_id=user_id,
            article_ids=[],
            summary_text={"status": "generating"},
            date=date.today(),
            status="pending"
        )
        db.add(pending_summary)
        await db.commit()
        await db.refresh(pending_summary)

        # Generate the actual summary
        summary = await service.generate_daily_summary(user_id)

        if not summary:
            # Generation failed - delete pending record
            await db.delete(pending_summary)
            await db.commit()
            raise HTTPException(status_code=500, detail="Could not generate summary. Please try again.")

        # Delete the pending placeholder (the real one was created by the service)
        await db.delete(pending_summary)
        await db.commit()

        return SummaryResponse(
            id=summary.id,
            summary_text=summary.summary_text,
            generated_at=summary.summary_generated_at,
            article_ids=summary.article_ids,
            status=summary.status
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in generate_today_summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")
