"""merge heads

Revision ID: 8450dd944042
Revises: ad2e0561b276, cc675b212d3c
Create Date: 2026-02-24 12:51:32.417202

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8450dd944042'
down_revision: Union[str, Sequence[str], None] = ('ad2e0561b276', 'cc675b212d3c')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
