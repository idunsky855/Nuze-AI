import asyncio
from app.database import AsyncSessionLocal
from app.services.auth_service import AuthService
from app.schemas.user import UserCreate

async def test_signup():
    async with AsyncSessionLocal() as db:
        service = AuthService(db)
        user_in = UserCreate(email="test_script@example.com", password="password", name="Script User")
        try:
            user = await service.create_user(user_in)
            print(f"User created: {user.id}")
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_signup())
