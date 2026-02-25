"""Pytest fixtures for testing."""

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

import taxonomy_builder.blob_store as blob_store_module
from taxonomy_builder.api.dependencies import AuthenticatedUser, get_current_user
from taxonomy_builder.blob_store import FilesystemBlobStore, NoOpPurger
from taxonomy_builder.config import settings
from taxonomy_builder.database import Base, db_manager, get_db
from taxonomy_builder.main import app
from taxonomy_builder.models.user import User


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


@pytest.fixture(scope="session", autouse=True)
def _init_blob_store(tmp_path_factory: pytest.TempPathFactory) -> None:
    """Initialise blob store and CDN purger singletons for the test session.

    The app lifespan (which normally does this) is not triggered by test
    clients, so we do it here instead.
    """
    root = tmp_path_factory.mktemp("blob-storage")
    blob_store_module._blob_store = FilesystemBlobStore(root=root)
    blob_store_module._cdn_purger = NoOpPurger()


@pytest.fixture
def blob_store() -> FilesystemBlobStore:
    """Access the test blob store singleton for assertions."""
    store = blob_store_module._blob_store
    assert isinstance(store, FilesystemBlobStore)
    return store


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
    """Provide an async HTTP client for testing API endpoints.

    This client does NOT bypass authentication. Use it for:
    - Testing that unauthenticated requests return 401
    - Testing the /health endpoint (which doesn't require auth)

    For most API tests, use `authenticated_client` instead.
    """
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user in the database."""
    user = User(
        keycloak_user_id="test-keycloak-id-12345",
        email="test@example.com",
        display_name="Test User",
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    # Detach from session to prevent expired state issues across requests
    db_session.expunge(user)
    return user


@pytest.fixture
async def authenticated_client(
    db_session: AsyncSession,
    test_user: User,
) -> AsyncGenerator[AsyncClient, None]:
    """Provide an async HTTP client with authentication bypassed.

    Use this fixture for most API tests. The get_current_user dependency
    is overridden to return a mock AuthenticatedUser without requiring
    actual JWT tokens.
    """

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    async def override_get_current_user() -> AuthenticatedUser:
        return AuthenticatedUser(
            user=test_user,
            org_id="test-org",
            org_name="Test Organization",
            org_roles=["user"],
            client_roles=["api-user", "feedback-user"],
        )

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
