"""Ontology class model for representing classes in a lightweight ontology."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid7

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from taxonomy_builder.database import Base

if TYPE_CHECKING:
    from taxonomy_builder.models.project import Project


class OntologyClass(Base):
    """An ontology class within a project.

    Classes represent domain entities (like Reference, Outcome) that
    properties attach to via their domain_class URI.
    """

    __tablename__ = "ontology_classes"
    __table_args__ = (
        UniqueConstraint(
            "project_id", "identifier", name="uq_ontology_class_identifier_per_project"
        ),
        UniqueConstraint("project_id", "uri", name="uq_ontology_classes_project_uri"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    project_id: Mapped[UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    identifier: Mapped[str] = mapped_column(String(255), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    scope_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    uri: Mapped[str] = mapped_column(String(2048), nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.now, onupdate=datetime.now)

    # Relationships
    project: Mapped["Project"] = relationship(
        back_populates="ontology_classes", lazy="selectin"
    )

