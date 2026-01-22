"""ChangeEvent model for tracking all changes."""

from datetime import datetime
from uuid import UUID, uuid7

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from taxonomy_builder.database import Base


class ChangeEvent(Base):
    """Immutable log of all changes to schemes and concepts."""

    __tablename__ = "change_events"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    timestamp: Mapped[datetime] = mapped_column(default=datetime.now)
    user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # What changed
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[UUID] = mapped_column(nullable=False)
    scheme_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("concept_schemes.id", ondelete="SET NULL"), nullable=True
    )

    # Type of change
    action: Mapped[str] = mapped_column(String(20), nullable=False)

    # State
    before_state: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    after_state: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        Index("ix_change_events_scheme_timestamp", "scheme_id", timestamp.desc()),
        Index(
            "ix_change_events_entity",
            "entity_type",
            "entity_id",
            timestamp.desc(),
        ),
    )
