"""Feedback API stub endpoints."""

from uuid import UUID

from fastapi import APIRouter

from taxonomy_builder.api.dependencies import CurrentUser

feedback_router = APIRouter(prefix="/api/feedback", tags=["feedback"])


@feedback_router.post("/ui/{project_id}")
async def post_feedback(
    project_id: UUID,
    _user: CurrentUser,
) -> dict:
    """Submit feedback for a project. Requires authentication."""
    return {"status": "ok"}
