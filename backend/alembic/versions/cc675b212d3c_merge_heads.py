"""merge heads

Revision ID: cc675b212d3c
Revises: 6fb4ab977cfe, c6371081056f
Create Date: 2026-02-22 11:26:17.008335

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cc675b212d3c'
down_revision: Union[str, Sequence[str], None] = ('6fb4ab977cfe', 'c6371081056f')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
