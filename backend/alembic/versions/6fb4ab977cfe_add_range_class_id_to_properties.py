"""add range_class to properties

Revision ID: 6fb4ab977cfe
Revises: 70a40f327144
Create Date: 2026-02-19 16:24:13.785256

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6fb4ab977cfe'
down_revision: Union[str, Sequence[str], None] = '70a40f327144'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('properties', sa.Column('range_class', sa.String(2048), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('properties', 'range_class')
