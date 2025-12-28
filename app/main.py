
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import logging

from app.database import engine, Base
from app.routers import auth, users, ingestion, feed, summary, feedback, interactions

# Import models to ensure they are registered with Base
from app.models import user, article, summary as summary_model, interaction, synthesized_article

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s",
)
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
logger = logging.getLogger("nuze-backend")

# Rate limiter setup
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Nuze Backend",
    version="0.1.0",
    description="Backend for Nuze news aggregation app.",
    redirect_slashes=False,  # Prevent HTTP redirects behind HTTPS proxy
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    origin = request.headers.get("origin")
    logger.info(f"Incoming request: {request.method} {request.url} | Origin: {origin}")
    response = await call_next(request)
    return response

# Add rate limiter state and exception handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://client.nuze.dpdns.org",
    ],
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
