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

    # Manually fetch sources for these articles to guarantee data availability
    # (Bypassing potential ORM lazy loading or property mapping issues)
    from app.models.synthesized_article import SynthesizedSource, SynthesizedArticle
    from app.models.article import Article as SourceArticle

    sources_query = select(SynthesizedSource, SourceArticle).join(
        SourceArticle, SynthesizedSource.article_id == SourceArticle.id
    ).where(
        SynthesizedSource.synthesized_id.in_(article_ids)
    )

    sources_result = await db.execute(sources_query)

    # Map sources by synthesized_article_id
    sources_map = {}
    rows = sources_result.all()

    # Debug: Print available keys in map
    for synth_source, source_article in rows:
        # Use string representation of UUID for reliable lookup
        sid = str(synth_source.synthesized_id)
        if sid not in sources_map:
            sources_map[sid] = []

        sources_map[sid].append({
            "title": source_article.title,
            "url": source_article.source_url,
            "publisher": source_article.publisher
        })

    # Populate is_liked field and ensure sources are passed
    response = []
    for article in articles:
        article_dict = ArticleResponse.model_validate(article).model_dump()
        article_dict['is_liked'] = interactions.get(article.id)

        # Override sources with explicitly fetched data
        aid = str(article.id)

        if aid in sources_map:
             article_dict['sources'] = sources_map[aid]
        else:
             pass # No sources map entry for article

        # Fallback logic...
        if not article_dict.get('sources'):
             try:
                 # Check property too just in case
                 if article.sources_detail:
                      article_dict['sources'] = article.sources_detail
             except:
                 pass

        response.append(ArticleResponse(**article_dict))

    return response
