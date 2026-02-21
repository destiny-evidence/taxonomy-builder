"""add uri column to ontology_classes and properties

Revision ID: 4837a613b04f
Revises: 22b9882fd86b
Create Date: 2026-02-21 19:26:49.306507

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4837a613b04f'
down_revision: Union[str, Sequence[str], None] = '22b9882fd86b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add uri column to ontology_classes and properties tables.

    Strategy: add as nullable, backfill from project namespace, set NOT NULL,
    add unique constraints.
    """
    # Add nullable columns first
    op.add_column('ontology_classes', sa.Column('uri', sa.String(2048), nullable=True))
    op.add_column('properties', sa.Column('uri', sa.String(2048), nullable=True))

    # Backfill URIs from project namespace + identifier
    op.execute("""
        UPDATE ontology_classes oc
        SET uri = RTRIM(p.namespace, '/') || '/' || oc.identifier
        FROM projects p
        WHERE oc.project_id = p.id AND p.namespace IS NOT NULL
    """)
    # Fallback for rows where project has no namespace
    op.execute("""
        UPDATE ontology_classes
        SET uri = 'urn:taxonomy:class:' || id::text
        WHERE uri IS NULL
    """)
    op.execute("""
        UPDATE properties pr
        SET uri = RTRIM(p.namespace, '/') || '/' || pr.identifier
        FROM projects p
        WHERE pr.project_id = p.id AND p.namespace IS NOT NULL
    """)
    # Fallback for rows where project has no namespace
    op.execute("""
        UPDATE properties
        SET uri = 'urn:taxonomy:property:' || id::text
        WHERE uri IS NULL
    """)

    # Set NOT NULL after backfill
    op.alter_column('ontology_classes', 'uri', nullable=False)
    op.alter_column('properties', 'uri', nullable=False)

    # Add composite unique constraints
    op.create_unique_constraint(
        'uq_ontology_classes_project_uri', 'ontology_classes', ['project_id', 'uri']
    )
    op.create_unique_constraint(
        'uq_properties_project_uri', 'properties', ['project_id', 'uri']
    )


def downgrade() -> None:
    """Remove uri column from ontology_classes and properties."""
    op.drop_constraint('uq_properties_project_uri', 'properties')
    op.drop_constraint('uq_ontology_classes_project_uri', 'ontology_classes')
    op.drop_column('properties', 'uri')
    op.drop_column('ontology_classes', 'uri')
