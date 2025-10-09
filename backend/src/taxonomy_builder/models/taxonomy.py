"""Taxonomy domain models."""

import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TaxonomyCreate(BaseModel):
    """Model for creating a new taxonomy."""

    id: str = Field(..., description="Unique identifier (slug format)")
    name: str = Field(..., description="Human-readable name")
    uri_prefix: str = Field(..., description="URI prefix for concepts in this taxonomy")
    description: str | None = Field(None, description="Optional description")

    @field_validator("id")
    @classmethod
    def validate_id_format(cls, v: str) -> str:
        """Validate that ID is a valid slug (lowercase, hyphens, numbers)."""
        if not v:
            raise ValueError("ID cannot be empty")
        if not re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", v):
            raise ValueError(
                "Invalid ID format: must be lowercase letters, numbers, and hyphens only"
            )
        return v

    @field_validator("uri_prefix")
    @classmethod
    def validate_uri_prefix(cls, v: str) -> str:
        """Validate that URI prefix is a valid URI."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("Invalid URI prefix: must start with http:// or https://")
        return v


class Taxonomy(BaseModel):
    """Taxonomy domain model."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    uri_prefix: str
    description: str | None = None
    created_at: datetime
