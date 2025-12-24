"""Unit tests for AuthService."""
import pytest
import pytest_asyncio
from uuid import uuid4

from app.services.auth_service import AuthService
from app.schemas.user import UserCreate, UserLogin
from app.utils.security import verify_password


class TestCreateUser:
    """Tests for AuthService.create_user"""

    @pytest.mark.asyncio
    async def test_create_user_success(self, db_session):
        """Creates user with hashed password."""
        service = AuthService(db_session)

        user_data = UserCreate(
            email="newuser@example.com",
            password="securepassword123",
            name="New User"
        )

        user = await service.create_user(user_data)

        assert user.email == "newuser@example.com"
        assert user.name == "New User"
        assert user.id is not None
        # Password should be hashed, not plaintext
        assert user.hashed_password != "securepassword123"

    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(self, db_session):
        """Raises 400 for existing email."""
        from fastapi import HTTPException

        service = AuthService(db_session)

        user_data = UserCreate(
            email="duplicate@example.com",
            password="password123",
            name="User One"
        )

        # Create first user
        await service.create_user(user_data)

        # Try to create duplicate
        with pytest.raises(HTTPException) as exc_info:
            await service.create_user(user_data)

        assert exc_info.value.status_code == 400
        assert "already registered" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_password_is_hashed(self, db_session):
        """Stored password is not plaintext."""
        service = AuthService(db_session)
        plaintext_password = "mySecretPassword"

        user_data = UserCreate(
            email="hashtest@example.com",
            password=plaintext_password,
            name="Hash Test"
        )

        user = await service.create_user(user_data)

        # Hashed password should be different from plaintext
        assert user.hashed_password != plaintext_password
        # But should verify correctly
        assert verify_password(plaintext_password, user.hashed_password)


class TestAuthenticateUser:
    """Tests for AuthService.authenticate_user"""

    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, db_session):
        """Returns user for valid credentials."""
        service = AuthService(db_session)

        # First create a user
        create_data = UserCreate(
            email="authtest@example.com",
            password="correctpassword",
            name="Auth Test"
        )
        created_user = await service.create_user(create_data)

        # Then authenticate
        login_data = UserLogin(
            email="authtest@example.com",
            password="correctpassword"
        )

        user = await service.authenticate_user(login_data)

        assert user is not None
        assert user.id == created_user.id
        assert user.email == "authtest@example.com"

    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_password(self, db_session):
        """Returns None for wrong password."""
        service = AuthService(db_session)

        # First create a user
        create_data = UserCreate(
            email="wrongpw@example.com",
            password="correctpassword",
            name="Wrong PW Test"
        )
        await service.create_user(create_data)

        # Try to authenticate with wrong password
        login_data = UserLogin(
            email="wrongpw@example.com",
            password="wrongpassword"
        )

        user = await service.authenticate_user(login_data)

        assert user is None

    @pytest.mark.asyncio
    async def test_authenticate_user_unknown_email(self, db_session):
        """Returns None for unknown email."""
        service = AuthService(db_session)

        login_data = UserLogin(
            email="nonexistent@example.com",
            password="anypassword"
        )

        user = await service.authenticate_user(login_data)

        assert user is None

    @pytest.mark.asyncio
    async def test_authenticate_preserves_user_data(self, db_session):
        """Authenticated user has correct data."""
        service = AuthService(db_session)

        create_data = UserCreate(
            email="fulldata@example.com",
            password="testpassword",
            name="Full Data User"
        )
        await service.create_user(create_data)

        login_data = UserLogin(
            email="fulldata@example.com",
            password="testpassword"
        )

        user = await service.authenticate_user(login_data)

        assert user.email == "fulldata@example.com"
        assert user.name == "Full Data User"
