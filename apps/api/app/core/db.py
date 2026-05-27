"""Async SQLAlchemy engine, session factory, and FastAPI dependency."""

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings

async_engine = create_async_engine(
    get_settings().database_url,
    echo=False,
    pool_pre_ping=True,
    future=True,
)

AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=async_engine,
    expire_on_commit=False,
    autoflush=False,
)


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency yielding an `AsyncSession` inside a transaction.

    The HTTP path auto-commits on success; services receiving the session
    MUST NOT call `session.commit()` themselves.
    """
    async with AsyncSessionLocal() as session, session.begin():
        yield session
