from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from app.database import get_db
from app.schemas.preferences import PreferencesUpdate, PreferencesResponse
from app.services.user_service import UserService
from app.utils.security import settings
from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

async def get_current_user_id(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        return user_id
    except JWTError:
        raise credentials_exception

router = APIRouter(prefix="/me", tags=["users"])

@router.get("/preferences", response_model=PreferencesResponse)
async def get_preferences(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    user_service = UserService(db)
    prefs, meta = await user_service.get_user_preferences(user_id)
    return {"interests_vector": prefs, "metadata": meta}

@router.post("/preferences", response_model=PreferencesResponse)
async def update_preferences(
    prefs_in: PreferencesUpdate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    if not prefs_in.interests_vector and not prefs_in.metadata:
        raise HTTPException(status_code=400, detail="No preferences provided")

    user_service = UserService(db)
    # We need current prefs if we are only updating metadata?
    # Service update_user_preferences replaces vector.
    # If interests_vector is None, `update_user_preferences` might error or overwrite with None?
    # Schema says Optional.
    # Logic in service: user.preferences = preferences.
    # If I pass None, it saves None? Wait, service definition type hint list[float].
    # I should check service again.

    current_prefs, current_meta = await user_service.get_user_preferences(user_id)

    new_vector = prefs_in.interests_vector if prefs_in.interests_vector is not None else current_prefs
    new_metadata = prefs_in.metadata if prefs_in.metadata is not None else current_meta

    updated_prefs = await user_service.update_user_preferences(user_id, new_vector, new_metadata)

    # Return updated state
    # update_user_preferences returns vector list.
    # I should fetch fresh or just return what we have.
    # But update_user_preferences modifies the object in session.
    # Let's re-fetch or assume successful update.
    # Actually service returns `list(user.preferences)`.
    # It doesn't return metadata.
    # So I will construct response manually from inputs/current state.

    return {"interests_vector": updated_prefs, "metadata": new_metadata}

from app.schemas.user import UserOnboarding

@router.post("/onboarding", response_model=PreferencesResponse)
async def onboarding(
    data: UserOnboarding,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    user_service = UserService(db)
    updated_prefs = await user_service.initialize_user_vector(user_id, data)
    return {"interests_vector": updated_prefs}

from app.schemas.user import UserResponse
from app.models.user import User
from sqlalchemy.future import select

@router.get("", response_model=UserResponse)
async def get_current_user_profile(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if onboarded (heuristic: preferences vector exists)
    is_onboarded = user.preferences is not None

    # We can create a response object or just return a dict that matches schema
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "age": user.age,
        "gender": user.gender,
        "location": user.location,
        "is_onboarded": is_onboarded
    }

from app.schemas.user import UserPasswordUpdate
from app.utils.security import verify_password, get_password_hash

@router.post("/password")
async def update_password(
    data: UserPasswordUpdate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_password(data.current_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect current password")

    user.hashed_password = get_password_hash(data.new_password)
    # No need to add to session if fetched from it, just commit
    await db.commit()

    return {"message": "Password updated successfully"}

from app.schemas.user import UserProfileUpdate

@router.put("", response_model=UserResponse)
async def update_profile(
    profile_data: UserProfileUpdate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update only the fields that were provided
    if profile_data.first_name is not None:
        user.first_name = profile_data.first_name
    if profile_data.last_name is not None:
        user.last_name = profile_data.last_name
    if profile_data.age is not None:
        user.age = profile_data.age
    if profile_data.gender is not None:
        user.gender = profile_data.gender
    if profile_data.location is not None:
        user.location = profile_data.location

    await db.commit()
    await db.refresh(user)

    is_onboarded = user.preferences is not None
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "age": user.age,
        "gender": user.gender,
        "location": user.location,
        "is_onboarded": is_onboarded
    }

from typing import List
from app.schemas.article import ArticleResponse

@router.get("/read", response_model=List[ArticleResponse])
async def get_read_history(
    skip: int = 0,
    limit: int = 20,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    from app.models.interaction import UserInteraction
    from sqlalchemy.future import select

    user_service = UserService(db)
    articles = await user_service.get_read_articles(user_id, limit, skip)

    # Fetch user interactions for these articles
    article_ids = [article.id for article in articles]
    interactions_result = await db.execute(
        select(UserInteraction).where(
            UserInteraction.user_id == user_id,
            UserInteraction.synthesized_article_id.in_(article_ids)
        )
    )
    interactions = {i.synthesized_article_id: i.is_liked for i in interactions_result.scalars().all()}

    # Populate is_liked field
    response = []
    for article in articles:
        article_dict = ArticleResponse.model_validate(article).model_dump()
        article_dict['is_liked'] = interactions.get(article.id)
        response.append(ArticleResponse(**article_dict))

    return response
