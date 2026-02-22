"""Property model for linking domain classes to concept schemes or datatypes."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid7

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from taxonomy_builder.database import Base, UrlString

if TYPE_CHECKING:
    from taxonomy_builder.models.concept_scheme import ConceptScheme
    from taxonomy_builder.models.project import Project


class Property(Base):
    """A property linking a domain class to a concept scheme or datatype.

    Properties define how entities (like Finding, Investigation) can be
    annotated with values from concept schemes or primitive datatypes.
    """

    __tablename__ = "properties"
    __table_args__ = (
        UniqueConstraint("project_id", "identifier", name="uq_property_identifier_per_project"),
        UniqueConstraint("project_id", "uri", name="uq_properties_project_uri"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    project_id: Mapped[UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    identifier: Mapped[str] = mapped_column(String(255), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Domain: the ontology class this property applies to
    domain_class: Mapped[str] = mapped_column(UrlString(), nullable=False)

    # Range: a concept scheme, a datatype, or an ontology class
    range_scheme_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("concept_schemes.id", ondelete="RESTRICT"), nullable=True
    )
    range_datatype: Mapped[str | None] = mapped_column(String(50), nullable=True)
    range_class: Mapped[str | None] = mapped_column(UrlString(), nullable=True)

    # Cardinality and optionality
    cardinality: Mapped[str] = mapped_column(String(20), nullable=False)  # 'single' or 'multiple'
    required: Mapped[bool] = mapped_column(default=False)
    uri: Mapped[str] = mapped_column(String(2048), nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.now, onupdate=datetime.now)

    # Relationships
    project: Mapped["Project"] = relationship(back_populates="properties", lazy="selectin")
    range_scheme: Mapped["ConceptScheme | None"] = relationship(lazy="selectin")
