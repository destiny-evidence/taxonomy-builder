"""PublishedVersion model for immutable project snapshots."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid7

from sqlalchemy import (
    Boolean,
    Computed,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    select,
    true,
)
from sqlalchemy.dialects.postgresql import ARRAY as PG_ARRAY
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, column_property, mapped_column, relationship

from taxonomy_builder.database import Base

if TYPE_CHECKING:
    from taxonomy_builder.models.project import Project


class PublishedVersion(Base):
    """A published snapshot of a project's vocabulary (release or pre-release)."""

    __tablename__ = "published_versions"
    __table_args__ = (
        UniqueConstraint(
            "project_id", "version", name="uq_published_version_per_project"
        ),
        Index(
            "ix_latest_version_lookup",
            "project_id",
            "version_sort_key",
            postgresql_where="finalized",
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
    publisher: Mapped[str | None] = mapped_column(String(255), nullable=True)
    snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False)
    version_sort_key: Mapped[list[int]] = mapped_column(
        PG_ARRAY(Integer),
        Computed(
            "CASE WHEN version LIKE '%%-pre%%' THEN"
            " string_to_array(split_part(version, '-pre', 1), '.')::int[]"
            " || ARRAY[split_part(version, '-pre', 2)::int]"
            " ELSE"
            " string_to_array(version, '.')::int[] || ARRAY[2147483647]"
            " END",
            persisted=True,
        ),
    )

    project: Mapped["Project"] = relationship(lazy="selectin")
    previous_version: Mapped["PublishedVersion | None"] = relationship(
        remote_side="PublishedVersion.id", lazy="selectin"
    )

    @classmethod
    def __declare_last__(cls) -> None:
        pv = cls.__table__.alias("pv_max")
        max_key = (
            select(func.max(pv.c.version_sort_key))
            .where(pv.c.project_id == cls.project_id, pv.c.finalized == true())
            .correlate(cls)
            .scalar_subquery()
        )
        cls.latest = column_property(
            func.coalesce(cls.version_sort_key == max_key, False)
        )
