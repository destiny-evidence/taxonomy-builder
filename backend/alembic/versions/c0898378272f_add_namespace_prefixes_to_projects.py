"""add namespace_prefixes to projects

Revision ID: c0898378272f
Revises: d085863314a9
Create Date: 2026-03-20 16:27:08.395009

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c0898378272f"
down_revision: str | Sequence[str] | None = "d085863314a9"
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
