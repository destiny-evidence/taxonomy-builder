"""Pydantic schemas for Comment."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CommentCreate(BaseModel):
    """Schema for creating a new comment."""

    content: str = Field(..., min_length=1, max_length=10000)
    parent_comment_id: UUID | None = None

    @field_validator("content")
    @classmethod
    def strip_and_validate_content(cls, v: str) -> str:
        """Strip whitespace and validate non-empty."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("Content cannot be empty or whitespace only")
        return stripped


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
    parent_comment_id: UUID | None
    content: str
    created_at: datetime
    updated_at: datetime
    user: CommentAuthor
    can_delete: bool = False  # Computed at API layer
