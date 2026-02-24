"""Projects API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import Response

from taxonomy_builder.api.dependencies import (
    CurrentUser,
    get_export_service,
    get_import_service,
    get_project_service,
)
from taxonomy_builder.api.schemes import slugify
from taxonomy_builder.models.project import Project
from taxonomy_builder.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate
from taxonomy_builder.schemas.skos_import import ImportPreviewResponse, ImportResultResponse
from taxonomy_builder.services.project_service import (
    ProjectNameExistsError,
    ProjectNotFoundError,
    ProjectService,
    VersionNotFoundError,
)
from taxonomy_builder.services.skos_export_service import (
    FORMAT_CONFIG,
    ExportFormat,
    SKOSExportService,
)
from taxonomy_builder.services.skos_import_service import (
    InvalidRDFError,
    SKOSImportService,
)

router = APIRouter(prefix="/api/projects", tags=["projects"])


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


@router.get("/{project_id}/versions/{version_id}/export")
async def export_version(
    project_id: UUID,
    version_id: str,
    current_user: CurrentUser,
    format: ExportFormat = Query(default=ExportFormat.TTL, description="Export format"),
    project_service: ProjectService = Depends(get_project_service),
    export_service: SKOSExportService = Depends(get_export_service),
) -> Response:
    """Export a published project version as SKOS RDF."""
    try:
        published_version = await project_service.get_project_version(project_id, version_id)
    except VersionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    rdflib_format, content_type, extension = FORMAT_CONFIG[format]
    content = await export_service.export_published_version(published_version, rdflib_format)
    filename = (
        f"{published_version.project.name}-{published_version.version}-{published_version.title}"
    )
    filename = f"{slugify(filename)}{extension}"

    return Response(
        content=content,
        media_type=f"{content_type}; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
