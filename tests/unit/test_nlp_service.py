"""Unit tests for NLPService."""
import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock, AsyncMock


class TestClassifyArticle:
    """Tests for NLPService.classify_article"""

    @pytest.mark.asyncio
    @patch('app.services.nlp_service.ollama.AsyncClient')
    async def test_classify_article_success(self, mock_client_class):
        """Returns 10-dim category vector."""
        from app.services.nlp_service import NLPService

        # Mock Ollama response
        mock_response = MagicMock()
        mock_response.message.content = '''{
            "Politics & Law": 0.5,
            "Economy & Business": 0.3,
            "Science & Technology": 0.2,
            "Health & Wellness": 0.0,
            "Education & Society": 0.0,
            "Culture & Entertainment": 0.0,
            "Religion & Belief": 0.0,
            "Sports": 0.0,
            "World & International Affairs": 0.0,
            "Opinion & General News": 0.0
        }'''

        mock_client = MagicMock()
        mock_client.chat = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        service = NLPService()
        result = await service.classify_article("Test article content")

        assert len(result) == 10
        assert result[0] == 0.5  # Politics & Law
        assert result[1] == 0.3  # Economy & Business

    @pytest.mark.asyncio
    @patch('app.services.nlp_service.ollama.AsyncClient')
    async def test_classify_article_error_handling(self, mock_client_class):
        """Returns zero vector on error."""
        from app.services.nlp_service import NLPService

        mock_client = MagicMock()
        mock_client.chat = AsyncMock(side_effect=Exception("Connection error"))
        mock_client_class.return_value = mock_client

        service = NLPService()
        result = await service.classify_article("Test content")

        assert len(result) == 10
        assert all(v == 0.0 for v in result)

    @pytest.mark.asyncio
    @patch('app.services.nlp_service.ollama.AsyncClient')
    async def test_classify_article_json_cleanup(self, mock_client_class):
        """Handles nested category object."""
        from app.services.nlp_service import NLPService

        mock_response = MagicMock()
        mock_response.message.content = '''{
            "category": {
                "Politics & Law": 0.7,
                "Economy & Business": 0.3
            }
        }'''

        mock_client = MagicMock()
        mock_client.chat = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        service = NLPService()
        result = await service.classify_article("Test content")

        assert len(result) == 10
        assert result[0] == 0.7  # Politics & Law flattened


class TestSummarizeArticles:
    """Tests for NLPService.summarize_articles"""

    @pytest.mark.asyncio
    @patch('app.services.nlp_service.ollama.AsyncClient')
    async def test_summarize_articles_success(self, mock_client_class):
        """Returns summary JSON string."""
        from app.services.nlp_service import NLPService

        mock_response = MagicMock()
        mock_response.message.content = '{"greeting": "Good morning!", "summary": "News summary", "key_points": ["Point 1"]}'

        mock_client = MagicMock()
        mock_client.chat = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        service = NLPService()
        result = await service.summarize_articles(
            ["Article 1 content", "Article 2 content"],
            {"Length": 0.5}
        )

        assert "greeting" in result
        assert "summary" in result

    @pytest.mark.asyncio
    @patch('app.services.nlp_service.ollama.AsyncClient')
    async def test_summarize_articles_error(self, mock_client_class):
        """Returns error message on failure."""
        from app.services.nlp_service import NLPService

        mock_client = MagicMock()
        mock_client.chat = AsyncMock(side_effect=Exception("LLM Error"))
        mock_client_class.return_value = mock_client

        service = NLPService()
        result = await service.summarize_articles(["Article content"])

        assert "Failed" in result

    @pytest.mark.asyncio
    @patch('app.services.nlp_service.ollama.AsyncClient')
    async def test_summarize_articles_markdown_cleanup(self, mock_client_class):
        """Strips markdown code blocks."""
        from app.services.nlp_service import NLPService

        mock_response = MagicMock()
        mock_response.message.content = '''```json
{"greeting": "Hello!", "summary": "News"}
```'''

        mock_client = MagicMock()
        mock_client.chat = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        service = NLPService()
        result = await service.summarize_articles(["Content"])

        # Should have cleaned up markdown
        assert result.startswith("{")
        assert result.endswith("}")

    @pytest.mark.asyncio
    @patch('app.services.nlp_service.ollama.AsyncClient')
    async def test_summarize_articles_with_preferences(self, mock_client_class):
        """Passes preferences to model."""
        from app.services.nlp_service import NLPService

        mock_response = MagicMock()
        mock_response.message.content = '{"greeting": "Hello!", "summary": "Custom summary"}'

        mock_client = MagicMock()
        mock_client.chat = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        service = NLPService()

        preferences = {"Length": 0.8, "Complexity": 0.2}
        await service.summarize_articles(["Article"], preferences)

        # Verify chat was called with preferences in prompt
        call_args = mock_client.chat.call_args
        prompt = call_args[1]["messages"][0]["content"]
        assert "preferences" in prompt.lower() or "0.8" in prompt


class TestNLPServiceInit:
    """Tests for NLPService initialization"""

    def test_default_model(self):
        """Uses default model name."""
        from app.services.nlp_service import NLPService

        service = NLPService()
        assert service.model_name == "news-classifier"

    def test_custom_model(self):
        """Accepts custom model name."""
        from app.services.nlp_service import NLPService

        service = NLPService(model_name="custom-model")
        assert service.model_name == "custom-model"
