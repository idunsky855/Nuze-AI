import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_db
from app.main import app
from app.config import settings
import asyncio
from sqlalchemy import text

# Use a separate test database to avoid wiping production data
TEST_DATABASE_URL = settings.DATABASE_URL.replace("/news_db", "/news_db_test")

@pytest_asyncio.fixture(scope="function")
async def db_session():
    # Create engine per test to avoid loop issues
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    TestingSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Create tables
    async with engine.begin() as conn:
        # Drop tables with CASCADE to handle dependencies
        tables = ["daily_summaries", "user_interactions", "synthesized_sources", "synthesized_articles", "article_reads", "articles", "users"]
        for table in tables:
            await conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))

        await conn.run_sync(Base.metadata.create_all)
        # Enable vector extension
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

    async with TestingSessionLocal() as session:
        yield session

    await engine.dispose()

@pytest_asyncio.fixture(scope="function")
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
