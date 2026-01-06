"""ConceptRelated model for symmetric related relationships."""

from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from taxonomy_builder.database import Base


class ConceptRelated(Base):
    """Join table for SKOS related relationships between concepts.

    This represents a symmetric relationship - if A is related to B, then B is
    related to A. To enforce this and prevent duplicates, we store only one
    direction with concept_id < related_concept_id.
    """

    __tablename__ = "concept_related"

    concept_id: Mapped[UUID] = mapped_column(
        ForeignKey("concepts.id", ondelete="CASCADE"),
        primary_key=True,
    )
    related_concept_id: Mapped[UUID] = mapped_column(
        ForeignKey("concepts.id", ondelete="CASCADE"),
        primary_key=True,
    )
