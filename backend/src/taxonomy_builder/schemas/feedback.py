"""Pydantic schemas for Feedback."""

from datetime import datetime
from typing import Self
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from taxonomy_builder.models.feedback import (
    FEEDBACK_TYPES_BY_ENTITY,
    EntityType,
    FeedbackStatus,
)


class FeedbackCreate(BaseModel):
    """Schema for creating feedback."""

    snapshot_version: str
    entity_type: EntityType
    entity_id: str
    entity_label: str = Field(max_length=500)
    feedback_type: str = Field(max_length=100)
    content: str = Field(min_length=1, max_length=10000)

    @field_validator("content")
    @classmethod
    def strip_and_validate_content(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Content cannot be empty or whitespace only")
        return stripped

    @model_validator(mode="after")
    def validate_feedback_type_for_entity(self) -> Self:
        valid_types = FEEDBACK_TYPES_BY_ENTITY.get(self.entity_type)
        if valid_types and self.feedback_type not in valid_types:
            raise ValueError(
                f"feedback_type '{self.feedback_type}' is not valid "
                f"for entity_type '{self.entity_type.value}'"
            )
        return self


class FeedbackResponse(BaseModel):
    """Nested response info shown to readers (no manager identity)."""

    content: str
    created_at: datetime


class FeedbackRead(BaseModel):
    """Schema for reading feedback (reader-facing)."""

    id: UUID
    project_id: UUID
    snapshot_version: str
    entity_type: str
    entity_id: str
    entity_label: str
    feedback_type: str
    content: str
    status: FeedbackStatus
    response: FeedbackResponse | None = None
    created_at: datetime
    can_delete: bool = False


class FeedbackManagerRead(FeedbackRead):
    """Schema for reading feedback (manager-facing, includes author info)."""

    author_name: str
    responded_by_name: str | None = None


class RespondRequest(BaseModel):
    """Body for POST /respond."""

    content: str = Field(min_length=1, max_length=10000)

    @field_validator("content")
    @classmethod
    def strip_and_validate(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Response content cannot be empty or whitespace only")
        return stripped


class TriageRequest(BaseModel):
    """Body for POST /resolve and POST /decline."""

    content: str | None = Field(default=None, max_length=10000)
