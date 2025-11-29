import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_get_preferences_empty(client: AsyncClient):
    # Signup and login
    await client.post("/auth/signup", json={
        "email": "pref@example.com",
        "password": "password123",
        "name": "Pref User"
    })
    login_res = await client.post("/auth/login", data={
        "username": "pref@example.com",
        "password": "password123"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get preferences
    response = await client.get("/me/preferences", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["interests_vector"] is None or data["interests_vector"] == []

@pytest.mark.asyncio
async def test_update_preferences(client: AsyncClient):
    # Signup and login
    await client.post("/auth/signup", json={
        "email": "update@example.com",
        "password": "password123",
        "name": "Update User"
    })
    login_res = await client.post("/auth/login", data={
        "username": "update@example.com",
        "password": "password123"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Update preferences (dimension 10)
    new_vec = [0.1] * 10
    response = await client.post("/me/preferences", headers=headers, json={
        "interests_vector": new_vec
    })
    assert response.status_code == 200
    
    # Verify update
    response = await client.get("/me/preferences", headers=headers)
    assert response.status_code == 200
    data = response.json()
    # Check approximate equality for floats
    assert data["interests_vector"] == pytest.approx(new_vec)
