"""Concept model."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid7

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from taxonomy_builder.database import Base

if TYPE_CHECKING:
    from taxonomy_builder.models.concept_scheme import ConceptScheme


class Concept(Base):
    """A SKOS concept within a concept scheme."""

    __tablename__ = "concepts"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    scheme_id: Mapped[UUID] = mapped_column(ForeignKey("concept_schemes.id", ondelete="CASCADE"))
    uri: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    pref_label: Mapped[str] = mapped_column(String(255), nullable=False)
    definition: Mapped[str | None] = mapped_column(Text, nullable=True)
    scope_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.now, onupdate=datetime.now)

    scheme: Mapped["ConceptScheme"] = relationship(back_populates="concepts")

    # SKOS broader/narrower relationships (many-to-many via concept_broader)
    broader: Mapped[list["Concept"]] = relationship(
        secondary="concept_broader",
        primaryjoin="Concept.id == concept_broader.c.concept_id",
        secondaryjoin="Concept.id == concept_broader.c.broader_concept_id",
        lazy="selectin",
    )
    narrower: Mapped[list["Concept"]] = relationship(
        secondary="concept_broader",
        primaryjoin="Concept.id == concept_broader.c.broader_concept_id",
        secondaryjoin="Concept.id == concept_broader.c.concept_id",
        lazy="selectin",
        viewonly=True,
    )
