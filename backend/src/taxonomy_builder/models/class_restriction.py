"""ClassRestriction model for OWL restriction pass-through."""

from uuid import UUID, uuid7

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from taxonomy_builder.database import Base


class ClassRestriction(Base):
    """Structured pass-through for OWL restrictions on ontology classes.

    Stores allValuesFrom (and potentially other) restrictions that appear as
    anonymous rdfs:subClassOf superclasses in the source ontology.
    """

    __tablename__ = "class_restrictions"
    __table_args__ = (
        UniqueConstraint(
            "class_id",
            "on_property_uri",
            "restriction_type",
            "value_uri",
            name="uq_class_restriction",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    class_id: Mapped[UUID] = mapped_column(
        ForeignKey("ontology_classes.id", ondelete="CASCADE"),
        nullable=False,
    )
    on_property_uri: Mapped[str] = mapped_column(String(2048), nullable=False)
    restriction_type: Mapped[str] = mapped_column(String(50), nullable=False)
    value_uri: Mapped[str] = mapped_column(String(2048), nullable=False)
