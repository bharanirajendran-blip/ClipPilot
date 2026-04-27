"""FastAPI application entry point."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import logging
from supabase import create_client
from redis import Redis
from app.config import settings
from app.utils.logger import setup_logging, get_logger
from app.routes import health, jobs, auth
from app.mcp.routes import router as mcp_router

logger = get_logger(__name__)

# Global clients
supabase_client = None
redis_client = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """FastAPI lifespan context manager for startup/shutdown.

    Args:
        app: FastAPI application

    Yields:
        During application lifetime
    """
    global supabase_client, redis_client

    # Startup
    logger.info("Starting up ClipPilot Lite backend")

    try:
        # Initialize Supabase client
        supabase_client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_ROLE_KEY,
        )
        logger.info("Supabase client initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Supabase: {str(e)}")
        raise

    try:
        # Initialize Redis connection
        redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=False)
        redis_client.ping()
        logger.info("Redis connection established")
    except Exception as e:
        logger.warning(f"Redis not available: {str(e)}. Job queue disabled — API routes still work.")
        redis_client = None

    yield

    # Shutdown
    logger.info("Shutting down")
    try:
        if redis_client:
            redis_client.close()
            logger.info("Redis connection closed")
    except Exception as e:
        logger.warning(f"Error closing Redis: {str(e)}")


# Setup logging
setup_logging()

# Create FastAPI app
app = FastAPI(
    title="ClipPilot Lite API",
    description="Backend API for short vertical video generation",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
cors_origins = settings.BACKEND_CORS_ORIGINS.split(",")
if settings.APP_ENV == "development":
    cors_origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True if settings.APP_ENV != "development" else False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests and responses.

    Args:
        request: HTTP request
        call_next: Next middleware

    Returns:
        HTTP response
    """
    logger.info(f"{request.method} {request.url.path}")

    response = await call_next(request)
    logger.info(f"{request.method} {request.url.path} -> {response.status_code}")

    return response


# Include routers
app.include_router(health.router)
app.include_router(jobs.router)
app.include_router(auth.router)
app.include_router(mcp_router)


# Exception handlers
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions.

    Args:
        request: HTTP request
        exc: Exception

    Returns:
        JSON error response
    """
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error": str(exc) if settings.APP_ENV == "development" else "Unknown error",
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.APP_ENV == "development",
        log_level=settings.LOG_LEVEL.lower(),
    )
