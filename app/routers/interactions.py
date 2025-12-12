from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Literal
from uuid import UUID

from app.database import get_db
from app.services.feedback_service import FeedbackService
from app.routers.users import get_current_user_id

router = APIRouter(prefix="/interactions", tags=["interactions"])

class InteractionRequest(BaseModel):
    articleId: UUID
    type: Literal['like', 'dislike', 'click']

@router.post("")
async def record_interaction(
    interaction: InteractionRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    service = FeedbackService(db)

    is_liked = None
    if interaction.type == 'like':
        is_liked = True
    elif interaction.type == 'dislike':
        is_liked = False

    # We call record_feedback from the existing service which handles logic and vector updates
    await service.record_feedback(user_id, interaction.articleId, is_liked)

    return {"status": "success", "message": f"Recorded {interaction.type}"}
