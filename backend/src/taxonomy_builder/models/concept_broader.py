"""ConceptBroader model for broader/narrower relationships."""

from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from taxonomy_builder.database import Base


class ConceptBroader(Base):
    """Join table for SKOS broader/narrower relationships between concepts."""

    __tablename__ = "concept_broader"

    concept_id: Mapped[UUID] = mapped_column(
        ForeignKey("concepts.id", ondelete="CASCADE"),
        primary_key=True,
    )
    broader_concept_id: Mapped[UUID] = mapped_column(
        ForeignKey("concepts.id", ondelete="CASCADE"),
        primary_key=True,
    )
