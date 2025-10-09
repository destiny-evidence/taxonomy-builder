"""Concept domain models."""

import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ConceptCreate(BaseModel):
    """Model for creating a new concept."""

    id: str = Field(..., description="Unique identifier (slug format)")
    pref_label: str = Field(
        ..., min_length=1, description="Preferred label (SKOS prefLabel)"
    )
    definition: str | None = Field(None, description="Optional definition (SKOS definition)")
    alt_labels: list[str] | None = Field(
        None, description="Optional alternative labels (SKOS altLabel)"
    )

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


class ConceptUpdate(BaseModel):
    """Model for updating a concept. All fields are optional."""

    pref_label: str | None = Field(None, description="Preferred label (SKOS prefLabel)")
    definition: str | None = Field(None, description="Optional definition (SKOS definition)")
    alt_labels: list[str] | None = Field(
        None, description="Optional alternative labels (SKOS altLabel)"
    )


class Concept(BaseModel):
    """Concept domain model."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    scheme_id: str
    uri: str
    pref_label: str
    definition: str | None = None
    alt_labels: list[str] | None = None
    broader_ids: list[str] = Field(default_factory=list)
    narrower_ids: list[str] = Field(default_factory=list)
    created_at: datetime
