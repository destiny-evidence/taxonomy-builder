"""Pydantic schemas for the publishing workflow API."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from taxonomy_builder.schemas.snapshot import DiffResult, ValidationResult


class ContentSummary(BaseModel):
    """Summary of what a project contains."""

    schemes: int = 0
    concepts: int = 0
    properties: int = 0
    classes: int = 0


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


PRE_RELEASE_SUFFIX = r"-pre\d+$"


class PublishRequest(BaseModel):
    """Request body for publishing a version."""

    version: str = Field(pattern=VERSION_PATTERN)
    title: str
    notes: str | None = None
    pre_release: bool = False

    @model_validator(mode="after")
    def version_matches_pre_release_flag(self) -> "PublishRequest":
        import re

        has_suffix = bool(re.search(PRE_RELEASE_SUFFIX, self.version))
        if self.pre_release and not has_suffix:
            raise ValueError("pre-release versions must have a -preN suffix")
        if not self.pre_release and has_suffix:
            raise ValueError("release versions must not have a -preN suffix")
        return self


class PublishedVersionRead(BaseModel):
    """Read model for a published version."""

    model_config = {"from_attributes": True}

    id: UUID
    project_id: UUID
    version: str
    title: str
    notes: str | None = None
    finalized: bool
    published_at: datetime
    publisher: str | None = None
    latest: bool = False

    previous_version_id: UUID | None = None
