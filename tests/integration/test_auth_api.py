"""Integration tests for Auth API endpoints."""
import pytest
from httpx import AsyncClient


class TestSignupEndpoint:
    """Tests for POST /auth/signup"""

    @pytest.mark.asyncio
    async def test_signup_success(self, client: AsyncClient):
        """POST /auth/signup creates new user."""
        response = await client.post("/auth/signup", json={
            "email": "newuser@example.com",
            "password": "securePassword123",
            "name": "New User"
        })

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["name"] == "New User"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_signup_duplicate_email(self, client: AsyncClient):
        """Returns 400 for duplicate email."""
        # First signup
        await client.post("/auth/signup", json={
            "email": "duplicate@example.com",
            "password": "password123",
            "name": "First User"
        })

        # Second signup with same email
        response = await client.post("/auth/signup", json={
            "email": "duplicate@example.com",
            "password": "differentpassword",
            "name": "Second User"
        })

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_signup_invalid_email(self, client: AsyncClient):
        """Returns 422 for invalid email format."""
        response = await client.post("/auth/signup", json={
            "email": "not-an-email",
            "password": "password123",
            "name": "Bad Email User"
        })

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_signup_missing_fields(self, client: AsyncClient):
        """Returns 422 for missing required fields."""
        response = await client.post("/auth/signup", json={
            "email": "incomplete@example.com"
        })

        assert response.status_code == 422


class TestLoginEndpoint:
    """Tests for POST /auth/login"""

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient):
        """POST /auth/login returns token."""
        # First create user
        await client.post("/auth/signup", json={
            "email": "logintest@example.com",
            "password": "correctPassword",
            "name": "Login Test"
        })

        # Then login
        response = await client.post("/auth/login", data={
            "username": "logintest@example.com",
            "password": "correctPassword"
        })

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient):
        """Returns 401 for wrong password."""
        # Create user
        await client.post("/auth/signup", json={
            "email": "wrongpw@example.com",
            "password": "correctPassword",
            "name": "Wrong PW Test"
        })

        # Login with wrong password
        response = await client.post("/auth/login", data={
            "username": "wrongpw@example.com",
            "password": "wrongPassword"
        })

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_unknown_user(self, client: AsyncClient):
        """Returns 401 for unknown email."""
        response = await client.post("/auth/login", data={
            "username": "nonexistent@example.com",
            "password": "anypassword"
        })

        assert response.status_code == 401


class TestTokenValidity:
    """Tests for token-based authentication"""

    @pytest.mark.asyncio
    async def test_token_can_access_protected_endpoints(self, client: AsyncClient):
        """Token can access protected endpoints."""
        # Signup and login
        await client.post("/auth/signup", json={
            "email": "tokentest@example.com",
            "password": "password123",
            "name": "Token Test"
        })

        login_response = await client.post("/auth/login", data={
            "username": "tokentest@example.com",
            "password": "password123"
        })
        token = login_response.json()["access_token"]

        # Access protected endpoint
        response = await client.get("/me", headers={
            "Authorization": f"Bearer {token}"
        })

        assert response.status_code == 200
        assert response.json()["email"] == "tokentest@example.com"

    @pytest.mark.asyncio
    async def test_invalid_token_rejected(self, client: AsyncClient):
        """Invalid token is rejected."""
        response = await client.get("/me", headers={
            "Authorization": "Bearer invalid-token"
        })

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_missing_token_rejected(self, client: AsyncClient):
        """Missing token is rejected."""
        response = await client.get("/me")

        assert response.status_code == 401
