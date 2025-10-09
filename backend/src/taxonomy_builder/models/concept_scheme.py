"""ConceptScheme domain models."""

import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ConceptSchemeCreate(BaseModel):
    """Model for creating a new concept scheme."""

    id: str = Field(..., description="Unique identifier (slug format)")
    name: str = Field(..., description="Human-readable name")
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


class ConceptSchemeUpdate(BaseModel):
    """Model for updating a concept scheme. All fields are optional."""

    name: str | None = Field(None, description="Human-readable name")
    description: str | None = Field(None, description="Optional description")


class ConceptScheme(BaseModel):
    """ConceptScheme domain model."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    taxonomy_id: str
    name: str
    uri: str
    description: str | None = None
    created_at: datetime
