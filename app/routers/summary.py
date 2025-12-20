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
            article_ids=summary.article_ids
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
        # Idempotency check
        existing_summary = await service.get_daily_summary(user_id)
        if existing_summary:
             logger.info(f"Summary exists for user {user_id}. Deleting for regeneration (POST request).")
             await db.delete(existing_summary)
             await db.commit()

        summary = await service.generate_daily_summary(user_id)

        if not summary:
             raise HTTPException(status_code=404, detail="Could not generate summary (no relevant articles found?)")

        return SummaryResponse(
            id=summary.id,
            summary_text=summary.summary_text,
            generated_at=summary.summary_generated_at,
            article_ids=summary.article_ids
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in generate_today_summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")
