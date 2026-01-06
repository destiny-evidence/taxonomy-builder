"""Versions API routes."""

from uuid import UUID

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.database import get_db
from taxonomy_builder.schemas.version import (
    PublishedVersionCreate,
    PublishedVersionRead,
)
from taxonomy_builder.services.version_service import (
    DuplicateVersionLabelError,
    SchemeNotFoundError,
    VersionService,
)

router = APIRouter(prefix="/api", tags=["versions"])


@router.post(
    "/schemes/{scheme_id}/versions",
    response_model=PublishedVersionRead,
    status_code=status.HTTP_201_CREATED,
)
async def publish_version(
    scheme_id: UUID,
    version_in: PublishedVersionCreate,
    db: AsyncSession = Depends(get_db),
) -> PublishedVersionRead:
    """Publish a new version of a scheme."""
    service = VersionService(db)
    try:
        version = await service.publish_version(
            scheme_id=scheme_id,
            version_label=version_in.version_label,
            notes=version_in.notes,
        )
        return PublishedVersionRead.model_validate(version)
    except SchemeNotFoundError:
        raise HTTPException(status_code=404, detail="Scheme not found")
    except DuplicateVersionLabelError:
        raise HTTPException(
            status_code=409, detail="Version label already exists for this scheme"
        )


@router.get("/schemes/{scheme_id}/versions", response_model=list[PublishedVersionRead])
async def list_versions(
    scheme_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> list[PublishedVersionRead]:
    """List all published versions for a scheme."""
    service = VersionService(db)
    versions = await service.list_versions(scheme_id=scheme_id)
    return [PublishedVersionRead.model_validate(v) for v in versions]


@router.get("/versions/{version_id}", response_model=PublishedVersionRead)
async def get_version(
    version_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> PublishedVersionRead:
    """Get a specific published version."""
    service = VersionService(db)
    version = await service.get_version(version_id=version_id)
    if version is None:
        raise HTTPException(status_code=404, detail="Version not found")
    return PublishedVersionRead.model_validate(version)


@router.get("/versions/{version_id}/export")
async def export_version(
    version_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Export a version's snapshot as JSON."""
    service = VersionService(db)
    version = await service.get_version(version_id=version_id)
    if version is None:
        raise HTTPException(status_code=404, detail="Version not found")
    return JSONResponse(content=version.snapshot)
