"""Pydantic schemas for Property."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from taxonomy_builder.schemas.validators import validate_identifier

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
    domain_class: str | None = Field(
        default=None, min_length=1, max_length=2048
    )
    range_scheme_id: UUID | None = None
    range_datatype: str | None = Field(default=None, max_length=50)
    range_class: str | None = Field(
        default=None, min_length=1, max_length=2048
    )
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
        """Enforce exactly one of range_scheme_id, range_datatype, range_class."""
        set_count = sum(
            x is not None
            for x in (self.range_scheme_id, self.range_datatype, self.range_class)
        )
        if set_count == 0:
            raise ValueError(
                "Exactly one of range_scheme_id, range_datatype, or range_class must be provided"
            )
        if set_count > 1:
            raise ValueError(
                "Exactly one of range_scheme_id, range_datatype,"
                " or range_class must be provided, not multiple"
            )
        return self


class PropertyUpdate(BaseModel):
    """Schema for updating an existing property."""

    identifier: str | None = Field(default=None, min_length=1, max_length=255)
    label: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    domain_class: str | None = Field(
        default=None, min_length=1, max_length=2048
    )
    range_scheme_id: UUID | None = None
    range_datatype: str | None = Field(default=None, max_length=50)
    range_class: str | None = Field(
        default=None, min_length=1, max_length=2048
    )
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
    domain_class: str | None
    range_scheme_id: UUID | None
    range_scheme: ConceptSchemeBrief | None
    range_datatype: str | None
    range_class: str | None
    cardinality: str
    required: bool
    uri: str
    created_at: datetime
    updated_at: datetime
