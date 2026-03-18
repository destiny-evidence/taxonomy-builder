"""Pydantic schemas for Property."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from taxonomy_builder.schemas.validators import validate_identifier

if TYPE_CHECKING:
    from taxonomy_builder.models.property import Property

_RANGE_FIELDS = ("range_scheme_id", "range_datatype", "range_class")


def _count_range_fields(model: BaseModel) -> int:
    """Count how many of the three range fields are set (non-None)."""
    return sum(getattr(model, f) is not None for f in _RANGE_FIELDS)


# Allowed XSD datatypes for range_datatype
ALLOWED_DATATYPES = frozenset([
    "xsd:string",
    "xsd:integer",
    "xsd:decimal",
    "xsd:boolean",
    "xsd:date",
    "xsd:dateTime",
    "xsd:anyURI",
])


class PropertyCreate(BaseModel):
    """Schema for creating a new property."""

    identifier: str = Field(..., min_length=1, max_length=255)
    label: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    domain_class_uris: list[str] = Field(..., min_length=1)
    range_scheme_id: UUID | None = None
    range_datatype: str | None = Field(default=None, max_length=50)
    range_class: str | None = Field(default=None, min_length=1, max_length=2048)
    cardinality: Literal["single", "multiple"]
    required: bool = False
    uri: str | None = Field(default=None, min_length=1, max_length=2048)

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

    @field_validator("range_datatype")
    @classmethod
    def validate_datatype(cls, v: str | None) -> str | None:
        """Validate that datatype is from allowed list."""
        if v is not None and v not in ALLOWED_DATATYPES:
            allowed = ", ".join(sorted(ALLOWED_DATATYPES))
            raise ValueError(f"range_datatype must be one of: {allowed}")
        return v

    @model_validator(mode="after")
    def check_exactly_one_range(self) -> "PropertyCreate":  # noqa: UP037
        """Enforce exactly one of range_scheme_id, range_datatype, or range_class."""
        if _count_range_fields(self) != 1:
            raise ValueError(
                "Exactly one of range_scheme_id, range_datatype, or range_class "
                "must be provided"
            )
        return self


class PropertyUpdate(BaseModel):
    """Schema for updating an existing property."""

    identifier: str | None = Field(default=None, min_length=1, max_length=255)
    label: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    domain_class_uris: list[str] | None = Field(default=None, min_length=1)
    range_scheme_id: UUID | None = None
    range_datatype: str | None = Field(default=None, max_length=50)
    range_class: str | None = Field(default=None, min_length=1, max_length=2048)
    cardinality: Literal["single", "multiple"] | None = None
    required: bool | None = None

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

    @field_validator("range_datatype")
    @classmethod
    def validate_datatype(cls, v: str | None) -> str | None:
        """Validate that datatype is from allowed list."""
        if v is not None and v not in ALLOWED_DATATYPES:
            allowed = ", ".join(sorted(ALLOWED_DATATYPES))
            raise ValueError(f"range_datatype must be one of: {allowed}")
        return v

    @model_validator(mode="after")
    def check_at_most_one_range(self) -> "PropertyUpdate":  # noqa: UP037
        """Reject updates that set multiple range fields simultaneously."""
        if _count_range_fields(self) > 1:
            raise ValueError(
                "At most one of range_scheme_id, range_datatype, or range_class "
                "may be set in a single update"
            )
        return self


class ConceptSchemeBrief(BaseModel):
    """Brief schema info for nested property responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    uri: str | None


class PropertyRead(BaseModel):
    """Schema for reading a property."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    identifier: str
    label: str
    description: str | None
    domain_class_uris: list[str] = []
    property_type: str
    range_scheme_id: UUID | None
    range_scheme: ConceptSchemeBrief | None
    range_datatype: str | None
    range_class: str | None
    cardinality: str
    required: bool
    uri: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_orm_model(cls, obj: Property) -> PropertyRead:
        """Build from ORM model, extracting relationship-derived fields."""
        return cls(
            id=obj.id,
            project_id=obj.project_id,
            identifier=obj.identifier,
            label=obj.label,
            description=obj.description,
            domain_class_uris=sorted(c.uri for c in obj.domain_classes),
            property_type=obj.property_type,
            range_scheme_id=obj.range_scheme_id,
            range_scheme=(
                ConceptSchemeBrief.model_validate(obj.range_scheme, from_attributes=True)
                if obj.range_scheme
                else None
            ),
            range_datatype=obj.range_datatype,
            range_class=obj.range_class,
            cardinality=obj.cardinality,
            required=obj.required,
            uri=obj.uri,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
        )
