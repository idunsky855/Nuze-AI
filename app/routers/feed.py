from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Any

from app.database import get_db
from app.services.feed_service import FeedService
from app.routers.users import get_current_user_id

router = APIRouter(prefix="/feed", tags=["feed"])

from app.schemas.article import ArticleResponse

@router.get("/", response_model=List[ArticleResponse]) # Use a proper schema for Article response
async def get_feed(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    feed_service = FeedService(db)
    articles = await feed_service.get_personalized_feed(user_id)
    return articles
