"""ClassSuperclass model for rdfs:subClassOf relationships between ontology classes."""

from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from taxonomy_builder.database import Base


class ClassSuperclass(Base):
    """Join table for rdfs:subClassOf relationships between ontology classes."""

    __tablename__ = "class_superclass"

    class_id: Mapped[UUID] = mapped_column(
        ForeignKey("ontology_classes.id", ondelete="CASCADE"),
        primary_key=True,
    )
    superclass_id: Mapped[UUID] = mapped_column(
        ForeignKey("ontology_classes.id", ondelete="CASCADE"),
        primary_key=True,
    )
