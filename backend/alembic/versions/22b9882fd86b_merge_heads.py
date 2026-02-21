"""merge heads

Revision ID: 22b9882fd86b
Revises: 6fb4ab977cfe, c6371081056f
Create Date: 2026-02-21 19:26:43.604739

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '22b9882fd86b'
down_revision: Union[str, Sequence[str], None] = ('6fb4ab977cfe', 'c6371081056f')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
