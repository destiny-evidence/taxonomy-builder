"""History API routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from taxonomy_builder.api.dependencies import CurrentUser, get_history_service
from taxonomy_builder.models.change_event import ChangeEvent
from taxonomy_builder.schemas.history import ChangeEventRead
from taxonomy_builder.services import ConceptNotFoundError, ProjectNotFoundError, SchemeNotFoundError
from taxonomy_builder.services.history_service import HistoryService
from taxonomy_builder.services.property_service import PropertyNotFoundError

router = APIRouter(prefix="/api", tags=["history"])


@router.get("/schemes/{scheme_id}/history", response_model=list[ChangeEventRead])
async def get_scheme_history(
    scheme_id: UUID,
    current_user: CurrentUser,
    service: HistoryService = Depends(get_history_service),
    limit: int | None = None,
    offset: int | None = None,
) -> list[ChangeEvent]:
    """Get history of changes for a scheme."""
    try:
        return await service.get_scheme_history(scheme_id, limit, offset)
    except SchemeNotFoundError:
        raise HTTPException(status_code=404, detail="Scheme not found")


@router.get("/concepts/{concept_id}/history", response_model=list[ChangeEventRead])
async def get_concept_history(
    concept_id: UUID,
    current_user: CurrentUser,
    service: HistoryService = Depends(get_history_service),
) -> list[ChangeEvent]:
    """Get history of changes for a specific concept."""
    try:
        return await service.get_concept_history(concept_id)
    except ConceptNotFoundError:
        raise HTTPException(status_code=404, detail="Concept not found")


@router.get("/projects/{project_id}/history", response_model=list[ChangeEventRead])
async def get_project_history(
    project_id: UUID,
    current_user: CurrentUser,
    service: HistoryService = Depends(get_history_service),
    limit: int | None = None,
    offset: int | None = None,
) -> list[ChangeEvent]:
    """Get history of changes for a project."""
    try:
        return await service.get_project_history(project_id, limit, offset)
    except ProjectNotFoundError:
        raise HTTPException(status_code=404, detail="Project not found")


@router.get("/properties/{property_id}/history", response_model=list[ChangeEventRead])
async def get_property_history(
    property_id: UUID,
    current_user: CurrentUser,
    service: HistoryService = Depends(get_history_service),
) -> list[ChangeEvent]:
    """Get history of changes for a specific property."""
    try:
        return await service.get_property_history(property_id)
    except PropertyNotFoundError:
        raise HTTPException(status_code=404, detail="Property not found")
