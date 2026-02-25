"""merge heads

Revision ID: 2baacab5ddc4
Revises: 012b88130906, 2a66da359e8f
Create Date: 2026-02-25 16:32:11.032143

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "2baacab5ddc4"
down_revision: Union[str, Sequence[str], None] = ("012b88130906", "2a66da359e8f")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
