import pytest
from httpx import AsyncClient
from unittest.mock import MagicMock, patch
from app.services.nlp_service import NLPService
from app.models.article import Article
from app.database import AsyncSessionLocal
from sqlalchemy.future import select

# Mock NLP Service
@pytest.fixture
def mock_nlp_service():
    with patch("app.services.content_service.NLPService") as MockNLP:
        instance = MockNLP.return_value
        instance.classify_article.return_value = [0.1] * 10
        instance.summarize_articles.return_value = "Mocked Summary"
        yield instance

@pytest.mark.asyncio
async def test_ingest_and_feed(client: AsyncClient, mock_nlp_service, db_session):
    # 1. Ingest Article
    article_data = {
        "title": "Test Article",
        "content": "This is a test article content.",
        "source_url": "http://test.com/1",
        "publisher": "Test Publisher"
    }
    response = await client.post("/ingestion/article", json=article_data)
    assert response.status_code == 200
    
    # Verify it's in DB
    result = await db_session.execute(select(Article).where(Article.source_url == "http://test.com/1"))
    article = result.scalar_one_or_none()
    assert article is not None
    assert article.title == "Test Article"
    
    # 2. Setup User
    await client.post("/auth/signup", json={
        "email": "feed@example.com",
        "password": "password",
        "name": "Feed User"
    })
    login_res = await client.post("/auth/login", data={"username": "feed@example.com", "password": "password"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 3. Get Feed
    response = await client.get("/feed/", headers=headers)
    assert response.status_code == 200
    feed = response.json()
    assert len(feed) > 0
    assert feed[0]["title"] == "Test Article"

@pytest.mark.asyncio
async def test_feedback_and_summary(client: AsyncClient, mock_nlp_service, db_session):
    # Setup User & Article
    await client.post("/auth/signup", json={
        "email": "summary@example.com",
        "password": "password",
        "name": "Summary User"
    })
    login_res = await client.post("/auth/login", data={"username": "summary@example.com", "password": "password"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Ingest article
    await client.post("/ingestion/article", json={
        "title": "Summary Article",
        "content": "Content for summary.",
        "source_url": "http://test.com/summary",
        "publisher": "Test"
    })
    
    # Get Article ID
    result = await db_session.execute(select(Article).where(Article.source_url == "http://test.com/summary"))
    article = result.scalar_one()
    article_id = str(article.id)
    
    # 1. Submit Feedback
    response = await client.post("/feedback/", headers=headers, json={
        "article_id": article_id,
        "is_liked": True
    })
    assert response.status_code == 200
    
    # 2. Get Summary (Mocked)
    # We need to patch NLPService in summary_service as well if it's instantiated there
    with patch("app.services.summary_service.NLPService") as MockNLP:
        instance = MockNLP.return_value
        instance.summarize_articles.return_value = "Mocked Daily Summary"
        
        response = await client.get("/summary/today", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["summary_text"] == "Mocked Daily Summary"
