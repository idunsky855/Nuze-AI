from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from uuid import UUID

from app.database import get_db
from app.services.feedback_service import FeedbackService
from app.routers.users import get_current_user_id

router = APIRouter(prefix="/feedback", tags=["feedback"])

class FeedbackCreate(BaseModel):
    article_id: UUID
    is_liked: bool

@router.post("/")
async def submit_feedback(
    feedback: FeedbackCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    service = FeedbackService(db)
    await service.record_feedback(user_id, feedback.article_id, feedback.is_liked)
    return {"message": "Feedback recorded"}
