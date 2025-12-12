from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
import numpy as np
from sqlalchemy.future import select
from app.models.interaction import UserInteraction
from app.models.synthesized_article import SynthesizedArticle
from app.services.user_service import UserService

class FeedbackService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_service = UserService(db)

    async def record_feedback(self, user_id: str, article_id: str, is_liked: bool | None):
        # 1. Determine article type
        stmt = select(SynthesizedArticle).where(SynthesizedArticle.id == article_id)
        result = await self.db.execute(stmt)
        synth_article = result.scalar_one_or_none()

        if synth_article:
            # Check if interaction already exists
            stmt = select(UserInteraction).where(
                UserInteraction.user_id == user_id,
                UserInteraction.synthesized_article_id == article_id
            )
            result = await self.db.execute(stmt)
            existing_interaction = result.scalar_one_or_none()

            if existing_interaction:
                # Update existing
                if existing_interaction.is_liked == is_liked:
                    # No change, do nothing
                    return existing_interaction

                # Update status
                existing_interaction.is_liked = is_liked
                self.db.add(existing_interaction)
                await self.db.commit()

                # Always update preferences on state change
                await self.update_preferences_from_article(user_id, article_id, is_liked, synth_article)

                return existing_interaction

            # Create new
            interaction = UserInteraction(
                user_id=user_id,
                synthesized_article_id=article_id,
                is_liked=is_liked
            )
        else:
             # If not found in synthesized, we no longer support standard articles
             raise HTTPException(status_code=404, detail="Article not found")

        self.db.add(interaction)

        # 2. Update preferences (New interaction)
        await self.update_preferences_from_article(user_id, article_id, is_liked, synth_article)

        await self.db.commit()
        return interaction

    async def update_preferences_from_article(self, user_id: str, article_id: str, is_liked: bool | None, article_obj=None):
        # Get article vector if we don't have object
        if not article_obj:
             # Try synth
             stmt = select(SynthesizedArticle).where(SynthesizedArticle.id == article_id)
             res = await self.db.execute(stmt)
             article_obj = res.scalar_one_or_none()

        if not article_obj or article_obj.category_scores is None:
            return

        # 1. Construct Article Full Vector (15 dims)
        article_cat_vec = np.array([float(x) for x in article_obj.category_scores])

        # Metadata defaults if missing
        default_meta = {"Length": 0.5, "Complexity": 0.5, "Neutral": 0.5, "Informative": 0.5, "Emotional": 0.5}
        article_meta_dict = article_obj.metadata_scores if article_obj.metadata_scores else default_meta
        article_meta_vec = self._get_metadata_vector(article_meta_dict)

        article_full_vec = np.concatenate([article_cat_vec, article_meta_vec])

        # 2. Get User Full Vector (15 dims)
        user_cat_list, user_meta_dict = await self.user_service.get_user_preferences(user_id)

        if not user_cat_list:
            # Initialize with article vector (rescaled categories, raw metadata)
            # Replicate initialization logic:
            # Categories: Normalize to 5.0
            new_cat_vec = self._rescale_and_normalize_vector(article_cat_vec)
            # Metadata: Keep as is (Assuming article metadata is valid reference point)
            new_meta_vec = article_meta_vec

            new_full_vec = np.concatenate([new_cat_vec, new_meta_vec])
             # Actually we only need to save, not run update math
        else:
            user_cat_vec = np.array(user_cat_list)
            # Use defaults if user has no metadata yet (e.g. legacy user)
            user_meta_dict = user_meta_dict if user_meta_dict else default_meta
            user_meta_vec = self._get_metadata_vector(user_meta_dict)

            user_full_vec = np.concatenate([user_cat_vec, user_meta_vec])

            # 3. Calculate Update on Full Vector
            # updated_vec is raw (not normalized)
            updated_full_vec = self._calculate_update(user_full_vec, article_full_vec, is_liked)

            # 4. Split and Normalize/Clip
            # Split back to 10 and 5
            new_cat_vec = updated_full_vec[:10]
            new_meta_vec = updated_full_vec[10:]

            # Normalize Categories
            new_cat_vec = self._rescale_and_normalize_vector(new_cat_vec)

        # Clip Metadata (0-1)
        # Note: If we entered 'if not user_cat_list' branch, new_meta_vec is defined there too.
        new_meta_vec = np.clip(new_meta_vec, 0.0, 1.0)

        # Convert back to dict
        new_meta_dict = self._get_metadata_dict(new_meta_vec)

        await self.user_service.update_user_preferences(user_id, new_cat_vec.tolist(), new_meta_dict)

    def _get_metadata_vector(self, meta_dict: dict) -> np.array:
        order = ["Length", "Complexity", "Neutral", "Informative", "Emotional"]
        return np.array([float(meta_dict.get(k, 0.5)) for k in order])

    def _get_metadata_dict(self, meta_vec: np.array) -> dict:
        order = ["Length", "Complexity", "Neutral", "Informative", "Emotional"]
        return {k: float(v) for k, v in zip(order, meta_vec)}

    def _rescale_and_normalize_vector(self, vector: np.array, target_sum=5.0) -> np.array:
        min_val = np.min(vector)
        if min_val < 0:
            vector += np.abs(min_val)

        sum_val = np.abs(vector).sum()
        if sum_val > 0:
            vector *= (target_sum / sum_val)
        return vector

    def _calculate_update(self, user_vec: np.array, article_vec: np.array, is_liked: bool | None, learning_rate=0.016) -> np.array:
        median = np.median(user_vec)

        # Avoid division by zero
        safe_median = median if median != 0 else 1e-10
        safe_art_vec = np.where(article_vec == 0, 1e-10, article_vec)

        update_ratio = np.array([
            1 - (art_val / safe_median) if art_val <= safe_median else 1 - (safe_median / art_val)
            for art_val in safe_art_vec
        ])

        updated_vec = np.zeros_like(user_vec)

        # Adjustment Logic
        if is_liked is True:
            # Strengthen (Full LR)
            effective_lr = learning_rate
            for i, val in enumerate(user_vec):
                if article_vec[i] >= median:
                    updated_vec[i] = val + effective_lr * update_ratio[i]
                else:
                    updated_vec[i] = val - effective_lr * update_ratio[i]
        elif is_liked is False:
            # Weaken (Full LR)
            effective_lr = learning_rate
            for i, val in enumerate(user_vec):
                if article_vec[i] <= median:
                    updated_vec[i] = val + effective_lr * update_ratio[i]
                else:
                    updated_vec[i] = val - effective_lr * update_ratio[i]
        else:
            # Click (None) -> Small Strengthen
            # Assume click is ~25% as strong as a Like
            effective_lr = learning_rate * 0.25
            for i, val in enumerate(user_vec):
                if article_vec[i] >= median:
                    updated_vec[i] = val + effective_lr * update_ratio[i]
                else:
                    updated_vec[i] = val - effective_lr * update_ratio[i]

        return updated_vec
