import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "Nuze Backend"
    PROJECT_VERSION: str = "0.1.0"

    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://news_user:12345678@localhost:5432/news_db")

    SECRET_KEY: str = os.getenv("SECRET_KEY", "supersecretkey")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120  # 2 hours

settings = Settings()
