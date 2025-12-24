"""Unit tests for FeedbackService."""
import pytest
import pytest_asyncio
import numpy as np
from uuid import uuid4
from fastapi import HTTPException

from app.services.feedback_service import FeedbackService


class TestRecordFeedback:
    """Tests for FeedbackService.record_feedback - DB-dependent tests"""

    @pytest.mark.asyncio
    async def test_record_feedback_article_not_found(self, db_session):
        """Raises 404 for unknown article."""
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

        service = FeedbackService(db_session)

        with pytest.raises(HTTPException) as exc_info:
            await service.record_feedback(str(user_id), str(uuid4()), is_liked=True)

        assert exc_info.value.status_code == 404


class TestCalculateUpdate:
    """Tests for FeedbackService._calculate_update"""

    def test_calculate_update_positive(self):
        """Validates learning rate math for like."""
        from app.services.feedback_service import FeedbackService
        from unittest.mock import MagicMock

        service = FeedbackService(MagicMock())

        user_vec = np.array([0.5] * 15)
        article_vec = np.array([0.8] * 15)  # Higher than user

        result = service._calculate_update(user_vec, article_vec, is_liked=True)

        assert len(result) == 15
        # Vector should be modified
        assert not np.allclose(result, user_vec)

    def test_calculate_update_negative(self):
        """Validates learning rate math for dislike."""
        from app.services.feedback_service import FeedbackService
        from unittest.mock import MagicMock

        service = FeedbackService(MagicMock())

        user_vec = np.array([0.5] * 15)
        article_vec = np.array([0.8] * 15)

        result = service._calculate_update(user_vec, article_vec, is_liked=False)

        assert len(result) == 15
        assert not np.allclose(result, user_vec)

    def test_calculate_update_click_ratio(self):
        """Click uses 25% of like learning rate."""
        from app.services.feedback_service import FeedbackService
        from unittest.mock import MagicMock

        service = FeedbackService(MagicMock())

        user_vec = np.array([0.5] * 15)
        article_vec = np.array([0.8] * 15)

        like_result = service._calculate_update(user_vec, article_vec, is_liked=True)
        click_result = service._calculate_update(user_vec, article_vec, is_liked=None)

        # Click change should be smaller than like change
        like_diff = np.abs(like_result - user_vec).sum()
        click_diff = np.abs(click_result - user_vec).sum()

        # Click is ~25% of like strength
        assert click_diff < like_diff


class TestHelperMethods:
    """Tests for FeedbackService helper methods"""

    def test_rescale_and_normalize_vector(self):
        """Vector sums to target_sum (5.0)."""
        from app.services.feedback_service import FeedbackService
        from unittest.mock import MagicMock

        service = FeedbackService(MagicMock())

        vec = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        result = service._rescale_and_normalize_vector(vec, target_sum=5.0)

        assert sum(result) == pytest.approx(5.0)

    def test_rescale_and_normalize_vector_negative(self):
        """Handles negative values correctly."""
        from app.services.feedback_service import FeedbackService
        from unittest.mock import MagicMock

        service = FeedbackService(MagicMock())

        vec = np.array([-1.0, 2.0, 3.0])
        result = service._rescale_and_normalize_vector(vec)

        # Should shift negatives up and normalize
        assert all(v >= 0 for v in result)
        assert sum(result) == pytest.approx(5.0)

    def test_metadata_vector_conversion(self):
        """Dict↔Vector conversion works."""
        from app.services.feedback_service import FeedbackService
        from unittest.mock import MagicMock

        service = FeedbackService(MagicMock())

        meta_dict = {
            "Length": 0.7,
            "Complexity": 0.3,
            "Neutral": 0.5,
            "Informative": 0.8,
            "Emotional": 0.2
        }

        vec = service._get_metadata_vector(meta_dict)
        assert len(vec) == 5
        assert vec[0] == 0.7  # Length
        assert vec[1] == 0.3  # Complexity

        # And back
        result_dict = service._get_metadata_dict(vec)
        assert result_dict["Length"] == 0.7
        assert result_dict["Complexity"] == 0.3

    def test_metadata_vector_defaults(self):
        """Missing keys default to 0.5."""
        from app.services.feedback_service import FeedbackService
        from unittest.mock import MagicMock

        service = FeedbackService(MagicMock())

        partial_dict = {"Length": 0.9}
        vec = service._get_metadata_vector(partial_dict)

        assert vec[0] == 0.9      # Length - specified
        assert vec[1] == 0.5      # Complexity - default
