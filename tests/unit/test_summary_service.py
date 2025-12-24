"""Unit tests for SummaryService."""
import pytest
import pytest_asyncio
from uuid import uuid4
from datetime import datetime, date
from unittest.mock import patch, MagicMock, AsyncMock


class TestGetDailySummary:
    """Tests for SummaryService.get_daily_summary"""

    @pytest.mark.asyncio
    async def test_get_daily_summary_exists(self, db_session):
        """Returns existing summary for today."""
        from app.models.user import User
        from app.models.summary import DailySummary
        from app.services.summary_service import SummaryService

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

        # Create today's summary
        summary = DailySummary(
            id=uuid4(),
            user_id=user_id,
            article_ids=[],
            summary_text={"greeting": "Hello!", "summary": "Test summary"},
            date=date.today()
        )
        db_session.add(summary)
        await db_session.commit()

        service = SummaryService(db_session)
        result = await service.get_daily_summary(str(user_id))

        assert result is not None
        assert result.user_id == user_id

    @pytest.mark.asyncio
    async def test_get_daily_summary_not_found(self, db_session):
        """Returns None when no summary."""
        from app.models.user import User
        from app.services.summary_service import SummaryService

        user_id = uuid4()
        user = User(
            id=user_id,
            email=f"test_{user_id}@example.com",
            hashed_password="hashed",
            name="Test User"
        )
        db_session.add(user)
        await db_session.commit()

        service = SummaryService(db_session)
        result = await service.get_daily_summary(str(user_id))

        assert result is None


class TestGenerateDailySummary:
    """Tests for SummaryService.generate_daily_summary"""

    @pytest.mark.asyncio
    async def test_generate_daily_summary_no_articles(self, db_session):
        """Returns None when no articles."""
        from app.models.user import User
        from app.services.summary_service import SummaryService

        user_id = uuid4()
        user = User(
            id=user_id,
            email=f"test_{user_id}@example.com",
            hashed_password="hashed",
            name="Test User"
        )
        db_session.add(user)
        await db_session.commit()

        service = SummaryService(db_session)
        result = await service.generate_daily_summary(str(user_id))

        assert result is None

    @pytest.mark.asyncio
    @patch('app.services.summary_service.NLPService')
    async def test_generate_daily_summary_success(self, mock_nlp_class, db_session):
        """Creates new summary from articles."""
        from app.models.user import User
        from app.models.article import Article
        from app.services.summary_service import SummaryService

        # Mock NLP service
        mock_nlp = MagicMock()
        mock_nlp.summarize_articles = AsyncMock(return_value='{"greeting": "Hello!", "summary": "News summary", "key_points": ["Point 1"]}')
        mock_nlp_class.return_value = mock_nlp

        user_id = uuid4()
        user = User(
            id=user_id,
            email=f"test_{user_id}@example.com",
            hashed_password="hashed",
            name="Test User",
            preferences=[0.5] * 10,
            preferences_metadata={"Length": 0.5}
        )
        db_session.add(user)

        # Create article published today
        article = Article(
            id=uuid4(),
            title="Today's News",
            content="News content here",
            source_url="http://example.com/news",
            publisher="Test Publisher",
            published_at=datetime.now(),
            category_scores=[0.5] * 10
        )
        db_session.add(article)
        await db_session.commit()

        service = SummaryService(db_session)
        result = await service.generate_daily_summary(str(user_id))

        assert result is not None
        assert result.user_id == user_id
        assert "greeting" in result.summary_text

    @pytest.mark.asyncio
    @patch('app.services.summary_service.NLPService')
    async def test_generate_daily_summary_includes_image(self, mock_nlp_class, db_session):
        """Includes top article image URL."""
        from app.models.user import User
        from app.models.article import Article
        from app.services.summary_service import SummaryService

        mock_nlp = MagicMock()
        mock_nlp.summarize_articles = AsyncMock(return_value='{"greeting": "Hello!", "summary": "News"}')
        mock_nlp_class.return_value = mock_nlp

        user_id = uuid4()
        user = User(
            id=user_id,
            email=f"test_{user_id}@example.com",
            hashed_password="hashed",
            name="Test User",
            preferences=[0.5] * 10
        )
        db_session.add(user)

        # Create article with image
        article = Article(
            id=uuid4(),
            title="Article with Image",
            content="Content",
            source_url="http://example.com/img",
            publisher="Test",
            published_at=datetime.now(),
            category_scores=[0.5] * 10,
            image_url="http://example.com/image.jpg"
        )
        db_session.add(article)
        await db_session.commit()

        service = SummaryService(db_session)
        result = await service.generate_daily_summary(str(user_id))

        assert result is not None
        assert result.summary_text.get("top_image_url") == "http://example.com/image.jpg"

    @pytest.mark.asyncio
    @patch('app.services.summary_service.NLPService')
    async def test_generate_daily_summary_handles_malformed_json(self, mock_nlp_class, db_session):
        """Handles parse errors gracefully."""
        from app.models.user import User
        from app.models.article import Article
        from app.services.summary_service import SummaryService

        mock_nlp = MagicMock()
        mock_nlp.summarize_articles = AsyncMock(return_value='not valid json at all')
        mock_nlp_class.return_value = mock_nlp

        user_id = uuid4()
        user = User(
            id=user_id,
            email=f"test_{user_id}@example.com",
            hashed_password="hashed",
            name="Test User",
            preferences=[0.5] * 10
        )
        db_session.add(user)

        article = Article(
            id=uuid4(),
            title="Article",
            content="Content",
            source_url="http://example.com/test",
            publisher="Test",
            published_at=datetime.now(),
            category_scores=[0.5] * 10
        )
        db_session.add(article)
        await db_session.commit()

        service = SummaryService(db_session)
        result = await service.generate_daily_summary(str(user_id))

        assert result is not None
        # Should have error field
        assert "error" in result.summary_text or "raw" in result.summary_text
