"""Unit tests for IngestionService."""
import pytest
import pytest_asyncio
from uuid import uuid4
from datetime import datetime
from unittest.mock import patch, MagicMock, AsyncMock


class TestParseOllamaJson:
    """Tests for IngestionService._parse_ollama_json"""

    def test_parse_ollama_json_valid(self):
        """Parses valid JSON response."""
        from app.services.ingestion_service import IngestionService

        service = IngestionService()

        raw = '{"Politics & Law": 0.5, "Economy & Business": 0.3}'
        result = service._parse_ollama_json(raw)

        assert result is not None
        assert result["Politics & Law"] == 0.5
        assert result["Economy & Business"] == 0.3

    def test_parse_ollama_json_with_markdown(self):
        """Handles markdown code blocks."""
        from app.services.ingestion_service import IngestionService

        service = IngestionService()

        raw = '''```json
{"Politics & Law": 0.5, "Sports": 0.2}
```'''
        result = service._parse_ollama_json(raw)

        assert result is not None
        assert result["Politics & Law"] == 0.5

    def test_parse_ollama_json_with_extra_text(self):
        """Extracts JSON from surrounding text."""
        from app.services.ingestion_service import IngestionService

        service = IngestionService()

        raw = '''Here is the analysis:
{"Politics & Law": 0.5, "Sports": 0.2}
That concludes the result.'''
        result = service._parse_ollama_json(raw)

        assert result is not None
        assert result["Politics & Law"] == 0.5

    def test_parse_ollama_json_invalid(self):
        """Returns None for invalid JSON."""
        from app.services.ingestion_service import IngestionService

        service = IngestionService()

        raw = "This is not JSON at all"
        result = service._parse_ollama_json(raw)

        assert result is None

    def test_parse_ollama_json_nested_category(self):
        """Handles nested category object."""
        from app.services.ingestion_service import IngestionService

        service = IngestionService()

        raw = '{"category": {"Politics & Law": 0.5, "Sports": 0.2}}'
        result = service._parse_ollama_json(raw)

        # Should flatten
        assert result is not None
        assert result["Politics & Law"] == 0.5
        assert "category" not in result


class TestExtractCategoryScores:
    """Tests for IngestionService._extract_category_scores"""

    def test_extract_category_scores_normalization(self):
        """Normalizes scores to sum=5.0."""
        from app.services.ingestion_service import IngestionService

        service = IngestionService()

        result = {
            "Politics & Law": 1.0,
            "Economy & Business": 1.0,
            "Science & Technology": 1.0,
            "Health & Wellness": 1.0,
            "Education & Society": 1.0,
            "Culture & Entertainment": 1.0,
            "Religion & Belief": 1.0,
            "Sports": 1.0,
            "World & International Affairs": 1.0,
            "Opinion & General News": 1.0
        }

        scores = service._extract_category_scores(result)

        assert len(scores) == 10
        assert sum(scores) == pytest.approx(5.0, abs=0.1)

    def test_extract_category_scores_missing_keys(self):
        """Handles missing category keys."""
        from app.services.ingestion_service import IngestionService

        service = IngestionService()

        result = {"Politics & Law": 5.0}  # Only one category

        scores = service._extract_category_scores(result)

        assert len(scores) == 10
        # First should be 5.0 (normalized), rest 0
        assert scores[0] == 5.0

    def test_extract_category_scores_already_normalized(self):
        """Preserves already-normalized scores."""
        from app.services.ingestion_service import IngestionService

        service = IngestionService()

        result = {
            "Politics & Law": 0.5,
            "Economy & Business": 0.5,
            "Science & Technology": 0.5,
            "Health & Wellness": 0.5,
            "Education & Society": 0.5,
            "Culture & Entertainment": 0.5,
            "Religion & Belief": 0.5,
            "Sports": 0.5,
            "World & International Affairs": 0.5,
            "Opinion & General News": 0.5
        }

        scores = service._extract_category_scores(result)

        assert sum(scores) == pytest.approx(5.0, abs=0.1)


class TestCallOllama:
    """Tests for IngestionService._call_ollama"""

    def test_call_ollama_empty_text(self):
        """Returns None for empty input."""
        from app.services.ingestion_service import IngestionService

        service = IngestionService()

        result = service._call_ollama("")
        assert result is None

        result = service._call_ollama(None)
        assert result is None


class TestProcessArticle:
    """Tests for IngestionService.process_article"""

    @pytest.mark.asyncio
    async def test_process_article_dry_run(self, db_session):
        """Logs but doesn't save in dry_run mode."""
        from app.services.ingestion_service import IngestionService
        from app.models.article import Article
        from sqlalchemy.future import select

        service = IngestionService()

        article_data = {
            "url": "http://example.com/dryrun",
            "title": "Dry Run Article",
            "content": "Test content"
        }

        await service.process_article(article_data, dry_run=True)

        # Should not be in database
        async with db_session as session:
            result = await session.execute(
                select(Article).where(Article.source_url == "http://example.com/dryrun")
            )
            assert result.scalar_one_or_none() is None

    @pytest.mark.asyncio
    async def test_process_article_no_url(self):
        """Handles article without URL."""
        from app.services.ingestion_service import IngestionService

        service = IngestionService()

        article_data = {
            "title": "No URL Article",
            "content": "Content"
        }

        # Should not raise
        await service.process_article(article_data)

