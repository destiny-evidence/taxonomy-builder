"""PropertyDomainClass model for multi-domain property relationships."""

from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from taxonomy_builder.database import Base


class PropertyDomainClass(Base):
    """Join table linking properties to their domain classes."""

    __tablename__ = "property_domain_class"

    property_id: Mapped[UUID] = mapped_column(
        ForeignKey("properties.id", ondelete="CASCADE"),
        primary_key=True,
    )
    class_id: Mapped[UUID] = mapped_column(
        ForeignKey("ontology_classes.id", ondelete="CASCADE"),
        primary_key=True,
    )
