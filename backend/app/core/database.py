from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
from typing import AsyncGenerator, Optional

from app.core.config import settings

# Lazy-loaded database engine
_engine: Optional[create_async_engine] = None
_AsyncSessionLocal: Optional[async_sessionmaker] = None


def _get_engine_kwargs() -> dict:
    """Get engine kwargs based on settings."""
    engine_kwargs = {
        "echo": settings.DATABASE_ECHO,
        "pool_pre_ping": True,
    }

    # Only add pool parameters for PostgreSQL (not SQLite)
    if "postgresql" in settings.DATABASE_URL:
        engine_kwargs.update({
            "pool_size": settings.DATABASE_POOL_SIZE,
            "max_overflow": settings.DATABASE_MAX_OVERFLOW,
        })

    # Use NullPool for testing
    if settings.APP_ENV == "testing":
        engine_kwargs["poolclass"] = NullPool

    return engine_kwargs


def _get_engine():
    """Get or create the database engine (lazy-loaded)."""
    global _engine, _AsyncSessionLocal
    if _engine is None:
        engine_kwargs = _get_engine_kwargs()
        _engine = create_async_engine(settings.DATABASE_URL, **engine_kwargs)
        _AsyncSessionLocal = async_sessionmaker(
            _engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    return _engine


def _get_session_maker():
    """Get or create the session maker (lazy-loaded)."""
    global _AsyncSessionLocal
    if _AsyncSessionLocal is None:
        _get_engine()  # Ensure engine is created
    return _AsyncSessionLocal


# Backward compatibility: export AsyncSessionLocal as a callable proxy
def AsyncSessionLocal(*args, **kwargs):
    """Proxy for lazy-loaded AsyncSessionLocal."""
    return _get_session_maker()(*args, **kwargs)


# Base class for models
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database sessions.
    """
    session_maker = _get_session_maker()
    async with session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database tables.
    """
    engine = _get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """
    Close database connections.
    """
    global _engine, _AsyncSessionLocal
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _AsyncSessionLocal = None
