"""PublishedVersion model for immutable snapshots of concept schemes."""

from datetime import datetime
from uuid import UUID, uuid7

from sqlalchemy import ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from taxonomy_builder.database import Base


class PublishedVersion(Base):
    """Immutable snapshot of a concept scheme at a point in time."""

    __tablename__ = "published_versions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    scheme_id: Mapped[UUID] = mapped_column(
        ForeignKey("concept_schemes.id", ondelete="CASCADE"), nullable=False
    )
    version_label: Mapped[str] = mapped_column(String(50), nullable=False)
    published_at: Mapped[datetime] = mapped_column(default=datetime.now)
    snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_published_versions_scheme_id", "scheme_id"),
        UniqueConstraint("scheme_id", "version_label", name="uq_published_versions_scheme_label"),
    )
