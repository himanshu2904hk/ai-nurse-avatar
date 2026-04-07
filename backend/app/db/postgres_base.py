"""
################################################################################
#                                                                              #
#                     SQLALCHEMY ASYNC DATABASE ENGINE                         #
#                                                                              #
#   Manages async database connections using SQLAlchemy 2.0.                   #
#   Uses asyncpg as the async PostgreSQL driver.                               #
#                                                                              #
################################################################################
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                        ENGINE & SESSION FACTORY                          ║
# ╚══════════════════════════════════════════════════════════════════════════╝

_engine = None
_session_factory = None


def _build_database_url() -> str:
    """Build async PostgreSQL URL from settings."""
    return (
        f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASSWORD}"
        f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
    )


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                          INIT / CLEANUP                                  ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def init_postgres():
    """Initialize SQLAlchemy async engine and session factory."""
    global _engine, _session_factory

    if _engine is not None:
        return

    _engine = create_async_engine(
        _build_database_url(),
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=0,
        echo=False,
    )

    _session_factory = async_sessionmaker(
        bind=_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    logger.info(f"SQLAlchemy async engine initialized (pool size: {settings.DB_POOL_SIZE})")


async def create_tables():
    """Create all tables defined in models.py (if they don't exist)."""
    from app.db.models import Base

    if _engine is None:
        init_postgres()

    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Database tables created/verified (patient_registry, patient_assessment, patient_visits)")



async def close_postgres():
    """Dispose of the SQLAlchemy engine and close all connections."""
    global _engine, _session_factory

    if _engine:
        await _engine.dispose()
        _engine = None
        _session_factory = None
        logger.info("SQLAlchemy engine disposed")


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                         GET SESSION                                      ║
# ╚══════════════════════════════════════════════════════════════════════════╝

@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get an async database session.

    Usage:
        async with get_session() as session:
            result = await session.execute(select(PatientRegistry))
    """
    if _session_factory is None:
        init_postgres()

    async with _session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
