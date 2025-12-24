"""Integration tests for the onboarding flow."""
import pytest
from httpx import AsyncClient


class TestOnboardingFlow:
    """End-to-end tests for the onboarding process"""

    @pytest.mark.asyncio
    async def test_full_onboarding_flow(self, client: AsyncClient, db_session):
        """Signup → Onboarding → Feed complete flow."""
        from app.models.synthesized_article import SynthesizedArticle
        from uuid import uuid4

        # Create some articles for feed
        for i in range(3):
            article = SynthesizedArticle(
                id=uuid4(),
                title=f"Test Article {i}",
                content="Content",
                category_scores=[0.5] * 10
            )
            db_session.add(article)
        await db_session.commit()

        # 1. Signup
        signup_res = await client.post("/auth/signup", json={
            "email": "fullflow@example.com",
            "password": "password123",
            "name": "Full Flow User"
        })
        assert signup_res.status_code == 201

        # 2. Login
        login_res = await client.post("/auth/login", data={
            "username": "fullflow@example.com",
            "password": "password123"
        })
        assert login_res.status_code == 200
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 3. Check not onboarded
        profile_res = await client.get("/me", headers=headers)
        assert profile_res.json()["is_onboarded"] is False

        # 4. Submit onboarding
        onboarding_res = await client.post("/me/onboarding",
            headers=headers,
            json={
                "age": 28,
                "gender": "female",
                "location": "urban",
                "preferences": ["Science & Technology", "Health & Wellness", "Culture & Entertainment"]
            }
        )
        assert onboarding_res.status_code == 200

        # 5. Check now onboarded
        profile_res = await client.get("/me", headers=headers)
        assert profile_res.json()["is_onboarded"] is True

        # 6. Check preferences exist
        prefs_res = await client.get("/me/preferences", headers=headers)
        assert prefs_res.status_code == 200
        assert len(prefs_res.json()["interests_vector"]) == 10

        # 7. Get personalized feed
        feed_res = await client.get("/feed/", headers=headers)
        assert feed_res.status_code == 200
        assert isinstance(feed_res.json(), list)

    @pytest.mark.asyncio
    async def test_onboarding_initializes_vector(self, client: AsyncClient):
        """POST /me/onboarding creates preference vector."""
        await client.post("/auth/signup", json={
            "email": "vectorinit@example.com",
            "password": "password123",
            "name": "Vector Init"
        })

        login_res = await client.post("/auth/login", data={
            "username": "vectorinit@example.com",
            "password": "password123"
        })
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Check no vector initially
        prefs_res = await client.get("/me/preferences", headers=headers)
        initial_vector = prefs_res.json()["interests_vector"]
        assert initial_vector == [] or initial_vector is None

        # Onboard
        await client.post("/me/onboarding",
            headers=headers,
            json={
                "age": 35,
                "gender": "male",
                "location": "suburban",
                "preferences": ["Sports", "Economy & Business"]
            }
        )

        # Check vector exists
        prefs_res = await client.get("/me/preferences", headers=headers)
        new_vector = prefs_res.json()["interests_vector"]
        assert new_vector is not None
        assert len(new_vector) == 10
        # Vector should sum to approximately 5.0
        assert sum(new_vector) == pytest.approx(5.0, abs=0.1)

    @pytest.mark.asyncio
    async def test_onboarding_metadata_initialized(self, client: AsyncClient):
        """Onboarding initializes metadata defaults."""
        await client.post("/auth/signup", json={
            "email": "metainit@example.com",
            "password": "password123",
            "name": "Meta Init"
        })

        login_res = await client.post("/auth/login", data={
            "username": "metainit@example.com",
            "password": "password123"
        })
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Onboard
        await client.post("/me/onboarding",
            headers=headers,
            json={
                "age": 22,
                "gender": "unknown",
                "location": "rural",
                "preferences": ["Education & Society"]
            }
        )

        # Check metadata
        prefs_res = await client.get("/me/preferences", headers=headers)
        metadata = prefs_res.json()["metadata"]

        assert metadata["Length"] == 0.5
        assert metadata["Complexity"] == 0.5
        assert metadata["Neutral"] == 0.5
        assert metadata["Informative"] == 0.5
        assert metadata["Emotional"] == 0.5

    @pytest.mark.asyncio
    async def test_is_onboarded_flag_update(self, client: AsyncClient):
        """Profile shows is_onboarded=true after onboarding."""
        await client.post("/auth/signup", json={
            "email": "flagupdate@example.com",
            "password": "password123",
            "name": "Flag Update"
        })

        login_res = await client.post("/auth/login", data={
            "username": "flagupdate@example.com",
            "password": "password123"
        })
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Before onboarding
        profile_res = await client.get("/me", headers=headers)
        assert profile_res.json()["is_onboarded"] is False

        # Onboard
        await client.post("/me/onboarding",
            headers=headers,
            json={
                "age": 45,
                "gender": "female",
                "location": "urban",
                "preferences": ["Politics & Law", "World & International Affairs", "Opinion & General News"]
            }
        )

        # After onboarding
        profile_res = await client.get("/me", headers=headers)
        assert profile_res.json()["is_onboarded"] is True

    @pytest.mark.asyncio
    async def test_onboarding_with_demographics(self, client: AsyncClient):
        """Demographics influence initial vector."""
        await client.post("/auth/signup", json={
            "email": "demographics@example.com",
            "password": "password123",
            "name": "Demographics"
        })

        login_res = await client.post("/auth/login", data={
            "username": "demographics@example.com",
            "password": "password123"
        })
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Young urban user
        await client.post("/me/onboarding",
            headers=headers,
            json={
                "age": 20,
                "gender": "male",
                "location": "urban",
                "preferences": []  # No explicit preferences
            }
        )

        # Check vector was created with demographic influences
        prefs_res = await client.get("/me/preferences", headers=headers)
        vector = prefs_res.json()["interests_vector"]

        assert vector is not None
        assert len(vector) == 10
        # Vector shouldn't be all equal (demographics should create variation)
        assert len(set(round(v, 2) for v in vector)) > 1

    @pytest.mark.asyncio
    async def test_onboarding_unauthenticated(self, client: AsyncClient):
        """Onboarding requires authentication."""
        response = await client.post("/me/onboarding",
            json={
                "age": 30,
                "gender": "female",
                "location": "urban",
                "preferences": ["Sports"]
            }
        )

        assert response.status_code == 401
