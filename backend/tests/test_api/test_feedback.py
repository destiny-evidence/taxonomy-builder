"""Tests for the Feedback API stub endpoints."""

import pytest
from httpx import AsyncClient

FAKE_PROJECT_ID = "01234567-89ab-7def-8123-456789abcdef"


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
