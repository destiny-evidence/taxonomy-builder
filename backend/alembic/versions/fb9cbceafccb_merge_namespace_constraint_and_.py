"""Merge namespace constraint and identifier NOT NULL

Revision ID: fb9cbceafccb
Revises: b367fee3d2ab, e032ecca6201
Create Date: 2026-03-15 07:49:33.462811

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fb9cbceafccb'
down_revision: Union[str, Sequence[str], None] = ('b367fee3d2ab', 'e032ecca6201')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
