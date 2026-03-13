"""Project model."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid7

from sqlalchemy import CheckConstraint, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from taxonomy_builder.database import Base, UrlString

if TYPE_CHECKING:
    from taxonomy_builder.models.concept_scheme import ConceptScheme
    from taxonomy_builder.models.ontology_class import OntologyClass
    from taxonomy_builder.models.property import Property


class Project(Base):
    """A project that groups related concept schemes."""

    __tablename__ = "projects"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    namespace: Mapped[str] = mapped_column(UrlString(), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.now, onupdate=datetime.now)

    identifier_prefix: Mapped[str | None] = mapped_column(String(4), nullable=True)
    identifier_counter: Mapped[int] = mapped_column(default=0, server_default="0")

    __table_args__ = (
        CheckConstraint(
            r"identifier_prefix ~ '^[A-Z]{1,4}$' OR identifier_prefix IS NULL",
            name="ck_projects_identifier_prefix_format",
        ),
        CheckConstraint(
            "identifier_counter >= 0",
            name="ck_projects_identifier_counter_non_negative",
        ),
    )

    schemes: Mapped[list[ConceptScheme]] = relationship(
        back_populates="project", cascade="all, delete-orphan", lazy="selectin"
    )
    properties: Mapped[list[Property]] = relationship(
        back_populates="project", cascade="all, delete-orphan", lazy="selectin"
    )
    ontology_classes: Mapped[list[OntologyClass]] = relationship(
        back_populates="project", cascade="all, delete-orphan", lazy="selectin"
    )
