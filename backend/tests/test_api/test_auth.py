"""Tests for authentication behavior."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_no_auth_required(client: AsyncClient) -> None:
    """Health endpoint should not require authentication."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


@pytest.mark.asyncio
async def test_projects_requires_auth(client: AsyncClient) -> None:
    """Projects endpoint should require authentication."""
    response = await client.get("/api/projects")
    assert response.status_code == 401
    assert "WWW-Authenticate" in response.headers


@pytest.mark.asyncio
async def test_schemes_requires_auth(client: AsyncClient) -> None:
    """Schemes endpoint should require authentication."""
    # Use a valid UUID format
    response = await client.get("/api/schemes/01234567-89ab-7def-8123-456789abcdef")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_concepts_requires_auth(client: AsyncClient) -> None:
    """Concepts endpoint should require authentication."""
    response = await client.get("/api/concepts/01234567-89ab-7def-8123-456789abcdef")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_authenticated_access_works(authenticated_client: AsyncClient) -> None:
    """Authenticated requests should succeed."""
    response = await authenticated_client.get("/api/projects")
    assert response.status_code == 200
