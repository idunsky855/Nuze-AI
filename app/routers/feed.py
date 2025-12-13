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
    skip: int = 0,
    limit: int = 20,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    from app.models.interaction import UserInteraction
    from sqlalchemy.future import select

    feed_service = FeedService(db)
    articles = await feed_service.get_personalized_feed(user_id, limit=limit, skip=skip)

    # Fetch user interactions for these articles
    article_ids = [article.id for article in articles]
    interactions_result = await db.execute(
        select(UserInteraction).where(
            UserInteraction.user_id == user_id,
            UserInteraction.synthesized_article_id.in_(article_ids)
        )
    )
    interactions = {i.synthesized_article_id: i.is_liked for i in interactions_result.scalars().all()}

    # Populate is_liked field
    response = []
    for article in articles:
        article_dict = ArticleResponse.model_validate(article).model_dump()
        article_dict['is_liked'] = interactions.get(article.id)
        response.append(ArticleResponse(**article_dict))

    return response
