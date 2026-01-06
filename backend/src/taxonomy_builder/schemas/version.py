"""Schemas for published versions."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class PublishedVersionCreate(BaseModel):
    """Schema for creating a published version."""

    version_label: str
    notes: str | None = None


class PublishedVersionRead(BaseModel):
    """Schema for reading a published version."""

    id: UUID
    scheme_id: UUID
    version_label: str
    published_at: datetime
    snapshot: dict[str, Any]
    notes: str | None

    model_config = {"from_attributes": True}
