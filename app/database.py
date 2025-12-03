from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import event
from app.config import settings
from pgvector.asyncpg import register_vector

import sys

# Default to localhost postgres if not specified
DATABASE_URL = settings.DATABASE_URL

print("DEBUG: app.database module imported", file=sys.stderr)

engine = create_async_engine(DATABASE_URL, echo=True)

@event.listens_for(engine.sync_engine, "connect")
def connect(dbapi_connection, connection_record):
    print("DEBUG: Registering pgvector on connection", file=sys.stderr)
    # dbapi_connection.run_async(register_vector)
    sys.stderr.flush()

AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
