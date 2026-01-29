"""Pydantic schemas for Comment."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CommentCreate(BaseModel):
    """Schema for creating a new comment."""

    content: str = Field(..., min_length=1, max_length=10000)

    @field_validator("content")
    @classmethod
    def strip_content(cls, v: str) -> str:
        """Strip whitespace from content."""
        return v.strip()


class CommentAuthor(BaseModel):
    """Schema for comment author info."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    display_name: str


class CommentRead(BaseModel):
    """Schema for reading a comment."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    concept_id: UUID
    user_id: UUID
    content: str
    created_at: datetime
    updated_at: datetime
    user: CommentAuthor
    can_delete: bool = False  # Computed at API layer
