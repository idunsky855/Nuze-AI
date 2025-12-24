"""Integration tests for Users API endpoints."""
import pytest
from httpx import AsyncClient
from uuid import uuid4


class TestProfileEndpoint:
    """Tests for GET /me"""

    @pytest.mark.asyncio
    async def test_get_profile(self, client: AsyncClient):
        """GET /me returns user info."""
        await client.post("/auth/signup", json={
            "email": "profile@example.com",
            "password": "password123",
            "name": "Profile User"
        })

        login_res = await client.post("/auth/login", data={
            "username": "profile@example.com",
            "password": "password123"
        })
        token = login_res.json()["access_token"]

        response = await client.get("/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "profile@example.com"
        assert data["name"] == "Profile User"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_get_profile_shows_onboarding_status(self, client: AsyncClient, db_session):
        """Profile shows is_onboarded status."""
        from app.models.user import User
        from sqlalchemy.future import select

        await client.post("/auth/signup", json={
            "email": "onboardstatus@example.com",
            "password": "password123",
            "name": "Onboard Status"
        })

        login_res = await client.post("/auth/login", data={
            "username": "onboardstatus@example.com",
            "password": "password123"
        })
        token = login_res.json()["access_token"]

        # Initially not onboarded
        response = await client.get("/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        assert response.json()["is_onboarded"] is False

        # Set preferences to simulate onboarding
        result = await db_session.execute(
            select(User).where(User.email == "onboardstatus@example.com")
        )
        user = result.scalar_one()
        user.preferences = [0.5] * 10
        await db_session.commit()

        # Now should be onboarded
        response = await client.get("/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.json()["is_onboarded"] is True


class TestPreferencesEndpoints:
    """Tests for /me/preferences"""

    @pytest.mark.asyncio
    async def test_get_preferences(self, client: AsyncClient, db_session):
        """GET /me/preferences returns user preferences."""
        from app.models.user import User
        from sqlalchemy.future import select

        await client.post("/auth/signup", json={
            "email": "getprefs@example.com",
            "password": "password123",
            "name": "Get Prefs"
        })

        # Set preferences
        result = await db_session.execute(
            select(User).where(User.email == "getprefs@example.com")
        )
        user = result.scalar_one()
        user.preferences = [0.3, 0.4, 0.5, 0.6, 0.7, 0.3, 0.4, 0.5, 0.6, 0.7]
        user.preferences_metadata = {"Length": 0.8}
        await db_session.commit()

        login_res = await client.post("/auth/login", data={
            "username": "getprefs@example.com",
            "password": "password123"
        })
        token = login_res.json()["access_token"]

        response = await client.get("/me/preferences",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "interests_vector" in data
        assert "metadata" in data
        assert len(data["interests_vector"]) == 10

    @pytest.mark.asyncio
    async def test_update_preferences(self, client: AsyncClient, db_session):
        """POST /me/preferences updates preferences."""
        from app.models.user import User
        from sqlalchemy.future import select

        await client.post("/auth/signup", json={
            "email": "updateprefs@example.com",
            "password": "password123",
            "name": "Update Prefs"
        })

        result = await db_session.execute(
            select(User).where(User.email == "updateprefs@example.com")
        )
        user = result.scalar_one()
        user.preferences = [0.5] * 10
        await db_session.commit()

        login_res = await client.post("/auth/login", data={
            "username": "updateprefs@example.com",
            "password": "password123"
        })
        token = login_res.json()["access_token"]

        new_prefs = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        response = await client.post("/me/preferences",
            headers={"Authorization": f"Bearer {token}"},
            json={"interests_vector": new_prefs}
        )

        assert response.status_code == 200

        # Verify update
        response = await client.get("/me/preferences",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.json()["interests_vector"] == pytest.approx(new_prefs)


class TestPasswordEndpoint:
    """Tests for POST /me/password"""

    @pytest.mark.asyncio
    async def test_update_password_success(self, client: AsyncClient):
        """POST /me/password updates password."""
        await client.post("/auth/signup", json={
            "email": "pwupdate@example.com",
            "password": "oldPassword123",
            "name": "Password Update"
        })

        login_res = await client.post("/auth/login", data={
            "username": "pwupdate@example.com",
            "password": "oldPassword123"
        })
        token = login_res.json()["access_token"]

        response = await client.post("/me/password",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "current_password": "oldPassword123",
                "new_password": "newPassword456"
            }
        )

        assert response.status_code == 200

        # Verify new password works
        login_res = await client.post("/auth/login", data={
            "username": "pwupdate@example.com",
            "password": "newPassword456"
        })
        assert login_res.status_code == 200

    @pytest.mark.asyncio
    async def test_update_password_wrong_current(self, client: AsyncClient):
        """Returns 400 for wrong current password."""
        await client.post("/auth/signup", json={
            "email": "pwwrong@example.com",
            "password": "correctPassword",
            "name": "Wrong Current"
        })

        login_res = await client.post("/auth/login", data={
            "username": "pwwrong@example.com",
            "password": "correctPassword"
        })
        token = login_res.json()["access_token"]

        response = await client.post("/me/password",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "current_password": "wrongPassword",
                "new_password": "newPassword456"
            }
        )

        assert response.status_code == 400


class TestReadHistoryEndpoint:
    """Tests for GET /me/read"""

    @pytest.mark.asyncio
    async def test_get_read_history(self, client: AsyncClient, db_session):
        """GET /me/read returns read articles."""
        from app.models.synthesized_article import SynthesizedArticle
        from app.models.user import User
        from app.models.interaction import UserInteraction
        from sqlalchemy.future import select

        await client.post("/auth/signup", json={
            "email": "readhistory@example.com",
            "password": "password123",
            "name": "Read History"
        })

        result = await db_session.execute(
            select(User).where(User.email == "readhistory@example.com")
        )
        user = result.scalar_one()

        # Create article
        article_id = uuid4()
        article = SynthesizedArticle(
            id=article_id,
            title="Read Article",
            content="Content",
            category_scores=[0.5] * 10
        )
        db_session.add(article)
        # Commit article first to satisfy FK constraints
        await db_session.commit()

        # Create interaction
        interaction = UserInteraction(
            user_id=user.id,
            synthesized_article_id=article_id,
            is_liked=True
        )
        db_session.add(interaction)
        await db_session.commit()

        login_res = await client.post("/auth/login", data={
            "username": "readhistory@example.com",
            "password": "password123"
        })
        token = login_res.json()["access_token"]

        response = await client.get("/me/read",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        history = response.json()
        assert len(history) == 1
        assert history[0]["title"] == "Read Article"

    @pytest.mark.asyncio
    async def test_get_read_history_empty(self, client: AsyncClient):
        """Returns empty list when no history."""
        await client.post("/auth/signup", json={
            "email": "nohistory@example.com",
            "password": "password123",
            "name": "No History"
        })

        login_res = await client.post("/auth/login", data={
            "username": "nohistory@example.com",
            "password": "password123"
        })
        token = login_res.json()["access_token"]

        response = await client.get("/me/read",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        assert response.json() == []
