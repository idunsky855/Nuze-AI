from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db
from app.services.content_service import ContentService

router = APIRouter(prefix="/ingestion", tags=["ingestion"])

class ArticleIngest(BaseModel):
    title: str
    content: str
    source_url: str
    publisher: str

@router.post("/article")
async def ingest_single_article(
    article_in: ArticleIngest,
    db: AsyncSession = Depends(get_db)
):
    service = ContentService(db)
    article = await service.ingest_article(
        title=article_in.title,
        content=article_in.content,
        source_url=article_in.source_url,
        publisher=article_in.publisher
    )
    if not article:
        return {"message": "Article already exists or failed to ingest"}
    return {"message": "Article ingested", "id": article.id}

