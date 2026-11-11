"""convert project namespace unique index to constraint

Revision ID: 65dfe9dc3e42
Revises: a7c3e1f9b268
Create Date: 2026-11-11 10:57:04.402467

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '65dfe9dc3e42'
down_revision: Union[str, Sequence[str], None] = 'a7c3e1f9b268'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_index(op.f('uq_project_namespace'), table_name='projects')
    op.create_unique_constraint('uq_project_namespace', 'projects', ['namespace'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('uq_project_namespace', 'projects', type_='unique')
    op.create_index(op.f('uq_project_namespace'), 'projects', ['namespace'], unique=True)
