"""remove publisher from concept_schemes

Revision ID: 3b39b875c37c
Revises: a5b8b1a6caeb
Create Date: 2026-02-16 17:54:30.510870

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3b39b875c37c'
down_revision: Union[str, Sequence[str], None] = 'a5b8b1a6caeb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_column('concept_schemes', 'publisher')


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column('concept_schemes', sa.Column('publisher', sa.VARCHAR(length=255), autoincrement=False, nullable=True))
