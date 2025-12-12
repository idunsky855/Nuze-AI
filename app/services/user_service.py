from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.user import User
from typing import List
import logging

logger = logging.getLogger(__name__)

class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_preferences(self, user_id) -> tuple[List[float], dict]:
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user:
            prefs = list(user.preferences) if user.preferences is not None else []
            meta = user.preferences_metadata if user.preferences_metadata else {}
            return prefs, meta
        return [], {}

    async def update_user_preferences(self, user_id, preferences: List[float], metadata: dict = None):
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user:
            user.preferences = preferences
            if metadata is not None:
                user.preferences_metadata = metadata
            await self.db.commit()
            await self.db.refresh(user)
            logger.info(f"Updated preferences for user {user_id}")
            return list(user.preferences)
        return None

    async def initialize_user_vector(self, user_id: str, onboarding_data):
        import numpy as np

        # Constants from heuristic
        categories = [
            "Politics & Law", "Economy & Business", "Science & Technology",
            "Health & Wellness", "Education & Society", "Culture & Entertainment",
            "Religion & Belief", "Sports", "World & International Affairs",
            "Opinion & General News"
        ]
        category_to_index = {cat: idx for idx, cat in enumerate(categories)}
        CATEGORY_DIM = len(categories)
        TARGET_SUM = 5.0 # Sum of all categories should be 5

        DEMOGRAPHIC_INFLUENCES = {
            'age': {
                (0, 17):   {'Culture & Entertainment': 0.15, 'Science & Technology': 0.10, 'Sports': 0.05},
                (18, 24):  {'Culture & Entertainment': 0.10, 'Science & Technology': 0.10, 'Sports': 0.05},
                (25, 34):  {'Science & Technology': 0.10, 'Economy & Business': 0.07, 'Culture & Entertainment': 0.05},
                (35, 49):  {'Health & Wellness': 0.10, 'Education & Society': 0.07, 'Opinion & General News': 0.05},
                (50, 64):  {'Health & Wellness': 0.12, 'Opinion & General News': 0.10},
                (65, 100): {'Health & Wellness': 0.15, 'Opinion & General News': 0.10},
            },
            'gender': {
                'female':      {'Health & Wellness': 0.08, 'Opinion & General News': 0.05},
                'male':        {'Sports': 0.08, 'Science & Technology': 0.05},
                'unknown':     {}
            },
            'location': {
                'urban':    {'Politics & Law': 0.10, 'World & International Affairs': 0.10, 'Economy & Business': 0.05},
                'suburban': {'Education & Society': 0.10, 'Culture & Entertainment': 0.05},
                'rural':    {'Economy & Business': 0.10, 'Education & Society': 0.05},
                'unknown':  {}
            }
        }

        def encode_demographics(age, gender, location):
            vec = np.zeros(CATEGORY_DIM)

            # Age
            for (low, high), weights in DEMOGRAPHIC_INFLUENCES['age'].items():
                if low <= age <= high:
                    for cat, w in weights.items():
                        if cat in category_to_index:
                            vec[category_to_index[cat]] += w
                    break

            # Gender
            weights = DEMOGRAPHIC_INFLUENCES['gender'].get(gender.lower(), {})
            for cat, w in weights.items():
                if cat in category_to_index:
                    vec[category_to_index[cat]] += w

            # Location
            weights = DEMOGRAPHIC_INFLUENCES['location'].get(location.lower(), {})
            for cat, w in weights.items():
                if cat in category_to_index:
                    vec[category_to_index[cat]] += w

            return vec

        def rescale_and_normalize_vector(vector, target_sum=TARGET_SUM):
            min_val = np.min(vector)
            if min_val < 0:
                vector += np.abs(min_val)

            s = np.abs(vector).sum()
            if s > 0:
                vector *= (target_sum / s)
            return vector

        # Calculation Logic
        base = 0.5
        vec = np.ones(CATEGORY_DIM) * base

        # Apply demographics
        vec += encode_demographics(onboarding_data.age, onboarding_data.gender, onboarding_data.location)
        vec = rescale_and_normalize_vector(vec)

        # Apply preferences
        for pref in onboarding_data.preferences:
            if pref in category_to_index:
                vec[category_to_index[pref]] += 0.25

        vec = rescale_and_normalize_vector(vec)

        # Initialize Metadata (Default 0.5)
        metadata_init = {
            "Length": 0.5,
            "Complexity": 0.5,
            "Neutral": 0.5,
            "Informative": 0.5,
            "Emotional": 0.5
        }

        # Update DB
        final_vector = vec.tolist()
        return await self.update_user_preferences(user_id, final_vector, metadata_init)
