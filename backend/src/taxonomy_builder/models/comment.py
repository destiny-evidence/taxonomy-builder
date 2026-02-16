"""Comment model for concept comments."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid7

from sqlalchemy import ForeignKey, Index, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from taxonomy_builder.database import Base

if TYPE_CHECKING:
    from taxonomy_builder.models.user import User


class Comment(Base):
    """A comment on a concept.

    Comments support soft delete via deleted_at timestamp to preserve history.
    """

    __tablename__ = "comments"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    concept_id: Mapped[UUID] = mapped_column(
        ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    parent_comment_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("comments.id", ondelete="CASCADE"), nullable=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.now, onupdate=datetime.now
    )
    deleted_at: Mapped[datetime | None] = mapped_column(nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(nullable=True)
    resolved_by: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    user: Mapped["User"] = relationship(
        foreign_keys=[user_id], lazy="selectin"
    )

    __table_args__ = (
        Index("ix_comments_concept_deleted", concept_id, deleted_at),
        Index("ix_comments_parent_comment_id", parent_comment_id, unique=False)
    )
