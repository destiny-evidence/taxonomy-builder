"""add position to concept schemes

Revision ID: ac5e25c4a2e5
Revises: cc9e5cb29931
Create Date: 2026-06-18 18:21:45.421777

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ac5e25c4a2e5'
down_revision: Union[str, Sequence[str], None] = 'cc9e5cb29931'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "concept_schemes",
        sa.Column("position", sa.Integer(), server_default="0", nullable=False),
    )
    # Backfill a gapless 0..n-1 sequence per project, preserving the previous
    # alphabetical (title) ordering as the starting order.
    op.execute(
        """
        UPDATE concept_schemes cs SET position = sub.rn
        FROM (
            SELECT id, row_number() OVER (
                PARTITION BY project_id ORDER BY title
            ) - 1 AS rn
            FROM concept_schemes
        ) sub
        WHERE cs.id = sub.id
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("concept_schemes", "position")
