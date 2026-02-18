"""Pydantic schemas for the publishing workflow API."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from taxonomy_builder.schemas.snapshot import DiffResult, ValidationResult


class ContentSummary(BaseModel):
    """Summary of what a project contains."""

    schemes: int = 0
    concepts: int = 0
    properties: int = 0


class PublishPreview(BaseModel):
    """Response from the preview endpoint: validation + diff + content summary."""

    validation: ValidationResult
    diff: DiffResult | None = None
    content_summary: ContentSummary
    suggested_version: str | None = None
    suggested_pre_release_version: str | None = None
    latest_version: str | None = None
    latest_pre_release_version: str | None = None


VERSION_PATTERN = r"^\d+(\.\d+)+(-pre\d+)?$"


class PublishRequest(BaseModel):
    """Request body for publishing a version."""

    version: str = Field(pattern=VERSION_PATTERN)
    title: str
    notes: str | None = None
    pre_release: bool = False


class PublishedVersionRead(BaseModel):
    """Read model for a published version."""

    model_config = {"from_attributes": True}

    id: UUID
    project_id: UUID
    version: str
    title: str
    notes: str | None = None
    finalized: bool
    published_at: datetime | None = None
    publisher: str | None = None
    latest: bool = False

    previous_version_id: UUID | None = None


class PublishedVersionDetail(PublishedVersionRead):
    """Published version with full snapshot data."""

    snapshot: dict
