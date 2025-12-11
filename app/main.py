from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.database import engine, Base
from app.routers import auth, users, ingestion, feed, summary, feedback, interactions

# Import models to ensure they are registered with Base
from app.models import user, article, summary as summary_model, interaction, synthesized_article

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s",
)
logger = logging.getLogger("nuze-backend")

app = FastAPI(
    title="Nuze Backend",
    version="0.1.0",
    description="Backend for Nuze news aggregation app.",
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(ingestion.router)
app.include_router(feed.router)
app.include_router(summary.router)
app.include_router(feedback.router)
app.include_router(interactions.router)

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("Starting Nuze Backend")
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Start Scheduler
    import asyncio
    from app.services.scheduler import start_scheduler
    asyncio.create_task(start_scheduler())

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Nuze Backend")

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
