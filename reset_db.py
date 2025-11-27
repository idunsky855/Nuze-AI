import asyncio
from sqlalchemy import text
from app.database import engine, Base

async def reset_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    print("Database reset.")

if __name__ == "__main__":
    asyncio.run(reset_db())
