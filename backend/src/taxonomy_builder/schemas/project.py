"""Pydantic schemas for Project."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

from taxonomy_builder.schemas.validators import UpdateSchema


class ProjectCreate(BaseModel):
    """Schema for creating a new project."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    namespace: HttpUrl
    identifier_prefix: str = Field(..., max_length=4, pattern=r"^[A-Z]{1,4}$")

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        """Strip whitespace from name."""
        return v.strip()

    @field_validator("namespace")
    @classmethod
    def reject_trailing_hash(cls, v: HttpUrl) -> HttpUrl:
        """Reject namespaces ending in '#'."""
        if str(v).endswith("#"):
            raise ValueError("namespace cannot end with '#'")
        return v


class ProjectUpdate(UpdateSchema):
    """Schema for updating an existing project."""

    non_nullable = frozenset({"name", "identifier_prefix"})

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
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
    namespace: str
    namespace_prefixes: dict[str, str] = Field(default_factory=dict)
    identifier_prefix: str
    identifier_counter: int
    prefix_locked: bool
    created_at: datetime
    updated_at: datetime
