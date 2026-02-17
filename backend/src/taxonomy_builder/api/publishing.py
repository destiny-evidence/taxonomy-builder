"""Publishing workflow API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.api.dependencies import CurrentUser
from taxonomy_builder.database import get_db
from taxonomy_builder.schemas.publishing import (
    PublishedVersionDetail,
    PublishedVersionRead,
    PublishPreview,
    PublishRequest,
    UpdateDraftRequest,
)
from taxonomy_builder.services.concept_service import ConceptService
from taxonomy_builder.services.project_service import ProjectNotFoundError, ProjectService
from taxonomy_builder.services.publishing_service import (
    DraftExistsError,
    NotADraftError,
    PublishingService,
    ValidationFailedError,
    VersionConflictError,
    VersionNotFoundError,
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
    """Publish a new version (or create a draft) of a project."""
    try:
        version = await service.publish(
            project_id, request, publisher=current_user.user.display_name
        )
        return PublishedVersionRead.model_validate(version)
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationFailedError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": str(e),
                "errors": [err.model_dump() for err in e.validation_result.errors],
            },
        )
    except VersionConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except DraftExistsError as e:
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


@router.get(
    "/{project_id}/versions/{version_id}",
    response_model=PublishedVersionDetail,
)
async def get_version(
    project_id: UUID,
    version_id: UUID,
    current_user: CurrentUser,
    service: PublishingService = Depends(_get_publishing_service),
) -> PublishedVersionDetail:
    """Get a single published version with its snapshot."""
    try:
        version = await service.get_version(project_id, version_id)
        return PublishedVersionDetail.model_validate(version)
    except VersionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/{project_id}/versions/{version_id}/finalize",
    response_model=PublishedVersionRead,
)
async def finalize_version(
    project_id: UUID,
    version_id: UUID,
    current_user: CurrentUser,
    service: PublishingService = Depends(_get_publishing_service),
) -> PublishedVersionRead:
    """Promote a draft version to finalized."""
    try:
        version = await service.finalize(project_id, version_id)
        return PublishedVersionRead.model_validate(version)
    except VersionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch(
    "/{project_id}/versions/{version_id}",
    response_model=PublishedVersionRead,
)
async def update_draft(
    project_id: UUID,
    version_id: UUID,
    request: UpdateDraftRequest,
    current_user: CurrentUser,
    service: PublishingService = Depends(_get_publishing_service),
) -> PublishedVersionRead:
    """Update a draft version with a fresh snapshot and optional metadata."""
    try:
        version = await service.update_draft(project_id, version_id, request)
        return PublishedVersionRead.model_validate(version)
    except VersionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except NotADraftError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ValidationFailedError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": str(e),
                "errors": [err.model_dump() for err in e.validation_result.errors],
            },
        )
    except VersionConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.delete(
    "/{project_id}/versions/{version_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_draft(
    project_id: UUID,
    version_id: UUID,
    current_user: CurrentUser,
    service: PublishingService = Depends(_get_publishing_service),
) -> None:
    """Delete a draft version."""
    try:
        await service.delete_draft(project_id, version_id)
    except VersionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except NotADraftError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
