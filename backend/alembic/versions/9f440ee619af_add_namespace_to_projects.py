"""add namespace to projects

Revision ID: 9f440ee619af
Revises: 6701f9190cd7
Create Date: 2026-01-31 14:17:48.187405

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '9f440ee619af'
down_revision: Union[str, Sequence[str], None] = '6701f9190cd7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('projects', sa.Column('namespace', sa.String(length=2048), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('projects', 'namespace')
