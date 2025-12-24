"""Integration tests for Summary API endpoints."""
import pytest
from httpx import AsyncClient
from uuid import uuid4
from datetime import datetime, date
from unittest.mock import patch, MagicMock, AsyncMock


class TestSummaryEndpoints:
    """Tests for /summary/ endpoints"""

    @pytest.mark.asyncio
    async def test_get_summary_existing(self, client: AsyncClient, db_session):
        """GET /summary/today returns cached summary."""
        from app.models.user import User
        from app.models.summary import DailySummary
        from sqlalchemy.future import select

        # Create user
        await client.post("/auth/signup", json={
            "email": "summaryget@example.com",
            "password": "password123",
            "name": "Summary Get"
        })

        result = await db_session.execute(
            select(User).where(User.email == "summaryget@example.com")
        )
        user = result.scalar_one()

        # Create existing summary
        summary = DailySummary(
            id=uuid4(),
            user_id=user.id,
            article_ids=[],
            summary_text={"greeting": "Hello!", "summary": "Test summary", "key_points": ["Point 1"]},
            date=date.today()
        )
        db_session.add(summary)
        await db_session.commit()

        login_res = await client.post("/auth/login", data={
            "username": "summaryget@example.com",
            "password": "password123"
        })
        token = login_res.json()["access_token"]

        response = await client.get("/summary/today",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "summary_text" in data

    @pytest.mark.asyncio
    async def test_summary_unauthenticated(self, client: AsyncClient):
        """Returns 401 without token."""
        response = await client.get("/summary/today")

        assert response.status_code == 401

    @pytest.mark.skip(reason="Requires shared DB session between test and API - complex setup")
    @pytest.mark.asyncio
    @patch('app.services.summary_service.NLPService')
    async def test_generate_summary(self, mock_nlp_class, client: AsyncClient, db_session):
        """POST /summary/generate creates new summary."""
        from app.models.article import Article
        from app.models.user import User
        from sqlalchemy.future import select

        # Mock NLP
        mock_nlp = MagicMock()
        mock_nlp.summarize_articles = AsyncMock(return_value='{"greeting": "Hello!", "summary": "Generated summary", "key_points": ["Point"]}')
        mock_nlp_class.return_value = mock_nlp

        # Create article
        article = Article(
            id=uuid4(),
            title="News Article",
            content="Article content for summary",
            source_url="http://example.com/news",
            publisher="Test",
            published_at=datetime.now(),
            category_scores=[0.5] * 10
        )
        db_session.add(article)

        # Create user
        await client.post("/auth/signup", json={
            "email": "summarygenerate@example.com",
            "password": "password123",
            "name": "Summary Generate"
        })

        result = await db_session.execute(
            select(User).where(User.email == "summarygenerate@example.com")
        )
        user = result.scalar_one()
        user.preferences = [0.5] * 10
        user.preferences_metadata = {"Length": 0.5}
        await db_session.commit()

        login_res = await client.post("/auth/login", data={
            "username": "summarygenerate@example.com",
            "password": "password123"
        })
        token = login_res.json()["access_token"]

        response = await client.post("/summary/generate",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Should return 200 or create summary
        assert response.status_code in [200, 201]

    @pytest.mark.asyncio
    async def test_summary_no_articles(self, client: AsyncClient, db_session):
        """Handles empty article list gracefully."""
        # Create user (no articles in DB)
        await client.post("/auth/signup", json={
            "email": "summaryempty@example.com",
            "password": "password123",
            "name": "Summary Empty"
        })

        login_res = await client.post("/auth/login", data={
            "username": "summaryempty@example.com",
            "password": "password123"
        })
        token = login_res.json()["access_token"]

        response = await client.get("/summary/today",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Should handle gracefully (either 200 with null or 404)
        assert response.status_code in [200, 404]
