"""add namespace_prefixes to projects

Revision ID: 5890c2d4e19b
Revises: 848fa99ec415
Create Date: 2026-03-24 15:00:02.112622

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5890c2d4e19b"
down_revision: str | Sequence[str] | None = "848fa99ec415"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "projects",
        sa.Column(
            "namespace_prefixes",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=False,
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("projects", "namespace_prefixes")
