"""Pydantic schemas for ontology classes."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from taxonomy_builder.models.class_restriction import RestrictionType
from taxonomy_builder.schemas.validators import validate_identifier

if TYPE_CHECKING:
    from taxonomy_builder.models.ontology_class import OntologyClass


class OntologyClassCreate(BaseModel):
    """Schema for creating a new ontology class."""

    identifier: str = Field(..., min_length=1, max_length=255)
    label: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    scope_note: str | None = None
    uri: str | None = Field(default=None, max_length=2048)

    @field_validator("identifier")
    @classmethod
    def check_identifier(cls, v: str) -> str:
        """Validate identifier is URI-safe."""
        result = validate_identifier(v)
        assert result is not None  # v is required (non-None)
        return result

    @field_validator("label")
    @classmethod
    def strip_label(cls, v: str) -> str:
        """Strip whitespace from label."""
        return v.strip()


class OntologyClassUpdate(BaseModel):
    """Schema for updating an existing ontology class."""

    identifier: str | None = Field(default=None, min_length=1, max_length=255)
    label: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    scope_note: str | None = None

    @field_validator("identifier")
    @classmethod
    def check_identifier(cls, v: str | None) -> str | None:
        """Validate identifier is URI-safe if provided."""
        return validate_identifier(v)

    @field_validator("label")
    @classmethod
    def strip_label(cls, v: str | None) -> str | None:
        """Strip whitespace from label if provided."""
        if v is not None:
            return v.strip()
        return v


class RestrictionRead(BaseModel):
    """Schema for reading an OWL restriction on an ontology class."""

    model_config = ConfigDict(from_attributes=True)

    on_property_uri: str
    restriction_type: RestrictionType
    value_uri: str


class OntologyClassRead(BaseModel):
    """Schema for reading an ontology class."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    identifier: str
    label: str
    description: str | None
    scope_note: str | None
    uri: str
    superclass_uris: list[str] = []
    subclass_uris: list[str] = []
    restrictions: list[RestrictionRead] = []
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_orm_model(cls, obj: OntologyClass) -> OntologyClassRead:
        """Build from ORM model, extracting relationship-derived fields.

        Must be called in an async context where relationships are loaded.
        """
        return cls(
            id=obj.id,
            project_id=obj.project_id,
            identifier=obj.identifier,
            label=obj.label,
            description=obj.description,
            scope_note=obj.scope_note,
            uri=obj.uri,
            superclass_uris=sorted(c.uri for c in obj.superclasses),
            subclass_uris=sorted(c.uri for c in obj.subclasses),
            restrictions=[
                RestrictionRead.model_validate(r, from_attributes=True)
                for r in obj.restrictions
            ],
            created_at=obj.created_at,
            updated_at=obj.updated_at,
        )
