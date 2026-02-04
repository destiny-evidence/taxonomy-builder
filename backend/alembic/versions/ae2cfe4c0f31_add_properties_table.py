"""add_properties_table

Revision ID: ae2cfe4c0f31
Revises: 505552e0c1e1
Create Date: 2026-02-04 17:36:43.333546

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'ae2cfe4c0f31'
down_revision: Union[str, Sequence[str], None] = '505552e0c1e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the properties table."""
    op.create_table(
        'properties',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('project_id', sa.Uuid(), nullable=False),
        sa.Column('identifier', sa.String(length=255), nullable=False),
        sa.Column('label', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('domain_class', sa.String(length=2048), nullable=False),
        sa.Column('range_scheme_id', sa.Uuid(), nullable=True),
        sa.Column('range_datatype', sa.String(length=50), nullable=True),
        sa.Column('cardinality', sa.String(length=20), nullable=False),
        sa.Column('required', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ['project_id'], ['projects.id'],
            name='fk_properties_project_id',
            ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['range_scheme_id'], ['concept_schemes.id'],
            name='fk_properties_range_scheme_id',
            ondelete='RESTRICT'
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'project_id', 'identifier',
            name='uq_property_identifier_per_project'
        )
    )


def downgrade() -> None:
    """Drop the properties table."""
    op.drop_table('properties')
