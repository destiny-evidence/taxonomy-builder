"""Feedback API stub endpoints."""

from uuid import UUID

from fastapi import APIRouter, Response

from taxonomy_builder.api.dependencies import CurrentUser, OptionalUser

feedback_router = APIRouter(prefix="/api/feedback", tags=["feedback"])

FEEDBACK_CACHE_CONTROL = "public, max-age=5, stale-while-revalidate=300"


@feedback_router.get("/ui/{project_id}")
async def get_feedback(
    project_id: UUID,
    _user: OptionalUser,
) -> Response:
    """Return feedback for a project. Public endpoint with caching headers."""
    return Response(
        content="[]",
        media_type="application/json",
        headers={"Cache-Control": FEEDBACK_CACHE_CONTROL},
    )


@feedback_router.post("/ui/{project_id}")
async def post_feedback(
    project_id: UUID,
    _user: CurrentUser,
) -> dict:
    """Submit feedback for a project. Requires authentication."""
    return {"status": "ok"}


@feedback_router.delete("/ui/{project_id}", status_code=204)
async def delete_feedback(
    project_id: UUID,
    _user: CurrentUser,
) -> None:
    """Delete feedback for a project. Requires authentication."""
