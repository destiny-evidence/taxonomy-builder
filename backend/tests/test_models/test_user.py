"""Tests for the User model."""

from uuid import UUID

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.user import User
from tests.factories import UserFactory, flush


@pytest.mark.asyncio
async def test_create_user(db_session: AsyncSession) -> None:
    """Test creating a user in the database."""
    user = await flush(
        db_session,
        UserFactory.create(
            keycloak_user_id="keycloak-123",
            email="test@example.com",
            display_name="Test User",
        ),
    )

    assert user.id is not None
    assert isinstance(user.id, UUID)
    assert user.keycloak_user_id == "keycloak-123"
    assert user.email == "test@example.com"
    assert user.display_name == "Test User"
    assert user.created_at is not None
    assert user.updated_at is not None


@pytest.mark.asyncio
async def test_user_id_is_uuidv7(db_session: AsyncSession) -> None:
    """Test that user IDs are UUIDv7 (version 7)."""
    user = await flush(db_session, UserFactory.create())

    assert user.id.version == 7


@pytest.mark.asyncio
async def test_user_keycloak_id_is_unique(db_session: AsyncSession) -> None:
    """Test that keycloak_user_id must be unique."""
    await flush(db_session, UserFactory.create(keycloak_user_id="same-keycloak-id"))

    UserFactory.create(keycloak_user_id="same-keycloak-id")

    with pytest.raises(IntegrityError):
        await db_session.flush()


@pytest.mark.asyncio
async def test_user_email_is_unique(db_session: AsyncSession) -> None:
    """Test that email must be unique."""
    await flush(db_session, UserFactory.create(email="same@example.com"))

    UserFactory.create(email="same@example.com")

    with pytest.raises(IntegrityError):
        await db_session.flush()


@pytest.mark.asyncio
async def test_query_user_by_keycloak_id(db_session: AsyncSession) -> None:
    """Test querying a user by keycloak_user_id."""
    await flush(
        db_session,
        UserFactory.create(keycloak_user_id="query-test-id", email="query@example.com"),
    )

    result = await db_session.execute(
        select(User).where(User.keycloak_user_id == "query-test-id")
    )
    found_user = result.scalar_one()

    assert found_user.email == "query@example.com"


@pytest.mark.asyncio
async def test_user_last_login_is_optional(db_session: AsyncSession) -> None:
    """Test that last_login_at is optional and defaults to None."""
    user = await flush(db_session, UserFactory.create())

    assert user.last_login_at is None
