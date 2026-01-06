"""Projects API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.database import get_db
from taxonomy_builder.models.project import Project
from taxonomy_builder.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate
from taxonomy_builder.services.project_service import (
    ProjectNameExistsError,
    ProjectNotFoundError,
    ProjectService,
)

router = APIRouter(prefix="/api/projects", tags=["projects"])


def get_project_service(db: AsyncSession = Depends(get_db)) -> ProjectService:
    """Dependency that provides a ProjectService instance."""
    return ProjectService(db)


@router.get("", response_model=list[ProjectRead])
async def list_projects(
    service: ProjectService = Depends(get_project_service),
) -> list[Project]:
    """List all projects."""
    return await service.list_projects()


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_in: ProjectCreate,
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
    service: ProjectService = Depends(get_project_service),
) -> None:
    """Delete a project."""
    try:
        await service.delete_project(project_id)
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
