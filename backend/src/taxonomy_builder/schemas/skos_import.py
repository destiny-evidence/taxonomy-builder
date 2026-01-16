"""Pydantic schemas for SKOS import."""

from uuid import UUID

from pydantic import BaseModel, Field


class SchemePreviewResponse(BaseModel):
    """Preview information for a single scheme to be imported."""

    title: str
    description: str | None
    uri: str | None
    concepts_count: int
    relationships_count: int
    warnings: list[str] = Field(default_factory=list)


class ImportPreviewResponse(BaseModel):
    """Response for import preview (dry run)."""

    valid: bool
    schemes: list[SchemePreviewResponse]
    total_concepts_count: int
    total_relationships_count: int
    errors: list[str] = Field(default_factory=list)


class SchemeCreatedResponse(BaseModel):
    """Information about a created scheme."""

    id: UUID
    title: str
    concepts_created: int


class ImportResultResponse(BaseModel):
    """Response for actual import execution."""

    schemes_created: list[SchemeCreatedResponse]
    total_concepts_created: int
    total_relationships_created: int
