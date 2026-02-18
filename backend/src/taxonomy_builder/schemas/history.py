"""Pydantic schemas for history API."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class ChangeEventRead(BaseModel):
    """Schema for reading a change event."""

    id: UUID
    timestamp: datetime
    entity_type: str
    entity_id: UUID
    project_id: UUID | None
    scheme_id: UUID | None
    action: str
    before_state: dict[str, Any] | None
    after_state: dict[str, Any] | None
    user_id: UUID | None
    user_display_name: str | None = None

    model_config = {"from_attributes": True}
