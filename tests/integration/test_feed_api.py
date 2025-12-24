"""Integration tests for Feed API endpoints."""
import pytest
from httpx import AsyncClient
from uuid import uuid4
from unittest.mock import patch


class TestFeedEndpoint:
    """Tests for GET /feed/"""

    @pytest.mark.asyncio
    async def test_get_feed_authenticated(self, client: AsyncClient, db_session):
        """GET /feed/ returns articles for authenticated user."""
        from app.models.synthesized_article import SynthesizedArticle

        # Create article
        article = SynthesizedArticle(
            id=uuid4(),
            title="Test Article",
            content="Content",
            category_scores=[0.5] * 10
        )
        db_session.add(article)
        await db_session.commit()

        # Create and login user
        await client.post("/auth/signup", json={
            "email": "feedtest@example.com",
            "password": "password123",
            "name": "Feed Test"
        })
        login_res = await client.post("/auth/login", data={
            "username": "feedtest@example.com",
            "password": "password123"
        })
        token = login_res.json()["access_token"]

        # Get feed
        response = await client.get("/feed/", headers={
            "Authorization": f"Bearer {token}"
        })

        assert response.status_code == 200
        feed = response.json()
        assert isinstance(feed, list)
        assert len(feed) >= 1

    @pytest.mark.asyncio
    async def test_get_feed_unauthenticated(self, client: AsyncClient):
        """Returns 401 without token."""
        response = await client.get("/feed/")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_feed_excludes_read(self, client: AsyncClient, db_session):
        """Excludes interacted articles."""
        from app.models.synthesized_article import SynthesizedArticle
        from app.models.user import User
        from app.models.interaction import UserInteraction
        from sqlalchemy.future import select

        # Create user first
        await client.post("/auth/signup", json={
            "email": "excludetest@example.com",
            "password": "password123",
            "name": "Exclude Test"
        })
        login_res = await client.post("/auth/login", data={
            "username": "excludetest@example.com",
            "password": "password123"
        })
        token = login_res.json()["access_token"]

        # Get user ID
        result = await db_session.execute(
            select(User).where(User.email == "excludetest@example.com")
        )
        user = result.scalar_one()

        # Create articles
        seen_id = uuid4()
        seen_article = SynthesizedArticle(
            id=seen_id,
            title="Seen Article",
            content="Content",
            category_scores=[0.5] * 10
        )
        db_session.add(seen_article)

        unseen_article = SynthesizedArticle(
            id=uuid4(),
            title="Unseen Article",
            content="Content",
            category_scores=[0.5] * 10
        )
        db_session.add(unseen_article)
        # Commit articles first to satisfy FK constraints
        await db_session.commit()

        # Mark one as read
        interaction = UserInteraction(
            user_id=user.id,
            synthesized_article_id=seen_id,
            is_liked=True
        )
        db_session.add(interaction)
        await db_session.commit()

        # Get feed
        response = await client.get("/feed/", headers={
            "Authorization": f"Bearer {token}"
        })

        assert response.status_code == 200
        feed = response.json()

        # Should not contain seen article
        seen_titles = [a["title"] for a in feed]
        assert "Seen Article" not in seen_titles
        assert "Unseen Article" in seen_titles

    @pytest.mark.asyncio
    async def test_get_feed_empty(self, client: AsyncClient):
        """Returns empty list when no articles."""
        # Create and login user
        await client.post("/auth/signup", json={
            "email": "emptytest@example.com",
            "password": "password123",
            "name": "Empty Test"
        })
        login_res = await client.post("/auth/login", data={
            "username": "emptytest@example.com",
            "password": "password123"
        })
        token = login_res.json()["access_token"]

        # Get feed (no articles in db for this test)
        response = await client.get("/feed/", headers={
            "Authorization": f"Bearer {token}"
        })

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_get_feed_pagination(self, client: AsyncClient, db_session):
        """Tests skip/limit parameters."""
        from app.models.synthesized_article import SynthesizedArticle

        # Create multiple articles
        for i in range(10):
            article = SynthesizedArticle(
                id=uuid4(),
                title=f"Article {i}",
                content="Content",
                category_scores=[0.5] * 10
            )
            db_session.add(article)
        await db_session.commit()

        # Create and login user
        await client.post("/auth/signup", json={
            "email": "paginationtest@example.com",
            "password": "password123",
            "name": "Pagination Test"
        })
        login_res = await client.post("/auth/login", data={
            "username": "paginationtest@example.com",
            "password": "password123"
        })
        token = login_res.json()["access_token"]

        # Get feed with limit
        response = await client.get("/feed/?limit=5", headers={
            "Authorization": f"Bearer {token}"
        })

        assert response.status_code == 200
        assert len(response.json()) <= 5
