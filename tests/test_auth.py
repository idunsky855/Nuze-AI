import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_signup(client: AsyncClient):
    response = await client.post("/auth/signup", json={
        "email": "test@example.com",
        "password": "password123",
        "name": "Test User"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data

@pytest.mark.asyncio
async def test_login(client: AsyncClient):
    # First signup
    await client.post("/auth/signup", json={
        "email": "login@example.com",
        "password": "password123",
        "name": "Login User"
    })
    
    # Then login
    response = await client.post("/auth/login", data={
        "username": "login@example.com",
        "password": "password123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient):
    response = await client.post("/auth/login", data={
        "username": "wrong@example.com",
        "password": "wrongpassword"
    })
    assert response.status_code == 401
