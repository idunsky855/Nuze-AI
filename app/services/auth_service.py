from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin
from app.utils.security import get_password_hash, verify_password, create_access_token

class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_user(self, user_in: UserCreate) -> User:
        # Check if user exists
        result = await self.db.execute(select(User).where(User.email == user_in.email))
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create user
        db_user = User(
            email=user_in.email,
            hashed_password=get_password_hash(user_in.password),
            name=user_in.name
        )
        self.db.add(db_user)
        await self.db.commit()
        await self.db.refresh(db_user)
        return db_user

    async def authenticate_user(self, user_in: UserLogin):
        result = await self.db.execute(select(User).where(User.email == user_in.email))
        user = result.scalar_one_or_none()
        
        if not user:
            return None
        if not verify_password(user_in.password, user.hashed_password):
            return None
        
        return user
