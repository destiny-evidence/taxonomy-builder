"""Pytest fixtures for testing."""

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from taxonomy_builder.config import settings
from taxonomy_builder.database import Base, db_manager
from taxonomy_builder.main import app


@pytest.fixture(scope="session", autouse=True)
async def _init_db() -> AsyncGenerator[None, None]:
    """Initialize database manager for test session."""
    db_manager.init(settings.test_database_url)
    async with db_manager.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with db_manager.engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await db_manager.close()


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a database session for testing with transaction rollback.

    Each test gets its own transaction that is rolled back after the test,
    ensuring test isolation without affecting the actual database.

    Tests should use `flush()` to persist data within the test, not `commit()`.
    """
    async with db_manager.engine.connect() as conn:
        # Start a transaction
        trans = await conn.begin()

        # Create a session bound to this connection
        test_sessionmaker = async_sessionmaker(
            bind=conn,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        async with test_sessionmaker() as session:
            yield session

        # Rollback the transaction to undo all changes
        await trans.rollback()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Provide an async HTTP client for testing API endpoints."""
    from taxonomy_builder.database import get_db

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
