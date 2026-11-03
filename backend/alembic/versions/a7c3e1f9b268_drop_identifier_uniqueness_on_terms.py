"""drop identifier uniqueness on properties and classes

Revision ID: a7c3e1f9b268
Revises: c9909d9448ce
Create Date: 2026-11-03 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a7c3e1f9b268'
down_revision: Union[str, Sequence[str], None] = 'c9909d9448ce'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Allow terms from different vocabularies to share a local name.

    URI uniqueness (uq_properties_project_uri, uq_ontology_classes_project_uri)
    remains the identity constraint.
    """
    op.drop_constraint('uq_property_identifier_per_project', 'properties', type_='unique')
    op.drop_constraint(
        'uq_ontology_class_identifier_per_project', 'ontology_classes', type_='unique'
    )


def downgrade() -> None:
    """Fails if any project now holds two terms with the same identifier."""
    op.create_unique_constraint(
        'uq_ontology_class_identifier_per_project',
        'ontology_classes',
        ['project_id', 'identifier'],
    )
    op.create_unique_constraint(
        'uq_property_identifier_per_project', 'properties', ['project_id', 'identifier']
    )
