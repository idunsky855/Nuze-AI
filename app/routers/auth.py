from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordRequestForm
import logging

from app.database import get_db
from app.schemas.user import UserCreate, UserResponse, Token, UserLogin
from app.services.auth_service import AuthService
from app.utils.security import create_access_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(user: UserCreate, db: AsyncSession = Depends(get_db)):
    logger.info(f"Signup attempt for email: {user.email}")
    auth_service = AuthService(db)
    return await auth_service.create_user(user)

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    # OAuth2PasswordRequestForm expects 'username' and 'password'
    # We map 'username' to 'email'
    auth_service = AuthService(db)
    logger.info(f"Login attempt for {form_data.username}")
    user_in = UserLogin(email=form_data.username, password=form_data.password)
    user = await auth_service.authenticate_user(user_in)

    if not user:
        logger.warning(f"Login failed for {form_data.username}: incorrect credentials")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(subject=user.id)
    return {"access_token": access_token, "token_type": "bearer", "user_id": user.id}
