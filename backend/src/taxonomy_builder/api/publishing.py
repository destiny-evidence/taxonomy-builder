"""Publishing workflow API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from fastapi.responses import RedirectResponse

from taxonomy_builder.api.dependencies import CurrentUser, get_publishing_service
from taxonomy_builder.config import settings
from taxonomy_builder.schemas.publishing import (
    VERSION_PATTERN,
    PublishedVersionRead,
    PublishPreview,
    PublishRequest,
)
from taxonomy_builder.services.project_service import (
    ProjectNotFoundError,
    VersionNotFoundError,
)
from taxonomy_builder.services.publishing_service import (
    PublishingService,
    ValidationFailedError,
    VersionConflictError,
)
from taxonomy_builder.services.skos_export_service import FORMAT_CONFIG, ExportFormat

router = APIRouter(prefix="/api/projects", tags=["publishing"])


@router.get(
    "/{project_id}/publish/preview",
    response_model=PublishPreview,
)
async def preview_publish(
    project_id: UUID,
    current_user: CurrentUser,
    service: PublishingService = Depends(get_publishing_service),
) -> PublishPreview:
    """Preview what would be published: validation, diff, content summary."""
    try:
        return await service.preview(project_id)
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/{project_id}/publish",
    response_model=PublishedVersionRead,
    status_code=status.HTTP_201_CREATED,
)
async def publish_version(
    project_id: UUID,
    request: PublishRequest,
    current_user: CurrentUser,
    service: PublishingService = Depends(get_publishing_service),
) -> PublishedVersionRead:
    """Publish a new version (release or pre-release) of a project."""
    try:
        version = await service.publish(
            project_id, request, publisher=current_user.user.display_name
        )
        await service.publish_artifacts(version)
        return PublishedVersionRead.model_validate(version)
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationFailedError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "message": str(e),
                "errors": [err.model_dump(mode="json") for err in e.validation_result.errors],
            },
        )
    except VersionConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get(
    "/{project_id}/versions",
    response_model=list[PublishedVersionRead],
)
async def list_versions(
    project_id: UUID,
    current_user: CurrentUser,
    service: PublishingService = Depends(get_publishing_service),
) -> list[PublishedVersionRead]:
    """List all published versions for a project."""
    try:
        versions = await service.list_versions(project_id)
        return [PublishedVersionRead.model_validate(v) for v in versions]
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/{project_id}/versions/{version}/artifacts",
    response_class=RedirectResponse,
)
async def get_artifact(
    project_id: UUID,
    version: str = Path(pattern=VERSION_PATTERN),
    format: ExportFormat = Query(default=ExportFormat.TTL, description="Export format"),
    service: PublishingService = Depends(get_publishing_service),
) -> RedirectResponse:
    """Redirect to the CDN URL for a published vocabulary artifact."""
    try:
        await service.get_version(project_id, version)
    except VersionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    base = settings.published_base_url.rstrip("/")
    _, _, _, filename = FORMAT_CONFIG[format]
    url = f"{base}/{project_id}/{version}/{filename}"
    return RedirectResponse(url=url)
