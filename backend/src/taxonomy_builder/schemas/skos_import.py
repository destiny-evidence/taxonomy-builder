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


class ClassPreviewResponse(BaseModel):
    """Preview information for an OWL class to be imported."""

    identifier: str
    label: str
    uri: str


class PropertyPreviewResponse(BaseModel):
    """Preview information for a property to be imported."""

    identifier: str
    label: str
    property_type: str  # "object" or "datatype"
    domain_class_uri: str | None
    range_uri: str | None
    range_scheme_title: str | None  # resolved scheme title, if matched


class ImportPreviewResponse(BaseModel):
    """Response for import preview (dry run)."""

    valid: bool
    schemes: list[SchemePreviewResponse]
    total_concepts_count: int
    total_relationships_count: int
    classes: list[ClassPreviewResponse] = Field(default_factory=list)
    properties: list[PropertyPreviewResponse] = Field(default_factory=list)
    classes_count: int = 0
    properties_count: int = 0
    errors: list[str] = Field(default_factory=list)


class SchemeCreatedResponse(BaseModel):
    """Information about a created scheme."""

    id: UUID
    title: str
    concepts_created: int


class ClassCreatedResponse(BaseModel):
    """Information about a created OntologyClass."""

    id: UUID
    identifier: str
    label: str


class PropertyCreatedResponse(BaseModel):
    """Information about a created Property."""

    id: UUID
    identifier: str
    label: str
    range_scheme_id: UUID | None
    range_datatype: str | None
    range_class_id: UUID | None


class ImportResultResponse(BaseModel):
    """Response for actual import execution."""

    schemes_created: list[SchemeCreatedResponse]
    total_concepts_created: int
    total_relationships_created: int
    classes_created: list[ClassCreatedResponse] = Field(default_factory=list)
    properties_created: list[PropertyCreatedResponse] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
