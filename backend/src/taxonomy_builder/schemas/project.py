"""Pydantic schemas for Project."""

import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProjectCreate(BaseModel):
    """Schema for creating a new project."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    namespace: str | None = None

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        """Strip whitespace from name."""
        return v.strip()

    @field_validator("namespace")
    @classmethod
    def validate_namespace_uri(cls, v: str | None) -> str | None:
        """Validate that namespace is a valid URI."""
        if v is None:
            return v

        # Basic URI validation: must start with http:// or https://
        uri_pattern = r"^https?://[^\s/$.?#].[^\s]*$"
        if not re.match(uri_pattern, v):
            raise ValueError("namespace must be a valid HTTP or HTTPS URI")

        return v


class ProjectUpdate(BaseModel):
    """Schema for updating an existing project."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    namespace: str | None = None

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str | None) -> str | None:
        """Strip whitespace from name if provided."""
        if v is not None:
            return v.strip()
        return v

    @field_validator("namespace")
    @classmethod
    def validate_namespace_uri(cls, v: str | None) -> str | None:
        """Validate that namespace is a valid URI."""
        if v is None:
            return v

        # Basic URI validation: must start with http:// or https://
        uri_pattern = r"^https?://[^\s/$.?#].[^\s]*$"
        if not re.match(uri_pattern, v):
            raise ValueError("namespace must be a valid HTTP or HTTPS URI")

        return v


class ProjectRead(BaseModel):
    """Schema for reading a project."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None
    namespace: str | None
    created_at: datetime
    updated_at: datetime
