"""Pydantic schemas for Project."""

import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

PREFIX_PATTERN = re.compile(r"^[A-Z]{1,4}$")


def _validate_identifier_prefix(v: str | None) -> str | None:
    """Validate that identifier_prefix is 1-4 uppercase ASCII letters or None."""
    if v is not None and not PREFIX_PATTERN.match(v):
        msg = "identifier_prefix must be 1-4 uppercase ASCII letters"
        raise ValueError(msg)
    return v


class ProjectCreate(BaseModel):
    """Schema for creating a new project."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    namespace: HttpUrl | None = None
    identifier_prefix: str | None = Field(default=None, max_length=4)

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        """Strip whitespace from name."""
        return v.strip()

    @field_validator("identifier_prefix")
    @classmethod
    def validate_prefix(cls, v: str | None) -> str | None:
        """Validate identifier prefix format."""
        return _validate_identifier_prefix(v)


class ProjectUpdate(BaseModel):
    """Schema for updating an existing project."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    namespace: HttpUrl | None = None
    identifier_prefix: str | None = Field(default=None, max_length=4)

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str | None) -> str | None:
        """Strip whitespace from name if provided."""
        if v is not None:
            return v.strip()
        return v

    @field_validator("identifier_prefix")
    @classmethod
    def validate_prefix(cls, v: str | None) -> str | None:
        """Validate identifier prefix format."""
        return _validate_identifier_prefix(v)


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
