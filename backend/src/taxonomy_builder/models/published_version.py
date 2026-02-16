"""PublishedVersion model for immutable project snapshots."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid7

from sqlalchemy import Boolean, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from taxonomy_builder.database import Base

if TYPE_CHECKING:
    from taxonomy_builder.models.project import Project


class PublishedVersion(Base):
    """A published (or draft) snapshot of a project's vocabulary."""

    __tablename__ = "published_versions"
    __table_args__ = (
        UniqueConstraint("project_id", "version", name="uq_published_version_per_project"),
        Index(
            "ix_one_draft_per_project",
            "project_id",
            unique=True,
            postgresql_where="NOT finalized",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    project_id: Mapped[UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    finalized: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    published_at: Mapped[datetime | None] = mapped_column(nullable=True)
    previous_version_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("published_versions.id", ondelete="SET NULL"), nullable=True
    )
    snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False)

    project: Mapped["Project"] = relationship(lazy="selectin")
    previous_version: Mapped["PublishedVersion | None"] = relationship(
        remote_side="PublishedVersion.id", lazy="selectin"
    )
