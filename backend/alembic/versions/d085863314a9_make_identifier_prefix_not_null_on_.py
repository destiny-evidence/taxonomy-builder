"""Make identifier_prefix NOT NULL on projects

Revision ID: d085863314a9
Revises: fb9cbceafccb
Create Date: 2026-03-15 12:05:48.051727

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d085863314a9"
down_revision: str | Sequence[str] | None = "fb9cbceafccb"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Default prefix for any projects that lack one (defensive — greenfields)
_DEFAULT_PREFIX = "C"


def upgrade() -> None:
    """Make identifier_prefix NOT NULL."""
    # Backfill any NULL prefixes (defensive for dev databases)
    op.execute(
        sa.text(
            "UPDATE projects SET identifier_prefix = :default_prefix "
            "WHERE identifier_prefix IS NULL"
        ).bindparams(default_prefix=_DEFAULT_PREFIX)
    )

    op.alter_column(
        "projects",
        "identifier_prefix",
        existing_type=sa.String(length=4),
        nullable=False,
    )

    # Tighten check constraint: NULL clause no longer needed
    op.drop_constraint(
        "ck_projects_identifier_prefix_format", "projects", type_="check"
    )
    op.create_check_constraint(
        "ck_projects_identifier_prefix_format",
        "projects",
        r"identifier_prefix ~ '^[A-Z]{1,4}$'",
    )


def downgrade() -> None:
    """Revert identifier_prefix to nullable."""
    # Restore NULL-permissive check constraint
    op.drop_constraint(
        "ck_projects_identifier_prefix_format", "projects", type_="check"
    )
    op.create_check_constraint(
        "ck_projects_identifier_prefix_format",
        "projects",
        r"identifier_prefix ~ '^[A-Z]{1,4}$' OR identifier_prefix IS NULL",
    )

    op.alter_column(
        "projects",
        "identifier_prefix",
        existing_type=sa.String(length=4),
        nullable=True,
    )
