import asyncio
import sys
import os
from sqlalchemy import text

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import AsyncSessionLocal

async def alter_table():
    print("Altering table to allow NULL is_liked...")
    async with AsyncSessionLocal() as db:
        try:
            # Ensure is_liked allows NULL
            await db.execute(text("ALTER TABLE user_interactions ALTER COLUMN is_liked DROP NOT NULL"))
            await db.commit()
            print("Successfully altered table.")
        except Exception as e:
            print(f"Error altering table: {e}")
            await db.rollback()

if __name__ == "__main__":
    asyncio.run(alter_table())
