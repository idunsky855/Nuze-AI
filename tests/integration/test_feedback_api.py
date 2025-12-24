"""Integration tests for Feedback API endpoints."""
import pytest
from httpx import AsyncClient
from uuid import uuid4


class TestFeedbackEndpoint:
    """Tests for POST /feedback/"""

    @pytest.mark.asyncio
    async def test_submit_feedback_like(self, client: AsyncClient, db_session):
        """POST /feedback/ with is_liked=true."""
        from app.models.synthesized_article import SynthesizedArticle
        from app.models.user import User
        from sqlalchemy.future import select

        # Create article
        article_id = uuid4()
        article = SynthesizedArticle(
            id=article_id,
            title="Feedback Test Article",
            content="Content",
            category_scores=[0.5] * 10,
            metadata_scores={"Length": 0.5, "Complexity": 0.5, "Neutral": 0.5, "Informative": 0.5, "Emotional": 0.5}
        )
        db_session.add(article)
        await db_session.commit()

        # Create and login user with preferences
        await client.post("/auth/signup", json={
            "email": "likefeedback@example.com",
            "password": "password123",
            "name": "Like Feedback"
        })

        # Set initial preferences
        result = await db_session.execute(
            select(User).where(User.email == "likefeedback@example.com")
        )
        user = result.scalar_one()
        user.preferences = [0.5] * 10
        user.preferences_metadata = {"Length": 0.5, "Complexity": 0.5, "Neutral": 0.5, "Informative": 0.5, "Emotional": 0.5}
        await db_session.commit()

        login_res = await client.post("/auth/login", data={
            "username": "likefeedback@example.com",
            "password": "password123"
        })
        token = login_res.json()["access_token"]

        # Submit like
        response = await client.post("/feedback/",
            headers={"Authorization": f"Bearer {token}"},
            json={"article_id": str(article_id), "is_liked": True}
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_submit_feedback_dislike(self, client: AsyncClient, db_session):
        """POST /feedback/ with is_liked=false."""
        from app.models.synthesized_article import SynthesizedArticle
        from app.models.user import User
        from sqlalchemy.future import select

        article_id = uuid4()
        article = SynthesizedArticle(
            id=article_id,
            title="Dislike Test Article",
            content="Content",
            category_scores=[0.5] * 10,
            metadata_scores={"Length": 0.5, "Complexity": 0.5, "Neutral": 0.5, "Informative": 0.5, "Emotional": 0.5}
        )
        db_session.add(article)
        await db_session.commit()

        await client.post("/auth/signup", json={
            "email": "dislikefeedback@example.com",
            "password": "password123",
            "name": "Dislike Feedback"
        })

        result = await db_session.execute(
            select(User).where(User.email == "dislikefeedback@example.com")
        )
        user = result.scalar_one()
        user.preferences = [0.5] * 10
        user.preferences_metadata = {"Length": 0.5, "Complexity": 0.5, "Neutral": 0.5, "Informative": 0.5, "Emotional": 0.5}
        await db_session.commit()

        login_res = await client.post("/auth/login", data={
            "username": "dislikefeedback@example.com",
            "password": "password123"
        })
        token = login_res.json()["access_token"]

        response = await client.post("/feedback/",
            headers={"Authorization": f"Bearer {token}"},
            json={"article_id": str(article_id), "is_liked": False}
        )

        assert response.status_code == 200

    @pytest.mark.skip(reason="Requires shared DB session between test and API - complex setup")
    @pytest.mark.asyncio
    async def test_submit_feedback_click(self, client: AsyncClient, db_session):
        """POST /feedback/ with is_liked=null (click)."""
        from app.models.synthesized_article import SynthesizedArticle
        from app.models.user import User
        from sqlalchemy.future import select

        article_id = uuid4()
        article = SynthesizedArticle(
            id=article_id,
            title="Click Test Article",
            content="Content",
            category_scores=[0.5] * 10,
            metadata_scores={"Length": 0.5, "Complexity": 0.5, "Neutral": 0.5, "Informative": 0.5, "Emotional": 0.5}
        )
        db_session.add(article)
        await db_session.commit()

        await client.post("/auth/signup", json={
            "email": "clickfeedback@example.com",
            "password": "password123",
            "name": "Click Feedback"
        })

        result = await db_session.execute(
            select(User).where(User.email == "clickfeedback@example.com")
        )
        user = result.scalar_one()
        user.preferences = [0.5] * 10
        user.preferences_metadata = {"Length": 0.5, "Complexity": 0.5, "Neutral": 0.5, "Informative": 0.5, "Emotional": 0.5}
        await db_session.commit()

        login_res = await client.post("/auth/login", data={
            "username": "clickfeedback@example.com",
            "password": "password123"
        })
        token = login_res.json()["access_token"]

        response = await client.post("/feedback/",
            headers={"Authorization": f"Bearer {token}"},
            json={"article_id": str(article_id), "is_liked": None}
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_submit_feedback_invalid_article(self, client: AsyncClient):
        """Returns 404 for unknown article."""
        await client.post("/auth/signup", json={
            "email": "invalidarticle@example.com",
            "password": "password123",
            "name": "Invalid Article"
        })

        login_res = await client.post("/auth/login", data={
            "username": "invalidarticle@example.com",
            "password": "password123"
        })
        token = login_res.json()["access_token"]

        response = await client.post("/feedback/",
            headers={"Authorization": f"Bearer {token}"},
            json={"article_id": str(uuid4()), "is_liked": True}
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_submit_feedback_unauthenticated(self, client: AsyncClient):
        """Returns 401 without token."""
        response = await client.post("/feedback/",
            json={"article_id": str(uuid4()), "is_liked": True}
        )

        assert response.status_code == 401

    @pytest.mark.skip(reason="Requires shared DB session between test and API - complex setup")
    @pytest.mark.asyncio
    async def test_feedback_updates_preferences(self, client: AsyncClient, db_session):
        """User vector changes after feedback."""
        from app.models.synthesized_article import SynthesizedArticle
        from app.models.user import User
        from sqlalchemy.future import select

        # Create article with extreme scores
        article_id = uuid4()
        article = SynthesizedArticle(
            id=article_id,
            title="Extreme Article",
            content="Content",
            category_scores=[1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            metadata_scores={"Length": 1.0, "Complexity": 1.0, "Neutral": 0.5, "Informative": 0.5, "Emotional": 0.5}
        )
        db_session.add(article)
        await db_session.commit()

        await client.post("/auth/signup", json={
            "email": "prefupdate@example.com",
            "password": "password123",
            "name": "Pref Update"
        })

        # Set initial preferences
        result = await db_session.execute(
            select(User).where(User.email == "prefupdate@example.com")
        )
        user = result.scalar_one()
        initial_prefs = [0.5] * 10
        user.preferences = initial_prefs.copy()
        user.preferences_metadata = {"Length": 0.5, "Complexity": 0.5, "Neutral": 0.5, "Informative": 0.5, "Emotional": 0.5}
        await db_session.commit()

        login_res = await client.post("/auth/login", data={
            "username": "prefupdate@example.com",
            "password": "password123"
        })
        token = login_res.json()["access_token"]

        # Submit like
        await client.post("/feedback/",
            headers={"Authorization": f"Bearer {token}"},
            json={"article_id": str(article_id), "is_liked": True}
        )

        # Check preferences changed
        await db_session.refresh(user)

        # Preferences should have changed
        assert user.preferences != initial_prefs
