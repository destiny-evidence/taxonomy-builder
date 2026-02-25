"""Feedback model for reader feedback on published entities."""

import enum
from datetime import datetime
from uuid import UUID, uuid7

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
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
    response: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    deleted_at: Mapped[datetime | None] = mapped_column(nullable=True)

    __table_args__ = (
        Index("ix_feedback_project_user", project_id, user_id, deleted_at),
        Index("ix_feedback_project_entity", project_id, entity_id, deleted_at),
    )
