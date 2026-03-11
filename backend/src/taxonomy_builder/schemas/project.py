"""Pydantic schemas for Project."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


class ProjectCreate(BaseModel):
    """Schema for creating a new project."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    namespace: HttpUrl | None = None
    identifier_prefix: str | None = Field(default=None, max_length=4, pattern=r"^[A-Z]{1,4}$")

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        """Strip whitespace from name."""
        return v.strip()


class ProjectUpdate(BaseModel):
    """Schema for updating an existing project."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    namespace: HttpUrl | None = None
    identifier_prefix: str | None = Field(default=None, max_length=4, pattern=r"^[A-Z]{1,4}$")

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
    namespace: str | None
    identifier_prefix: str | None
    identifier_counter: int
    created_at: datetime
    updated_at: datetime
