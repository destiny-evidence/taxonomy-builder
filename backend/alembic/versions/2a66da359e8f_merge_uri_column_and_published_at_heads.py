"""merge uri column and published_at heads

Revision ID: 2a66da359e8f
Revises: 4837a613b04f, ad2e0561b276
Create Date: 2026-02-24 17:28:45.198761

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2a66da359e8f'
down_revision: Union[str, Sequence[str], None] = ('4837a613b04f', 'ad2e0561b276')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
