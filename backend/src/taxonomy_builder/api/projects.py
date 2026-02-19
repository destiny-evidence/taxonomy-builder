"""Projects API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.api.dependencies import AuthenticatedUser, CurrentUser, get_current_user, get_import_service
from taxonomy_builder.database import get_db
from taxonomy_builder.models.project import Project
from taxonomy_builder.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate
from taxonomy_builder.schemas.skos_import import ImportPreviewResponse, ImportResultResponse
from taxonomy_builder.services.project_service import (
    ProjectNameExistsError,
    ProjectNotFoundError,
    ProjectService,
)
from taxonomy_builder.services.skos_import_service import (
    InvalidRDFError,
    SchemeURIConflictError,
    SKOSImportService,
)

router = APIRouter(prefix="/api/projects", tags=["projects"])


def get_project_service(
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> ProjectService:
    """Dependency that provides a ProjectService instance with user context."""
    return ProjectService(db, user_id=current_user.user.id)


@router.get("", response_model=list[ProjectRead])
async def list_projects(
    current_user: CurrentUser,
    service: ProjectService = Depends(get_project_service),
) -> list[Project]:
    """List all projects."""
    return await service.list_projects()


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_in: ProjectCreate,
    current_user: CurrentUser,
    service: ProjectService = Depends(get_project_service),
) -> Project:
    """Create a new project."""
    try:
        return await service.create_project(project_in)
    except ProjectNameExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get("/{project_id}", response_model=ProjectRead)
async def get_project(
    project_id: UUID,
    current_user: CurrentUser,
    service: ProjectService = Depends(get_project_service),
) -> Project:
    """Get a single project by ID."""
    try:
        return await service.get_project(project_id)
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{project_id}", response_model=ProjectRead)
async def update_project(
    project_id: UUID,
    project_in: ProjectUpdate,
    current_user: CurrentUser,
    service: ProjectService = Depends(get_project_service),
) -> Project:
    """Update an existing project."""
    try:
        return await service.update_project(project_id, project_in)
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ProjectNameExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: UUID,
    current_user: CurrentUser,
    service: ProjectService = Depends(get_project_service),
) -> None:
    """Delete a project."""
    try:
        await service.delete_project(project_id)
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/{project_id}/import",
    response_model=ImportPreviewResponse | ImportResultResponse,
)
async def import_skos(
    project_id: UUID,
    file: UploadFile = File(...),
    dry_run: bool = Query(default=True),
    project_service: ProjectService = Depends(get_project_service),
    import_service: SKOSImportService = Depends(get_import_service),
) -> ImportPreviewResponse | ImportResultResponse:
    """Import SKOS RDF file into project.

    Args:
        project_id: The project to import into
        file: The RDF file to import
        dry_run: If true (default), return preview without creating entities

    Returns:
        ImportPreviewResponse if dry_run=true, ImportResultResponse if dry_run=false
    """
    # Verify project exists
    try:
        await project_service.get_project(project_id)
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    # Read file content
    content = await file.read()
    filename = file.filename or "unknown.ttl"

    try:
        if dry_run:
            return await import_service.preview(project_id, content, filename)
        else:
            return await import_service.execute(project_id, content, filename)
    except InvalidRDFError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except SchemeURIConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
