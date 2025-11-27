from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.user import User
from typing import List

class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_preferences(self, user_id) -> List[float]:
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user and user.preferences is not None:
            # pgvector returns a list or numpy array, let's ensure list
            return list(user.preferences)
        return []

    async def update_user_preferences(self, user_id, preferences: List[float]):
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user:
            user.preferences = preferences
            await self.db.commit()
            await self.db.refresh(user)
            return list(user.preferences)
        return None
