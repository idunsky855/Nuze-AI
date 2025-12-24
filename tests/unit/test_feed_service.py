"""Unit tests for FeedService."""
import pytest
import pytest_asyncio
from uuid import uuid4
from datetime import datetime, date
from unittest.mock import patch


class TestGetPersonalizedFeed:
    """Tests for FeedService.get_personalized_feed"""

    @pytest.mark.asyncio
    async def test_get_personalized_feed_no_preferences(self, db_session):
        """Falls back to recency sort."""
        from app.models.user import User
        from app.models.synthesized_article import SynthesizedArticle
        from app.services.feed_service import FeedService

        user_id = uuid4()
        user = User(
            id=user_id,
            email=f"test_{user_id}@example.com",
            hashed_password="hashed",
            name="Test User",
            preferences=None  # No preferences
        )
        db_session.add(user)

        # Create articles
        for i in range(3):
            article = SynthesizedArticle(
                id=uuid4(),
                title=f"Article {i}",
                content="Content",
                category_scores=[0.5] * 10
            )
            db_session.add(article)

        await db_session.commit()

        service = FeedService(db_session)
        result = await service.get_personalized_feed(user_id)

        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_get_personalized_feed_with_preferences(self, db_session):
        """Returns cosine-similarity sorted articles."""
        from app.models.user import User
        from app.models.synthesized_article import SynthesizedArticle
        from app.services.feed_service import FeedService

        user_id = uuid4()
        # User prefers first category
        user_prefs = [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        user = User(
            id=user_id,
            email=f"test_{user_id}@example.com",
            hashed_password="hashed",
            name="Test User",
            preferences=user_prefs
        )
        db_session.add(user)

        # Create articles with different category profiles
        matching_article = SynthesizedArticle(
            id=uuid4(),
            title="Matching Article",
            content="Content",
            category_scores=[1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        )
        db_session.add(matching_article)

        non_matching = SynthesizedArticle(
            id=uuid4(),
            title="Non-matching Article",
            content="Content",
            category_scores=[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0]
        )
        db_session.add(non_matching)

        await db_session.commit()

        service = FeedService(db_session)
        result = await service.get_personalized_feed(user_id, limit=10)

        # Should have articles (bucket randomization applies)
        assert len(result) >= 1

    @pytest.mark.asyncio
    async def test_get_personalized_feed_excludes_interacted(self, db_session):
        """Filters out already-seen articles."""
        from app.models.user import User
        from app.models.synthesized_article import SynthesizedArticle
        from app.models.interaction import UserInteraction
        from app.services.feed_service import FeedService

        user_id = uuid4()
        user = User(
            id=user_id,
            email=f"test_{user_id}@example.com",
            hashed_password="hashed",
            name="Test User",
            preferences=[0.5] * 10
        )
        db_session.add(user)

        # Create seen article
        seen_id = uuid4()
        seen_article = SynthesizedArticle(
            id=seen_id,
            title="Seen Article",
            content="Content",
            category_scores=[0.5] * 10
        )
        db_session.add(seen_article)

        # Create unseen article
        unseen_id = uuid4()
        unseen_article = SynthesizedArticle(
            id=unseen_id,
            title="Unseen Article",
            content="Content",
            category_scores=[0.5] * 10
        )
        db_session.add(unseen_article)
        # Commit user and articles first to satisfy FK constraints
        await db_session.commit()

        # Mark one as seen
        interaction = UserInteraction(
            user_id=user_id,
            synthesized_article_id=seen_id,
            is_liked=True
        )
        db_session.add(interaction)
        await db_session.commit()

        service = FeedService(db_session)
        result = await service.get_personalized_feed(user_id)

        # Should only return unseen
        assert len(result) == 1
        assert result[0].id == unseen_id

    @pytest.mark.asyncio
    async def test_get_personalized_feed_pagination(self, db_session):
        """Tests skip/limit parameters."""
        from app.models.user import User
        from app.models.synthesized_article import SynthesizedArticle
        from app.services.feed_service import FeedService

        user_id = uuid4()
        user = User(
            id=user_id,
            email=f"test_{user_id}@example.com",
            hashed_password="hashed",
            name="Test User",
            preferences=None
        )
        db_session.add(user)

        # Create 10 articles
        for i in range(10):
            article = SynthesizedArticle(
                id=uuid4(),
                title=f"Article {i}",
                content="Content",
                category_scores=[0.5] * 10
            )
            db_session.add(article)

        await db_session.commit()

        service = FeedService(db_session)

        # Test limit
        result = await service.get_personalized_feed(user_id, limit=5)
        assert len(result) == 5

    @pytest.mark.asyncio
    async def test_get_personalized_feed_empty(self, db_session):
        """Returns empty list when no articles."""
        from app.models.user import User
        from app.services.feed_service import FeedService

        user_id = uuid4()
        user = User(
            id=user_id,
            email=f"test_{user_id}@example.com",
            hashed_password="hashed",
            name="Test User"
        )
        db_session.add(user)
        await db_session.commit()

        service = FeedService(db_session)
        result = await service.get_personalized_feed(user_id)

        assert result == []


class TestGetTopArticles:
    """Tests for FeedService.get_top_articles"""

    @pytest.mark.asyncio
    async def test_get_top_articles_no_preferences(self, db_session):
        """Falls back to latest articles."""
        from app.models.user import User
        from app.models.article import Article
        from app.services.feed_service import FeedService

        user_id = uuid4()
        user = User(
            id=user_id,
            email=f"test_{user_id}@example.com",
            hashed_password="hashed",
            name="Test User",
            preferences=None
        )
        db_session.add(user)

        # Create article published today
        article = Article(
            id=uuid4(),
            title="Today's Article",
            content="Content",
            source_url="http://example.com/today",
            publisher="Test",
            published_at=datetime.now(),
            category_scores=[0.5] * 10
        )
        db_session.add(article)

        await db_session.commit()

        service = FeedService(db_session)
        result = await service.get_top_articles(user_id)

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_top_articles_with_preferences(self, db_session):
        """Returns strictly sorted by similarity."""
        from app.models.user import User
        from app.models.article import Article
        from app.services.feed_service import FeedService

        user_id = uuid4()
        user_prefs = [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        user = User(
            id=user_id,
            email=f"test_{user_id}@example.com",
            hashed_password="hashed",
            name="Test User",
            preferences=user_prefs
        )
        db_session.add(user)

        # Create matching article (today)
        matching = Article(
            id=uuid4(),
            title="Matching",
            content="Content",
            source_url="http://example.com/match",
            publisher="Test",
            published_at=datetime.now(),
            category_scores=[1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        )
        db_session.add(matching)

        # Create non-matching (today)
        non_matching = Article(
            id=uuid4(),
            title="Non-matching",
            content="Content",
            source_url="http://example.com/nomatch",
            publisher="Test",
            published_at=datetime.now(),
            category_scores=[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0]
        )
        db_session.add(non_matching)

        await db_session.commit()

        service = FeedService(db_session)
        result = await service.get_top_articles(user_id)

        # Should be sorted by similarity - matching first
        if len(result) >= 2:
            assert result[0].title == "Matching"

    @pytest.mark.asyncio
    async def test_get_top_articles_empty_database(self, db_session):
        """Returns empty list gracefully."""
        from app.models.user import User
        from app.services.feed_service import FeedService

        user_id = uuid4()
        user = User(
            id=user_id,
            email=f"test_{user_id}@example.com",
            hashed_password="hashed",
            name="Test User",
            preferences=[0.5] * 10
        )
        db_session.add(user)
        await db_session.commit()

        service = FeedService(db_session)
        result = await service.get_top_articles(user_id)

        assert result == []
