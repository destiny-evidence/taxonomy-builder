"""ConceptScheme model."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid7

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from taxonomy_builder.database import Base

if TYPE_CHECKING:
    from taxonomy_builder.models.concept import Concept
    from taxonomy_builder.models.project import Project


class ConceptScheme(Base):
    """A SKOS concept scheme within a project."""

    __tablename__ = "concept_schemes"
    __table_args__ = (UniqueConstraint("project_id", "title", name="uq_scheme_title_per_project"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    uri: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.now, onupdate=datetime.now)

    project: Mapped["Project"] = relationship(back_populates="schemes")
    concepts: Mapped[list["Concept"]] = relationship(
        back_populates="scheme", cascade="all, delete-orphan", lazy="selectin"
    )
