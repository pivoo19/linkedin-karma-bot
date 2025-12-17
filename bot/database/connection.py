"""
Database connection management using SQLAlchemy 2.0 async.

Supports both SQLite (via aiosqlite) and PostgreSQL (via asyncpg).
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from bot.models import Base

# Global engine and session factory
_engine: AsyncEngine | None = None
_async_session_factory: async_sessionmaker[AsyncSession] | None = None


def init_engine(database_url: str, echo: bool = False) -> AsyncEngine:
    """
    Initialize the database engine.

    Args:
        database_url: Database URL. Examples:
            - SQLite: "sqlite+aiosqlite:///./data.db"
            - PostgreSQL: "postgresql+asyncpg://user:pass@localhost/dbname"
        echo: Whether to log all SQL statements

    Returns:
        Initialized async engine
    """
    global _engine, _async_session_factory

    # Create async engine
    _engine = create_async_engine(
        database_url,
        echo=echo,
        pool_pre_ping=True,  # Verify connections before using
        pool_recycle=3600,   # Recycle connections after 1 hour
    )

    # Create session factory
    _async_session_factory = async_sessionmaker(
        _engine,
        class_=AsyncSession,
        expire_on_commit=False,  # Don't expire objects after commit
    )

    return _engine


def get_engine() -> AsyncEngine:
    """
    Get the current database engine.

    Returns:
        The initialized engine

    Raises:
        RuntimeError: If engine hasn't been initialized
    """
    if _engine is None:
        raise RuntimeError(
            "Database engine not initialized. Call init_engine() first."
        )
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """
    Get the session factory.

    Returns:
        The session factory

    Raises:
        RuntimeError: If session factory hasn't been initialized
    """
    if _async_session_factory is None:
        raise RuntimeError(
            "Session factory not initialized. Call init_engine() first."
        )
    return _async_session_factory


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Async context manager for database sessions.

    Usage:
        async with get_session() as session:
            # Use session here
            result = await session.execute(select(User))

    Yields:
        AsyncSession instance
    """
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize the database by creating all tables.

    This should be called once when the application starts.
    """
    engine = get_engine()

    async with engine.begin() as conn:
        # Create all tables defined in Base metadata
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """
    Close the database connection and dispose of the engine.

    This should be called when the application shuts down.
    """
    global _engine, _async_session_factory

    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _async_session_factory = None
