"""ConceptScheme API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.database import get_db
from taxonomy_builder.models.concept_scheme import ConceptScheme
from taxonomy_builder.schemas.concept_scheme import (
    ConceptSchemeCreate,
    ConceptSchemeRead,
    ConceptSchemeUpdate,
)
from taxonomy_builder.services.concept_scheme_service import (
    ConceptSchemeService,
    ProjectNotFoundError,
    SchemeNotFoundError,
    SchemeTitleExistsError,
)

# Router for project-scoped scheme operations
project_schemes_router = APIRouter(prefix="/api/projects", tags=["schemes"])

# Router for direct scheme operations
schemes_router = APIRouter(prefix="/api/schemes", tags=["schemes"])


def get_scheme_service(db: AsyncSession = Depends(get_db)) -> ConceptSchemeService:
    """Dependency that provides a ConceptSchemeService instance."""
    return ConceptSchemeService(db)


@project_schemes_router.get("/{project_id}/schemes", response_model=list[ConceptSchemeRead])
async def list_schemes(
    project_id: UUID,
    service: ConceptSchemeService = Depends(get_scheme_service),
) -> list[ConceptScheme]:
    """List all concept schemes for a project."""
    try:
        return await service.list_schemes_for_project(project_id)
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@project_schemes_router.post(
    "/{project_id}/schemes",
    response_model=ConceptSchemeRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_scheme(
    project_id: UUID,
    scheme_in: ConceptSchemeCreate,
    service: ConceptSchemeService = Depends(get_scheme_service),
) -> ConceptScheme:
    """Create a new concept scheme in a project."""
    try:
        return await service.create_scheme(project_id, scheme_in)
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except SchemeTitleExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@schemes_router.get("/{scheme_id}", response_model=ConceptSchemeRead)
async def get_scheme(
    scheme_id: UUID,
    service: ConceptSchemeService = Depends(get_scheme_service),
) -> ConceptScheme:
    """Get a single concept scheme by ID."""
    try:
        return await service.get_scheme(scheme_id)
    except SchemeNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@schemes_router.put("/{scheme_id}", response_model=ConceptSchemeRead)
async def update_scheme(
    scheme_id: UUID,
    scheme_in: ConceptSchemeUpdate,
    service: ConceptSchemeService = Depends(get_scheme_service),
) -> ConceptScheme:
    """Update an existing concept scheme."""
    try:
        return await service.update_scheme(scheme_id, scheme_in)
    except SchemeNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except SchemeTitleExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@schemes_router.delete("/{scheme_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scheme(
    scheme_id: UUID,
    service: ConceptSchemeService = Depends(get_scheme_service),
) -> None:
    """Delete a concept scheme."""
    try:
        await service.delete_scheme(scheme_id)
    except SchemeNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
