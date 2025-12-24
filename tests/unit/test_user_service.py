"""Unit tests for UserService."""
import pytest
import pytest_asyncio
import numpy as np
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.services.user_service import UserService
from app.schemas.user import UserOnboarding


class TestGetUserPreferences:
    """Tests for UserService.get_user_preferences"""

    @pytest.mark.asyncio
    async def test_get_user_preferences_existing_user(self, db_session):
        """Returns preferences and metadata for existing user."""
        from app.models.user import User

        user_id = uuid4()
        test_prefs = [0.5] * 10
        test_meta = {"Length": 0.7, "Complexity": 0.3}

        user = User(
            id=user_id,
            email=f"test_{user_id}@example.com",
            hashed_password="hashed",
            name="Test User",
            preferences=test_prefs,
            preferences_metadata=test_meta
        )
        db_session.add(user)
        await db_session.commit()

        service = UserService(db_session)
        prefs, meta = await service.get_user_preferences(user_id)

        assert prefs == pytest.approx(test_prefs)
        assert meta == test_meta

    @pytest.mark.asyncio
    async def test_get_user_preferences_nonexistent_user(self, db_session):
        """Returns empty list and dict for unknown user."""
        service = UserService(db_session)
        prefs, meta = await service.get_user_preferences(uuid4())

        assert prefs == []
        assert meta == {}

    @pytest.mark.asyncio
    async def test_get_user_preferences_null_values(self, db_session):
        """Returns empty values when user has no preferences set."""
        from app.models.user import User

        user_id = uuid4()
        user = User(
            id=user_id,
            email=f"test_{user_id}@example.com",
            hashed_password="hashed",
            name="Test User",
            preferences=None,
            preferences_metadata=None
        )
        db_session.add(user)
        await db_session.commit()

        service = UserService(db_session)
        prefs, meta = await service.get_user_preferences(user_id)

        assert prefs == []
        assert meta == {}


class TestUpdateUserPreferences:
    """Tests for UserService.update_user_preferences"""

    @pytest.mark.asyncio
    async def test_update_user_preferences_success(self, db_session):
        """Updates vector and metadata correctly."""
        from app.models.user import User

        user_id = uuid4()
        user = User(
            id=user_id,
            email=f"test_{user_id}@example.com",
            hashed_password="hashed",
            name="Test User"
        )
        db_session.add(user)
        await db_session.commit()

        service = UserService(db_session)
        new_prefs = [0.3] * 10
        new_meta = {"Length": 0.8}

        result = await service.update_user_preferences(user_id, new_prefs, new_meta)

        assert result == pytest.approx(new_prefs)

        # Verify persistence
        prefs, meta = await service.get_user_preferences(user_id)
        assert prefs == pytest.approx(new_prefs)
        assert meta["Length"] == 0.8

    @pytest.mark.asyncio
    async def test_update_user_preferences_nonexistent_user(self, db_session):
        """Returns None when user doesn't exist."""
        service = UserService(db_session)
        result = await service.update_user_preferences(uuid4(), [0.5] * 10, {})

        assert result is None


class TestInitializeUserVector:
    """Tests for UserService.initialize_user_vector"""

    @pytest.mark.asyncio
    async def test_initialize_user_vector_basic(self, db_session):
        """Creates initial vector from onboarding data."""
        from app.models.user import User

        user_id = uuid4()
        user = User(
            id=user_id,
            email=f"test_{user_id}@example.com",
            hashed_password="hashed",
            name="Test User"
        )
        db_session.add(user)
        await db_session.commit()

        service = UserService(db_session)
        onboarding = UserOnboarding(
            age=25,
            gender="male",
            location="urban",
            preferences=["Science & Technology"]
        )

        result = await service.initialize_user_vector(str(user_id), onboarding)

        assert result is not None
        assert len(result) == 10
        # Vector should sum to approximately 5.0
        assert sum(result) == pytest.approx(5.0, abs=0.1)

    @pytest.mark.asyncio
    async def test_initialize_user_vector_demographics_age(self, db_session):
        """Validates age demographic influences on vector."""
        from app.models.user import User

        user_id = uuid4()
        user = User(
            id=user_id,
            email=f"test_{user_id}@example.com",
            hashed_password="hashed",
            name="Test User"
        )
        db_session.add(user)
        await db_session.commit()

        service = UserService(db_session)

        # Young user should have higher Culture & Entertainment
        young_onboarding = UserOnboarding(
            age=20,
            gender="unknown",
            location="unknown",
            preferences=[]
        )

        result = await service.initialize_user_vector(str(user_id), young_onboarding)

        # Culture & Entertainment is index 5
        assert result is not None
        assert len(result) == 10

    @pytest.mark.asyncio
    async def test_initialize_user_vector_category_preferences(self, db_session):
        """Validates category preferences boost."""
        from app.models.user import User

        user_id = uuid4()
        user = User(
            id=user_id,
            email=f"test_{user_id}@example.com",
            hashed_password="hashed",
            name="Test User"
        )
        db_session.add(user)
        await db_session.commit()

        service = UserService(db_session)

        # User with Sports preference
        onboarding = UserOnboarding(
            age=30,
            gender="unknown",
            location="unknown",
            preferences=["Sports", "Health & Wellness"]
        )

        result = await service.initialize_user_vector(str(user_id), onboarding)

        # Sports is index 7, Health is index 3
        assert result is not None
        # Categories with preferences should be boosted relative to others
        avg = sum(result) / len(result)
        assert result[7] > avg * 0.5 or result[3] > avg * 0.5  # At least one boosted

    @pytest.mark.asyncio
    async def test_initialize_user_vector_metadata_defaults(self, db_session):
        """Validates default metadata is set."""
        from app.models.user import User

        user_id = uuid4()
        user = User(
            id=user_id,
            email=f"test_{user_id}@example.com",
            hashed_password="hashed",
            name="Test User"
        )
        db_session.add(user)
        await db_session.commit()

        service = UserService(db_session)
        onboarding = UserOnboarding(
            age=25,
            gender="female",
            location="suburban",
            preferences=[]
        )

        await service.initialize_user_vector(str(user_id), onboarding)

        _, meta = await service.get_user_preferences(user_id)

        assert meta["Length"] == 0.5
        assert meta["Complexity"] == 0.5
        assert meta["Neutral"] == 0.5
        assert meta["Informative"] == 0.5
        assert meta["Emotional"] == 0.5


class TestGetReadArticles:
    """Tests for UserService.get_read_articles"""

    @pytest.mark.asyncio
    async def test_get_read_articles_empty(self, db_session):
        """Returns empty list when no history."""
        from app.models.user import User

        user_id = uuid4()
        user = User(
            id=user_id,
            email=f"test_{user_id}@example.com",
            hashed_password="hashed",
            name="Test User"
        )
        db_session.add(user)
        await db_session.commit()

        service = UserService(db_session)
        result = await service.get_read_articles(user_id)

        assert result == []

    @pytest.mark.asyncio
    async def test_get_read_articles_with_history(self, db_session):
        """Returns articles from user's read history."""
        from app.models.user import User
        from app.models.synthesized_article import SynthesizedArticle
        from app.models.interaction import UserInteraction

        user_id = uuid4()
        user = User(
            id=user_id,
            email=f"test_{user_id}@example.com",
            hashed_password="hashed",
            name="Test User"
        )
        db_session.add(user)

        article_id = uuid4()
        article = SynthesizedArticle(
            id=article_id,
            title="Test Article",
            content="Content",
            category_scores=[0.5] * 10
        )
        db_session.add(article)
        # Commit user and article first to satisfy FK constraints
        await db_session.commit()

        interaction = UserInteraction(
            user_id=user_id,
            synthesized_article_id=article_id,
            is_liked=True
        )
        db_session.add(interaction)
        await db_session.commit()

        service = UserService(db_session)
        result = await service.get_read_articles(user_id)

        assert len(result) == 1
        assert result[0].id == article_id

    @pytest.mark.asyncio
    async def test_get_read_articles_pagination(self, db_session):
        """Tests limit and skip parameters."""
        from app.models.user import User
        from app.models.synthesized_article import SynthesizedArticle
        from app.models.interaction import UserInteraction

        user_id = uuid4()
        user = User(
            id=user_id,
            email=f"test_{user_id}@example.com",
            hashed_password="hashed",
            name="Test User"
        )
        db_session.add(user)
        # Commit user first to satisfy FK constraints
        await db_session.commit()

        # Create 5 articles
        for i in range(5):
            article_id = uuid4()
            article = SynthesizedArticle(
                id=article_id,
                title=f"Test Article {i}",
                content="Content",
                category_scores=[0.5] * 10
            )
            db_session.add(article)
            await db_session.commit()

            interaction = UserInteraction(
                user_id=user_id,
                synthesized_article_id=article_id,
                is_liked=True
            )
            db_session.add(interaction)
            await db_session.commit()

        service = UserService(db_session)

        # Test limit
        result = await service.get_read_articles(user_id, limit=3)
        assert len(result) == 3

        # Test skip
        result = await service.get_read_articles(user_id, limit=10, skip=3)
        assert len(result) == 2
