"""Database connection and session management."""

import contextlib
from collections.abc import AsyncIterator

from sqlalchemy import String
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.types import TypeDecorator


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


class UrlString(TypeDecorator):
    """Column type that converts URL objects to strings on bind."""

    impl = String
    cache_ok = True

    def __init__(self, length: int = 2048) -> None:
        super().__init__(length)

    def process_bind_param(self, value: object, dialect: object) -> str | None:
        """Convert value to string before storing."""
        return str(value) if value is not None else None


class DatabaseSessionManager:
    """Manages database sessions."""

    def __init__(self) -> None:
        self._engine: AsyncEngine | None = None
        self._sessionmaker: async_sessionmaker[AsyncSession] | None = None

    def init(self, database_url: str) -> None:
        """Initialize the database manager."""
        self._engine = create_async_engine(database_url, echo=False)
        self._sessionmaker = async_sessionmaker(
            bind=self._engine,
            expire_on_commit=False,
        )

    async def close(self) -> None:
        """Close all database connections."""
        if self._engine is None:
            return
        await self._engine.dispose()
        self._engine = None
        self._sessionmaker = None

    @contextlib.asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        """Yield a database session with auto-commit."""
        if self._sessionmaker is None:
            raise RuntimeError("DatabaseSessionManager is not initialized")
        async with self._sessionmaker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    @property
    def engine(self) -> AsyncEngine:
        """Get the engine (for migrations/testing)."""
        if self._engine is None:
            raise RuntimeError("DatabaseSessionManager is not initialized")
        return self._engine


db_manager = DatabaseSessionManager()


async def get_db() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency that provides a database session."""
    async with db_manager.session() as session:
        yield session


def get_constraint_name(exc: Exception) -> str | None:
    """Extract the violated constraint name from an IntegrityError.

    Tries DBAPI-specific attributes first (asyncpg, psycopg2),
    falls back to string matching against the error message.
    """
    orig = getattr(exc, "orig", None)
    if orig is not None:
        # asyncpg stores it directly
        name = getattr(orig, "constraint_name", None)
        if name:
            return str(name)
        # psycopg2 uses diag
        diag = getattr(orig, "diag", None)
        if diag:
            name = getattr(diag, "constraint_name", None)
            if name:
                return str(name)
    # Fallback: search the error message for known constraint names
    msg = str(exc)
    for candidate in (
        "uq_properties_project_uri",
        "uq_ontology_classes_project_uri",
        "uq_property_identifier_per_project",
        "uq_ontology_class_identifier_per_project",
    ):
        if candidate in msg:
            return candidate
    return None
