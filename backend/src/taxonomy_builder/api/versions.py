"""Versions API routes."""

import re
from enum import Enum
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.api.dependencies import get_version_service
from taxonomy_builder.database import get_db
from taxonomy_builder.schemas.version import (
    PublishedVersionCreate,
    PublishedVersionRead,
)
from taxonomy_builder.services.skos_export_service import SKOSExportService
from taxonomy_builder.services.version_service import (
    DuplicateVersionLabelError,
    SchemeNotFoundError,
    VersionService,
)


class ExportFormat(str, Enum):
    """Supported export formats."""

    TTL = "ttl"
    XML = "xml"
    JSONLD = "jsonld"


# Format to RDFLib format string and content type mapping
FORMAT_CONFIG = {
    ExportFormat.TTL: ("turtle", "text/turtle", ".ttl"),
    ExportFormat.XML: ("xml", "application/rdf+xml", ".rdf"),
    ExportFormat.JSONLD: ("json-ld", "application/ld+json", ".jsonld"),
}


def slugify(text: str) -> str:
    """Convert text to a URL-safe slug."""
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return text.strip("-")

router = APIRouter(prefix="/api", tags=["versions"])


@router.post(
    "/schemes/{scheme_id}/versions",
    response_model=PublishedVersionRead,
    status_code=status.HTTP_201_CREATED,
)
async def publish_version(
    scheme_id: UUID,
    version_in: PublishedVersionCreate,
    service: VersionService = Depends(get_version_service),
) -> PublishedVersionRead:
    """Publish a new version of a scheme."""
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
    service: VersionService = Depends(get_version_service),
) -> list[PublishedVersionRead]:
    """List all published versions for a scheme."""
    versions = await service.list_versions(scheme_id=scheme_id)
    return [PublishedVersionRead.model_validate(v) for v in versions]


@router.get("/versions/{version_id}", response_model=PublishedVersionRead)
async def get_version(
    version_id: UUID,
    service: VersionService = Depends(get_version_service),
) -> PublishedVersionRead:
    """Get a specific published version."""
    version = await service.get_version(version_id=version_id)
    if version is None:
        raise HTTPException(status_code=404, detail="Version not found")
    return PublishedVersionRead.model_validate(version)


@router.get("/versions/{version_id}/export")
async def export_version(
    version_id: UUID,
    format: ExportFormat = Query(default=ExportFormat.TTL, description="Export format"),
    service: VersionService = Depends(get_version_service),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Export a version's snapshot as SKOS RDF.

    Supports multiple formats:
    - ttl: Turtle (default, human-readable)
    - xml: RDF/XML (widest compatibility)
    - jsonld: JSON-LD (web-friendly)
    """
    version = await service.get_version(version_id=version_id)
    if version is None:
        raise HTTPException(status_code=404, detail="Version not found")

    # Get format configuration
    rdflib_format, content_type, extension = FORMAT_CONFIG[format]

    # Export the snapshot
    export_service = SKOSExportService(db)
    content = export_service.export_snapshot(version.snapshot, rdflib_format)

    # Generate filename from scheme title and version label
    scheme_title = version.snapshot.get("scheme", {}).get("title", "scheme")
    filename = f"{slugify(scheme_title)}-v{version.version_label}{extension}"

    return Response(
        content=content,
        media_type=f"{content_type}; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
