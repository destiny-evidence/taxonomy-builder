"""Pydantic schemas for ConceptScheme."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ConceptSchemeCreate(BaseModel):
    """Schema for creating a new concept scheme."""

    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    uri: str | None = Field(default=None, max_length=2048)

    @field_validator("title")
    @classmethod
    def strip_title(cls, v: str) -> str:
        """Strip whitespace from title."""
        return v.strip()


class ConceptSchemeUpdate(BaseModel):
    """Schema for updating an existing concept scheme."""

    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    uri: str | None = Field(default=None, max_length=2048)

    @field_validator("title")
    @classmethod
    def strip_title(cls, v: str | None) -> str | None:
        """Strip whitespace from title if provided."""
        if v is not None:
            return v.strip()
        return v


class ConceptSchemeRead(BaseModel):
    """Schema for reading a concept scheme."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    title: str
    description: str | None
    uri: str | None
    created_at: datetime
    updated_at: datetime
