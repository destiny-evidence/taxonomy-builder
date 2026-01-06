"""Pydantic schemas for Project."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProjectCreate(BaseModel):
    """Schema for creating a new project."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        """Strip whitespace from name."""
        return v.strip()


class ProjectUpdate(BaseModel):
    """Schema for updating an existing project."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str | None) -> str | None:
        """Strip whitespace from name if provided."""
        if v is not None:
            return v.strip()
        return v


class ProjectRead(BaseModel):
    """Schema for reading a project."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime
