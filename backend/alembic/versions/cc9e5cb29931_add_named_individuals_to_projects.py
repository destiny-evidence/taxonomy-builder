"""add named_individuals to projects

Revision ID: cc9e5cb29931
Revises: 5890c2d4e19b
Create Date: 2026-03-29 16:34:37.804605

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "cc9e5cb29931"
down_revision: str | Sequence[str] | None = "5890c2d4e19b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "projects",
        sa.Column(
            "named_individuals",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="[]",
            nullable=False,
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("projects", "named_individuals")
