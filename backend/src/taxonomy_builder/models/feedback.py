"""Feedback model for reader feedback on published entities."""

import enum
from datetime import datetime
from uuid import UUID, uuid7

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from taxonomy_builder.database import Base


class EntityType(str, enum.Enum):
    concept = "concept"
    scheme = "scheme"
    ontology_class = "class"
    property = "property"


class FeedbackStatus(str, enum.Enum):
    open = "open"
    responded = "responded"
    resolved = "resolved"
    declined = "declined"


# Valid feedback_type values per entity category
FEEDBACK_TYPES_CONCEPT_SCHEME = {
    "unclear_definition",
    "missing_term",
    "scope_question",
    "overlap_duplication",
    "general_comment",
}

FEEDBACK_TYPES_CLASS_PROPERTY = {
    "incorrect_modelling",
    "missing_relationship",
    "structural_question",
    "general_comment",
}

FEEDBACK_TYPES_BY_ENTITY = {
    EntityType.concept: FEEDBACK_TYPES_CONCEPT_SCHEME,
    EntityType.scheme: FEEDBACK_TYPES_CONCEPT_SCHEME,
    EntityType.ontology_class: FEEDBACK_TYPES_CLASS_PROPERTY,
    EntityType.property: FEEDBACK_TYPES_CLASS_PROPERTY,
}


class Feedback(Base):
    """Reader feedback on a published entity.

    Feedback references entities by their snapshot ID (not a FK — the entity
    lives inside the PublishedVersion JSONB). Supports soft delete via
    deleted_at.
    """

    __tablename__ = "feedback"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    project_id: Mapped[UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    snapshot_version: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(20), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(36), nullable=False)
    entity_label: Mapped[str] = mapped_column(String(500), nullable=False)
    feedback_type: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    author_name: Mapped[str] = mapped_column(String(255), nullable=False)
    author_email: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=FeedbackStatus.open.value
    )
    response_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    responded_by: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    responded_by_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    responded_at: Mapped[datetime | None] = mapped_column(nullable=True)
    # Status change tracking
    status_changed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    status_changed_by: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    deleted_at: Mapped[datetime | None] = mapped_column(nullable=True)

    def to_read_dict(self, *, can_delete: bool) -> dict:
        """Reader-facing response dict (no manager identity)."""
        response_dict = None
        if self.response_content:
            response_dict = {
                "author": "Vocabulary manager",
                "content": self.response_content,
                "created_at": self.responded_at,
            }
        return {
            "id": self.id,
            "project_id": self.project_id,
            "snapshot_version": self.snapshot_version,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "entity_label": self.entity_label,
            "feedback_type": self.feedback_type,
            "content": self.content,
            "status": self.status,
            "response": response_dict,
            "created_at": self.created_at,
            "can_delete": can_delete,
        }

    def to_manager_dict(self) -> dict:
        """Manager-facing response dict (includes author info)."""
        base = self.to_read_dict(can_delete=False)
        base["author_name"] = self.author_name
        base["responded_by_name"] = self.responded_by_name
        return base

    __table_args__ = (
        Index("ix_feedback_project_user", project_id, user_id, deleted_at),
        Index("ix_feedback_project_entity", project_id, entity_id, deleted_at),
        Index(
            "ix_feedback_project_status",
            project_id, deleted_at, status, created_at,
        ),
    )
