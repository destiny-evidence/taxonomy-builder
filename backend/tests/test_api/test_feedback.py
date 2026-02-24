"""Tests for the Feedback API stub endpoints."""

import pytest
from httpx import AsyncClient

from taxonomy_builder.api.feedback import FEEDBACK_CACHE_CONTROL

FAKE_PROJECT_ID = "01234567-89ab-7def-8123-456789abcdef"


@pytest.mark.asyncio
async def test_get_feedback_no_auth(client: AsyncClient) -> None:
    """GET feedback should work without authentication."""
    response = await client.get(f"/api/feedback/ui/{FAKE_PROJECT_ID}")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_feedback_cache_headers(client: AsyncClient) -> None:
    """GET feedback should set stale-while-revalidate Cache-Control."""
    response = await client.get(f"/api/feedback/ui/{FAKE_PROJECT_ID}")
    assert response.status_code == 200
    assert response.headers["cache-control"] == FEEDBACK_CACHE_CONTROL


@pytest.mark.asyncio
async def test_get_feedback_returns_list(client: AsyncClient) -> None:
    """GET feedback should return a list (empty stub for now)."""
    response = await client.get(f"/api/feedback/ui/{FAKE_PROJECT_ID}")
    assert response.json() == []


@pytest.mark.asyncio
async def test_post_feedback_requires_auth(client: AsyncClient) -> None:
    """POST feedback should require authentication."""
    response = await client.post(
        f"/api/feedback/ui/{FAKE_PROJECT_ID}",
        json={"body": "Great taxonomy!"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_post_feedback_authenticated(authenticated_client: AsyncClient) -> None:
    """POST feedback should succeed with authentication."""
    response = await authenticated_client.post(
        f"/api/feedback/ui/{FAKE_PROJECT_ID}",
        json={"body": "Great taxonomy!"},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_delete_feedback_requires_auth(client: AsyncClient) -> None:
    """DELETE feedback should require authentication."""
    response = await client.delete(f"/api/feedback/ui/{FAKE_PROJECT_ID}")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_delete_feedback_authenticated(authenticated_client: AsyncClient) -> None:
    """DELETE feedback should succeed with authentication."""
    response = await authenticated_client.delete(f"/api/feedback/ui/{FAKE_PROJECT_ID}")
    assert response.status_code == 204
