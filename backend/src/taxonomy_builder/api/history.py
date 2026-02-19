"""History API routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query

from taxonomy_builder.api.dependencies import CurrentUser, get_history_service
from taxonomy_builder.models.change_event import ChangeEvent
from taxonomy_builder.schemas.history import ChangeEventRead
from taxonomy_builder.services.history_service import HistoryService

router = APIRouter(prefix="/api", tags=["history"])


@router.get("/schemes/{scheme_id}/history", response_model=list[ChangeEventRead])
async def get_scheme_history(
    scheme_id: UUID,
    current_user: CurrentUser,
    service: HistoryService = Depends(get_history_service),
    limit: int | None = Query(None, ge=1, le=500),
    offset: int | None = Query(None, ge=0),
) -> list[ChangeEvent]:
    """Get history of changes for a scheme."""
    return await service.get_scheme_history(scheme_id, limit, offset)


@router.get("/concepts/{concept_id}/history", response_model=list[ChangeEventRead])
async def get_concept_history(
    concept_id: UUID,
    current_user: CurrentUser,
    service: HistoryService = Depends(get_history_service),
) -> list[ChangeEvent]:
    """Get history of changes for a specific concept."""
    return await service.get_concept_history(concept_id)


@router.get("/projects/{project_id}/history", response_model=list[ChangeEventRead])
async def get_project_history(
    project_id: UUID,
    current_user: CurrentUser,
    service: HistoryService = Depends(get_history_service),
    limit: int | None = Query(None, ge=1, le=500),
    offset: int | None = Query(None, ge=0),
) -> list[ChangeEvent]:
    """Get history of changes for a project."""
    return await service.get_project_history(project_id, limit, offset)


@router.get("/properties/{property_id}/history", response_model=list[ChangeEventRead])
async def get_property_history(
    property_id: UUID,
    current_user: CurrentUser,
    service: HistoryService = Depends(get_history_service),
) -> list[ChangeEvent]:
    """Get history of changes for a specific property."""
    return await service.get_property_history(property_id)
