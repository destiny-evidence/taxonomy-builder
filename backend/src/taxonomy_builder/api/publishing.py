"""Publishing workflow API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.api.dependencies import CurrentUser
from taxonomy_builder.database import get_db
from taxonomy_builder.schemas.publishing import (
    PublishedVersionRead,
    PublishPreview,
    PublishRequest,
)
from taxonomy_builder.services.concept_service import ConceptService
from taxonomy_builder.services.project_service import ProjectNotFoundError, ProjectService
from taxonomy_builder.services.publishing_service import (
    PublishingService,
    ValidationFailedError,
    VersionConflictError,
)
from taxonomy_builder.services.snapshot_service import SnapshotService

router = APIRouter(prefix="/api/projects", tags=["publishing"])


def _get_publishing_service(db: AsyncSession = Depends(get_db)) -> PublishingService:
    project_service = ProjectService(db)
    concept_service = ConceptService(db)
    snapshot_service = SnapshotService(db, project_service, concept_service)
    return PublishingService(db, project_service, snapshot_service)


@router.get(
    "/{project_id}/publish/preview",
    response_model=PublishPreview,
)
async def preview_publish(
    project_id: UUID,
    current_user: CurrentUser,
    service: PublishingService = Depends(_get_publishing_service),
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
    service: PublishingService = Depends(_get_publishing_service),
) -> PublishedVersionRead:
    """Publish a new version (release or pre-release) of a project."""
    try:
        version = await service.publish(
            project_id, request, publisher=current_user.user.display_name
        )
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
    service: PublishingService = Depends(_get_publishing_service),
) -> list[PublishedVersionRead]:
    """List all published versions for a project."""
    try:
        versions = await service.list_versions(project_id)
        return [PublishedVersionRead.model_validate(v) for v in versions]
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


