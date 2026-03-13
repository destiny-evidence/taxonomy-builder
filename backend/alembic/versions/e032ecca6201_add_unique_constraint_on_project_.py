"""add unique constraint on project namespace

Revision ID: e032ecca6201
Revises: 9817166d9a32
Create Date: 2026-03-13 10:46:51.896312

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'e032ecca6201'
down_revision: Union[str, Sequence[str], None] = '9817166d9a32'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_index('uq_project_namespace', 'projects', ['namespace'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('uq_project_namespace', table_name='projects')
