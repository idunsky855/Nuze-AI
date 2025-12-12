import asyncio
import sys
import os
import httpx
import pytest
from uuid import uuid4

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import AsyncSessionLocal
from app.models.user import User
from app.utils.security import create_access_token

async def test_preferences_api():
    print("Starting Preferences API Verification...")

    # Setup: Create User directly in DB
    user_id = uuid4()
    email = f"pref_test_{user_id}@example.com"

    async with AsyncSessionLocal() as db:
        user = User(
            id=user_id,
            email=email,
            hashed_password="pw",
            name="Pref Tester",
            preferences=[0.1]*10,
            preferences_metadata={"Length": 0.5}
        )
        db.add(user)
        await db.commit()

    # Generate Token
    token = create_access_token(subject=str(user_id))
    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        # 1. GET /me/preferences
        print("Testing GET /me/preferences...")
        resp = await client.get("/me/preferences", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        print(f"GET Response: {data}")
        assert "interests_vector" in data
        assert "metadata" in data
        assert data["metadata"]["Length"] == 0.5

        # 2. POST /me/preferences (Update Metadata)
        print("Testing POST /me/preferences (Metadata update)...")
        payload = {
            "metadata": {
                "Length": 0.9,
                "Complexity": 0.2,
                "Neutral": 0.1,
                "Informative": 0.8,
                "Emotional": 0.3
            }
        }
        resp = await client.post("/me/preferences", json=payload, headers=headers)
        assert resp.status_code == 200, f"Update failed: {resp.text}"
        data = resp.json()
        print(f"POST Response: {data}")
        assert data["metadata"]["Length"] == 0.9

        # 3. Verify Persistence (GET again)
        print("Verifying persistence...")
        resp = await client.get("/me/preferences", headers=headers)
        data = resp.json()
        assert data["metadata"]["Length"] == 0.9
        assert data["interests_vector"] is not None # Vector should persist
        print(f"Vector (first val): {data['interests_vector'][0]}")
        assert abs(data["interests_vector"][0] - 0.1) < 0.0001

    print("SUCCESS: Preferences API verified!")

    # Cleanup
    async with AsyncSessionLocal() as db:
        from sqlalchemy import text
        await db.execute(text(f"DELETE FROM users WHERE id = '{user_id}'"))
        await db.commit()

if __name__ == "__main__":
    asyncio.run(test_preferences_api())
