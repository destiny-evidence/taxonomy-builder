"""Feedback API endpoints for reader feedback on published entities."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.api.dependencies import AuthenticatedUser, get_current_user
from taxonomy_builder.database import get_db
from taxonomy_builder.schemas.feedback import FeedbackCreate, FeedbackRead
from taxonomy_builder.services.feedback_service import (
    EntityNotInSnapshotError,
    FeedbackNotFoundError,
    FeedbackService,
    VersionNotFoundError,
)

feedback_router = APIRouter(prefix="/api/feedback", tags=["feedback"])


def get_feedback_service(
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> FeedbackService:
    return FeedbackService(
        db,
        user_id=current_user.user.id,
        user_display_name=current_user.user.display_name,
        user_email=current_user.user.email,
    )


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
    version: str | None = None,
    entity_type: str | None = None,
    service: FeedbackService = Depends(get_feedback_service),
) -> list[dict]:
    """List the current user's feedback for a project."""
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


def _to_response(feedback, *, can_delete: bool) -> dict:
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
        "response": feedback.response,
        "created_at": feedback.created_at,
        "can_delete": can_delete,
    }
