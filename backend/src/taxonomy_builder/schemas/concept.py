"""Pydantic schemas for Concept."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ConceptCreate(BaseModel):
    """Schema for creating a new concept."""

    pref_label: str = Field(..., min_length=1, max_length=255)
    definition: str | None = None
    scope_note: str | None = None
    uri: str | None = Field(default=None, max_length=2048)

    @field_validator("pref_label")
    @classmethod
    def strip_pref_label(cls, v: str) -> str:
        """Strip whitespace from pref_label."""
        return v.strip()


class ConceptUpdate(BaseModel):
    """Schema for updating an existing concept."""

    pref_label: str | None = Field(default=None, min_length=1, max_length=255)
    definition: str | None = None
    scope_note: str | None = None
    uri: str | None = Field(default=None, max_length=2048)

    @field_validator("pref_label")
    @classmethod
    def strip_pref_label(cls, v: str | None) -> str | None:
        """Strip whitespace from pref_label if provided."""
        if v is not None:
            return v.strip()
        return v


class ConceptBrief(BaseModel):
    """Brief schema for a concept (used in relationships)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    scheme_id: UUID
    pref_label: str
    definition: str | None
    scope_note: str | None
    uri: str | None
    created_at: datetime
    updated_at: datetime


class ConceptRead(BaseModel):
    """Schema for reading a concept."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    scheme_id: UUID
    pref_label: str
    definition: str | None
    scope_note: str | None
    uri: str | None
    created_at: datetime
    updated_at: datetime
    broader: list[ConceptBrief] = []
