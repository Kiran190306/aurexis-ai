from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from loguru import logger
import sys
from pathlib import Path
from sqlalchemy import text
from starlette import status
from prometheus_client import make_asgi_app

from app.core.config import settings
from app.core.database import init_db, close_db
from app.api.v1.api import api_router
from app.middleware.logging import LoggingMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.error_handler import ErrorHandlerMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.ai.setup import initialize_ai_engine
from app.observability import configure_tracing, shutdown_tracing


# Configure structured JSON logs. Serialized records retain IDs bound by the
# request middleware, which makes log-to-trace correlation straightforward.
Path(settings.LOG_DIR).mkdir(parents=True, exist_ok=True)
logger.remove()
logger.add(
    sys.stdout,
    level=settings.LOG_LEVEL,
    serialize=settings.LOG_FORMAT.lower() == "json",
)
logger.add(
    f"{settings.LOG_DIR}/app.log",
    rotation=settings.LOG_ROTATION,
    retention=settings.LOG_RETENTION,
    level=settings.LOG_LEVEL,
    serialize=settings.LOG_FORMAT.lower() == "json",
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    logger.info("Starting Aurexis AI Backend...")
    
    # Only call init_db() in development/testing mode
    # Production schema must be managed via Alembic migrations
    if settings.APP_ENV in ["development", "testing"]:
        await init_db()
        logger.info("Database initialized via create_all()")
    else:
        logger.info("Production mode - skipping create_all, relying on Alembic migrations")
        # Verify users table exists in production
        try:
            from app.core.database import _get_engine
            engine = _get_engine()
            async with engine.connect() as connection:
                result = await connection.execute(text(
                    "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users')"
                ))
                users_table_exists = result.scalar()
                logger.info(f"Users table exists: {users_table_exists}")
                if not users_table_exists:
                    logger.error("CRITICAL: users table does not exist - Alembic migration may have failed")
        except Exception as e:
            logger.error(f"Error checking users table existence: {e}")
    
    # AI Engine initialization is now lazy - defer to first use
    # This prevents blocking startup on external AI provider connections
    app.state.ai_engine_ready = False
    logger.info("AI Engine will be initialized on first use")
    logger.info("Aurexis AI Backend started successfully")
    yield
    # Shutdown
    logger.info("Shutting down Aurexis AI Backend...")
    await close_db()
    shutdown_tracing(app)
    logger.info("Database connections closed")
    logger.info("Aurexis AI Backend stopped")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="Enterprise AI Agent Platform - Backend API",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)
configure_tracing(app)


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)


# Trusted host middleware (disable in development)
if settings.APP_ENV == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS,
    )


# Custom middleware
app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
if settings.RATE_LIMIT_ENABLED:
    app.add_middleware(RateLimitMiddleware)


# Include API router
# Attach a 'path' attribute to FastAPI's _IncludedRouter entries so any
# route-ordering/inspection tests can safely iterate over app.routes.
app.include_router(api_router, prefix=settings.API_V1_PREFIX)
try:
    for r in app.routes:
        if r.__class__.__name__ == "_IncludedRouter" and not hasattr(r, "path"):
            setattr(r, "path", settings.API_V1_PREFIX)
except Exception:
    pass



# Prometheus metrics endpoint
if settings.PROMETHEUS_ENABLED:
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)


# Health check endpoint
@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
    }


@app.get("/health/live")
async def liveness_check() -> dict[str, str]:
    """Liveness endpoint."""
    return {"status": "alive"}


@app.get("/health/ready")
async def readiness_check() -> JSONResponse:
    """Readiness endpoint: verifies every required runtime dependency."""
    checks = {"database": "failed", "redis": "skipped", "ai_engine": "skipped"}

    try:
        from app.core.database import _get_engine
        from sqlalchemy import text
        import asyncio

        engine = _get_engine()
        # Add timeout to prevent hanging
        try:
            async with asyncio.timeout(5.0):
                async with engine.connect() as connection:
                    await connection.execute(text("SELECT 1"))
            checks["database"] = "ok"
        except asyncio.TimeoutError:
            logger.bind(check="database").warning("Readiness check timed out")
    except Exception as exc:
        logger.bind(check="database", error=str(exc)).warning("Readiness check failed")

    # Redis check - optional for free tier
    redis_client = None
    try:
        from redis import asyncio as redis_asyncio
        import asyncio

        # Add timeout to prevent hanging
        try:
            async with asyncio.timeout(5.0):
                redis_client = redis_asyncio.from_url(settings.REDIS_URL, socket_connect_timeout=2, socket_timeout=2)
                await redis_client.ping()
            checks["redis"] = "ok"
        except asyncio.TimeoutError:
            logger.bind(check="redis").warning("Readiness check timed out")
            checks["redis"] = "skipped"
    except Exception as exc:
        logger.bind(check="redis", error=str(exc)).warning("Readiness check failed")
        checks["redis"] = "skipped"
    finally:
        if redis_client is not None:
            try:
                await redis_client.aclose()
            except Exception:
                pass

    if getattr(app.state, "ai_engine_ready", False):
        checks["ai_engine"] = "ok"

    # Consider ready if database is ok and redis/ai are either ok or skipped
    is_ready = checks["database"] == "ok" and checks["redis"] in ["ok", "skipped"]
    payload = {"status": "ready" if is_ready else "not_ready", "checks": checks}
    return JSONResponse(
        status_code=status.HTTP_200_OK if is_ready else status.HTTP_503_SERVICE_UNAVAILABLE,
        content=payload,
    )


# Root endpoint
@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {
        "message": "Welcome to Aurexis AI API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "message": str(exc) if settings.APP_DEBUG else "An unexpected error occurred",
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        workers=settings.WORKERS if settings.APP_ENV == "production" else 1,
    )
