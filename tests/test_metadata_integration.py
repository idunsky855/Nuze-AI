import asyncio
import sys
import os
import pytest
from sqlalchemy import text
from uuid import uuid4

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import AsyncSessionLocal
from app.services.user_service import UserService
from app.services.feedback_service import FeedbackService
from app.models.user import User
from app.models.synthesized_article import SynthesizedArticle
from app.schemas.user import UserOnboarding

@pytest.mark.asyncio
async def test_metadata_flow():
    print("Starting Metadata Verification...")
    async with AsyncSessionLocal() as db:
        user_service = UserService(db)
        feedback_service = FeedbackService(db)

        # 1. Create User
        user_id = uuid4()
        email = f"test_meta_{user_id}@example.com"
        db_user = User(id=user_id, email=email, hashed_password="pw", name="Test User")
        db.add(db_user)
        await db.commit()

        # Init Vector
        onboarding = UserOnboarding(
            age=25, gender="female", location="urban",
            preferences=["Technology"]
        )
        await user_service.initialize_user_vector(user_id, onboarding)

        # Check Initial State
        prefs, meta = await user_service.get_user_preferences(user_id)
        print(f"Initial Metadata: {meta}")
        assert meta["Length"] == 0.5
        assert meta["Complexity"] == 0.5

        # 2. Create Article with EXTREME metadata
        article_id = uuid4()
        synth = SynthesizedArticle(
            id=article_id,
            title="Long Complex Article",
            content="...",
            category_scores=[0.1]*10, # Irrelevant for this test
            metadata_scores={
                "Length": 1.0, # Very Long
                "Complexity": 1.0, # Very Complex
                "Neutral": 0.5,
                "Informative": 0.5,
                "Emotional": 0.5
            }
        )
        db.add(synth)
        await db.commit()

        # 3. Simulate LIKE
        print("Simulating LIKE on Long/Complex article...")
        await feedback_service.record_feedback(user_id, article_id, is_liked=True)

        # 4. Check Updated State
        new_prefs, new_meta = await user_service.get_user_preferences(user_id)
        print(f"Updated Metadata: {new_meta}")

        # Assertions
        # User liked Long article -> Length pref should increase
        assert new_meta["Length"] > 0.5, f"Length should increase (Got {new_meta['Length']})"
        # User liked Complex article -> Complexity pref should increase
        assert new_meta["Complexity"] > 0.5, f"Complexity should increase (Got {new_meta['Complexity']})"

        print("SUCCESS: Metadata preferences updated correctly!")

        # Cleanup
        await db.execute(text(f"DELETE FROM user_interactions WHERE user_id = '{user_id}'"))
        await db.execute(text(f"DELETE FROM synthesized_articles WHERE id = '{article_id}'"))
        await db.execute(text(f"DELETE FROM users WHERE id = '{user_id}'"))
        await db.commit()

if __name__ == "__main__":
    asyncio.run(test_metadata_flow())
