"""Pydantic schemas for Concept."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ConceptCreate(BaseModel):
    """Schema for creating a new concept."""

    pref_label: str = Field(..., min_length=1, max_length=255)
    identifier: str | None = Field(default=None, max_length=255)
    definition: str | None = None
    scope_note: str | None = None
    alt_labels: list[str] = Field(default_factory=list)

    @field_validator("pref_label")
    @classmethod
    def strip_pref_label(cls, v: str) -> str:
        """Strip whitespace from pref_label."""
        return v.strip()

    @field_validator("identifier")
    @classmethod
    def strip_identifier(cls, v: str | None) -> str | None:
        """Strip whitespace from identifier if provided."""
        if v is not None:
            return v.strip() or None
        return v

    @field_validator("alt_labels")
    @classmethod
    def clean_alt_labels(cls, v: list[str]) -> list[str]:
        """Strip whitespace, remove empty strings, remove case-insensitive duplicates."""
        seen_lower: set[str] = set()
        result: list[str] = []
        for label in v:
            stripped = label.strip()
            if stripped and stripped.lower() not in seen_lower:
                result.append(stripped)
                seen_lower.add(stripped.lower())
        return result


class ConceptUpdate(BaseModel):
    """Schema for updating an existing concept."""

    pref_label: str | None = Field(default=None, min_length=1, max_length=255)
    identifier: str | None = Field(default=None, max_length=255)
    definition: str | None = None
    scope_note: str | None = None
    alt_labels: list[str] | None = None  # None = no change, [] = clear all

    @field_validator("pref_label")
    @classmethod
    def strip_pref_label(cls, v: str | None) -> str | None:
        """Strip whitespace from pref_label if provided."""
        if v is not None:
            return v.strip()
        return v

    @field_validator("identifier")
    @classmethod
    def strip_identifier(cls, v: str | None) -> str | None:
        """Strip whitespace from identifier if provided."""
        if v is not None:
            return v.strip() or None
        return v

    @field_validator("alt_labels")
    @classmethod
    def clean_alt_labels(cls, v: list[str] | None) -> list[str] | None:
        """Strip whitespace, remove empty strings, remove duplicates if provided."""
        if v is None:
            return None
        seen_lower: set[str] = set()
        result: list[str] = []
        for label in v:
            stripped = label.strip()
            if stripped and stripped.lower() not in seen_lower:
                result.append(stripped)
                seen_lower.add(stripped.lower())
        return result


class ConceptBrief(BaseModel):
    """Brief schema for a concept (used in relationships)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    scheme_id: UUID
    identifier: str | None
    pref_label: str
    definition: str | None
    scope_note: str | None
    uri: str | None  # Computed from scheme.uri + identifier
    alt_labels: list[str] = []
    created_at: datetime
    updated_at: datetime


class ConceptRead(BaseModel):
    """Schema for reading a concept."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    scheme_id: UUID
    identifier: str | None
    pref_label: str
    definition: str | None
    scope_note: str | None
    uri: str | None  # Computed from scheme.uri + identifier
    alt_labels: list[str] = []
    created_at: datetime
    updated_at: datetime
    broader: list[ConceptBrief] = []
