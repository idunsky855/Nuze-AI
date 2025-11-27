import asyncio
from sqlalchemy import text
from app.database import engine

async def enable_vector():
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    print("Vector extension enabled.")

if __name__ == "__main__":
    asyncio.run(enable_vector())
