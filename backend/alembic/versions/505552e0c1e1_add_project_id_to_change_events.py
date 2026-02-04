"""add_project_id_to_change_events

Revision ID: 505552e0c1e1
Revises: 9f440ee619af
Create Date: 2026-02-04 17:24:52.544006

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '505552e0c1e1'
down_revision: Union[str, Sequence[str], None] = '9f440ee619af'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add project_id column to change_events for project-level tracking."""
    op.add_column('change_events', sa.Column('project_id', sa.Uuid(), nullable=True))
    op.create_index(
        'ix_change_events_project_timestamp',
        'change_events',
        ['project_id', sa.literal_column('timestamp DESC')],
        unique=False
    )
    op.create_foreign_key(
        'fk_change_events_project_id',
        'change_events',
        'projects',
        ['project_id'],
        ['id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    """Remove project_id column from change_events."""
    op.drop_constraint('fk_change_events_project_id', 'change_events', type_='foreignkey')
    op.drop_index('ix_change_events_project_timestamp', table_name='change_events')
    op.drop_column('change_events', 'project_id')
