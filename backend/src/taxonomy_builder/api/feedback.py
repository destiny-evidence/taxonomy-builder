"""Feedback API endpoints for reader feedback on published entities."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from taxonomy_builder.api.dependencies import (
    get_feedback_service,
    get_manager_feedback_service,
)
from taxonomy_builder.schemas.feedback import (
    FeedbackCreate,
    FeedbackManagerRead,
    FeedbackRead,
    RespondRequest,
    TriageRequest,
)
from taxonomy_builder.services.feedback_service import (
    EntityNotInSnapshotError,
    FeedbackNotFoundError,
    FeedbackService,
    FeedbackStatusConflictError,
    VersionNotFoundError,
)

feedback_router = APIRouter(prefix="/api/feedback", tags=["feedback"])


def _to_response(feedback, *, can_delete: bool) -> dict:
    """Build a reader-facing response dict (no manager identity)."""
    response_dict = None
    if feedback.response_content:
        response_dict = {
            "author": "Vocabulary manager",
            "content": feedback.response_content,
            "created_at": feedback.responded_at,
        }
    return {
        "id": feedback.id,
        "project_id": feedback.project_id,
        "snapshot_version": feedback.snapshot_version,
        "entity_type": feedback.entity_type,
        "entity_id": feedback.entity_id,
        "entity_label": feedback.entity_label,
        "feedback_type": feedback.feedback_type,
        "content": feedback.content,
        "status": feedback.status,
        "response": response_dict,
        "created_at": feedback.created_at,
        "can_delete": can_delete,
    }


def _to_manager_response(feedback) -> dict:
    """Build a manager-facing response dict (includes author info)."""
    base = _to_response(feedback, can_delete=False)
    base["author_name"] = feedback.author_name
    base["responded_by_name"] = feedback.responded_by_name
    return base


# --- Static paths first (before {project_id} / {feedback_id} params) ---


@feedback_router.get(
    "/counts",
)
async def get_open_counts(
    project_ids: list[UUID] = Query(...),
    service: FeedbackService = Depends(get_manager_feedback_service),
) -> dict[str, int]:
    """Open + responded feedback counts per project for badge display."""
    counts = await service.get_open_counts(project_ids)
    return {str(k): v for k, v in counts.items()}


# --- Reader endpoints ---


@feedback_router.post(
    "/{project_id}",
    response_model=FeedbackRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_feedback(
    project_id: UUID,
    feedback_in: FeedbackCreate,
    service: FeedbackService = Depends(get_feedback_service),
) -> dict:
    """Submit feedback on a published entity."""
    try:
        feedback = await service.create(project_id, feedback_in)
        return _to_response(feedback, can_delete=True)
    except VersionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except EntityNotInSnapshotError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )


@feedback_router.get(
    "/{project_id}/mine",
    response_model=list[FeedbackRead],
)
async def list_own_feedback(
    project_id: UUID,
    response: Response,
    version: str | None = None,
    entity_type: str | None = None,
    service: FeedbackService = Depends(get_feedback_service),
) -> list[dict]:
    """List the current user's feedback for a project."""
    response.headers["Cache-Control"] = "private, max-age=0, stale-while-revalidate=300"
    items = await service.list_own(
        project_id, version=version, entity_type=entity_type
    )
    return [_to_response(fb, can_delete=True) for fb in items]


@feedback_router.delete(
    "/{feedback_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_feedback(
    feedback_id: UUID,
    service: FeedbackService = Depends(get_feedback_service),
) -> None:
    """Soft-delete own feedback."""
    try:
        await service.delete(feedback_id)
    except FeedbackNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# --- Manager endpoints ---


@feedback_router.get(
    "/{project_id}/all",
    response_model=list[FeedbackManagerRead],
)
async def list_all_feedback(
    project_id: UUID,
    status_filter: str | None = Query(default=None, alias="status"),
    entity_type: str | None = None,
    feedback_type: str | None = None,
    q: str | None = None,
    limit: int = Query(default=500, le=500, ge=1),
    service: FeedbackService = Depends(get_manager_feedback_service),
) -> list[dict]:
    """All non-deleted feedback for a project (manager view)."""
    items = await service.list_all(
        project_id,
        status=status_filter,
        entity_type=entity_type,
        feedback_type=feedback_type,
        q=q,
        limit=limit,
    )
    return [_to_manager_response(fb) for fb in items]


@feedback_router.post(
    "/{feedback_id}/respond",
    response_model=FeedbackManagerRead,
)
async def respond_to_feedback(
    feedback_id: UUID,
    body: RespondRequest,
    service: FeedbackService = Depends(get_manager_feedback_service),
) -> dict:
    """Add or overwrite a response on feedback."""
    try:
        fb = await service.respond(feedback_id, body.content)
        return _to_manager_response(fb)
    except FeedbackNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except FeedbackStatusConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@feedback_router.post(
    "/{feedback_id}/resolve",
    response_model=FeedbackManagerRead,
)
async def resolve_feedback(
    feedback_id: UUID,
    body: TriageRequest,
    service: FeedbackService = Depends(get_manager_feedback_service),
) -> dict:
    """Resolve feedback, optionally with a response message."""
    try:
        fb = await service.resolve(feedback_id, content=body.content)
        return _to_manager_response(fb)
    except FeedbackNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@feedback_router.post(
    "/{feedback_id}/decline",
    response_model=FeedbackManagerRead,
)
async def decline_feedback(
    feedback_id: UUID,
    body: TriageRequest,
    service: FeedbackService = Depends(get_manager_feedback_service),
) -> dict:
    """Decline feedback, optionally with a response message."""
    try:
        fb = await service.decline(feedback_id, content=body.content)
        return _to_manager_response(fb)
    except FeedbackNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
