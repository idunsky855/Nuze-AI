from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.database import get_db
from app.services.summary_service import SummaryService
from app.routers.users import get_current_user_id

router = APIRouter(prefix="/summary", tags=["summary"])

class SummaryResponse(BaseModel):
    id: UUID
    summary_text: str
    generated_at: datetime
    article_ids: List[UUID]

@router.get("/today", response_model=SummaryResponse)
async def get_today_summary(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    service = SummaryService(db)
    summary = await service.get_daily_summary(user_id)
    
    if not summary:
        raise HTTPException(status_code=404, detail="Could not generate summary (no articles found?)")
        
    return SummaryResponse(
        id=summary.id,
        summary_text=summary.summary_text,
        generated_at=summary.summary_generated_at,
        article_ids=summary.article_ids
    )
