"""Add identifier prefix and counter to projects, partial unique index on concepts

Revision ID: 476b21d7dd14
Revises: 86d7baaf2296
Create Date: 2026-03-10 18:34:19.527886

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '476b21d7dd14'
down_revision: str | Sequence[str] | None = '86d7baaf2296'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('projects', sa.Column('identifier_prefix', sa.String(length=4), nullable=True))
    op.add_column(
        'projects',
        sa.Column('identifier_counter', sa.Integer(), server_default='0', nullable=False),
    )
    op.create_check_constraint(
        'ck_projects_identifier_prefix_format',
        'projects',
        r"identifier_prefix ~ '^[A-Z]{1,4}$' OR identifier_prefix IS NULL",
    )
    op.create_check_constraint(
        'ck_projects_identifier_counter_non_negative',
        'projects',
        'identifier_counter >= 0',
    )
    op.create_index(
        'uq_concept_scheme_identifier',
        'concepts',
        ['scheme_id', 'identifier'],
        unique=True,
        postgresql_where=sa.text('identifier IS NOT NULL'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('uq_concept_scheme_identifier', table_name='concepts')
    op.drop_constraint('ck_projects_identifier_counter_non_negative', 'projects', type_='check')
    op.drop_constraint('ck_projects_identifier_prefix_format', 'projects', type_='check')
    op.drop_column('projects', 'identifier_counter')
    op.drop_column('projects', 'identifier_prefix')
