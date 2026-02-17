"""Tests for the AuthService."""

from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.user import User
from taxonomy_builder.services.auth_service import AuthService, AuthenticationError
from tests.factories import UserFactory, flush


@pytest.mark.asyncio
async def test_get_or_create_user_creates_new_user(db_session: AsyncSession) -> None:
    """Test that a new user is created when not found."""
    service = AuthService(db_session)

    token_claims = {
        "sub": "keycloak-new-user-123",
        "email": "newuser@example.com",
        "name": "New User",
    }

    user = await service.get_or_create_user(token_claims)

    assert user.keycloak_user_id == "keycloak-new-user-123"
    assert user.email == "newuser@example.com"
    assert user.display_name == "New User"
    assert user.last_login_at is not None


@pytest.mark.asyncio
async def test_get_or_create_user_returns_existing_user(db_session: AsyncSession) -> None:
    """Test that an existing user is returned when found."""
    existing_user = await flush(
        db_session,
        UserFactory.create(
            keycloak_user_id="keycloak-existing-456",
            email="existing@example.com",
            display_name="Existing User",
        ),
    )
    original_id = existing_user.id

    service = AuthService(db_session)

    token_claims = {
        "sub": "keycloak-existing-456",
        "email": "existing@example.com",
        "name": "Existing User",
    }

    user = await service.get_or_create_user(token_claims)

    assert user.id == original_id
    assert user.last_login_at is not None


@pytest.mark.asyncio
async def test_get_or_create_user_updates_last_login(db_session: AsyncSession) -> None:
    """Test that last_login_at is updated for existing users."""
    existing_user = await flush(
        db_session,
        UserFactory.create(
            keycloak_user_id="keycloak-login-789",
            email="login@example.com",
            display_name="Login User",
        ),
    )

    assert existing_user.last_login_at is None

    service = AuthService(db_session)
    token_claims = {
        "sub": "keycloak-login-789",
        "email": "login@example.com",
        "name": "Login User",
    }

    user = await service.get_or_create_user(token_claims)

    assert user.last_login_at is not None


@pytest.mark.asyncio
async def test_get_or_create_user_uses_preferred_username_fallback(
    db_session: AsyncSession,
) -> None:
    """Test that preferred_username is used if name is not present."""
    service = AuthService(db_session)

    token_claims = {
        "sub": "keycloak-username-fallback",
        "email": "username@example.com",
        "preferred_username": "preferred_user",
    }

    user = await service.get_or_create_user(token_claims)

    assert user.display_name == "preferred_user"


@pytest.mark.asyncio
async def test_get_or_create_user_unknown_fallback(db_session: AsyncSession) -> None:
    """Test that 'Unknown' is used if no name fields are present."""
    service = AuthService(db_session)

    token_claims = {
        "sub": "keycloak-unknown-fallback",
        "email": "unknown@example.com",
    }

    user = await service.get_or_create_user(token_claims)

    assert user.display_name == "Unknown"


@pytest.mark.asyncio
async def test_get_user_by_id(db_session: AsyncSession) -> None:
    """Test getting a user by their internal ID."""
    user = await flush(
        db_session,
        UserFactory.create(
            keycloak_user_id="keycloak-getbyid",
            email="getbyid@example.com",
            display_name="Get By ID User",
        ),
    )

    service = AuthService(db_session)
    found_user = await service.get_user_by_id(user.id)

    assert found_user is not None
    assert found_user.id == user.id


@pytest.mark.asyncio
async def test_get_user_by_id_not_found(db_session: AsyncSession) -> None:
    """Test that None is returned when user not found."""
    from uuid import uuid4

    service = AuthService(db_session)
    found_user = await service.get_user_by_id(uuid4())

    assert found_user is None


@pytest.mark.asyncio
async def test_extract_org_claims_from_token() -> None:
    """Test extracting organization claims from Keycloak token."""
    service = AuthService(None)  # type: ignore - db not needed for this

    token_claims = {
        "sub": "user-123",
        "groups": ["/EEF", "/UCL"],
        "realm_access": {"roles": ["admin", "user"]},
    }

    org_claims = service.extract_org_claims(token_claims)

    assert org_claims["org_id"] == "/EEF"
    assert org_claims["org_name"] == "/EEF"
    assert "admin" in org_claims["roles"]
    assert "user" in org_claims["roles"]


@pytest.mark.asyncio
async def test_extract_org_claims_empty_when_no_org() -> None:
    """Test that empty claims are returned when no org info in token."""
    service = AuthService(None)  # type: ignore

    token_claims = {
        "sub": "user-123",
        "email": "user@example.com",
    }

    org_claims = service.extract_org_claims(token_claims)

    assert org_claims["org_id"] is None
    assert org_claims["org_name"] is None
    assert org_claims["roles"] == []
