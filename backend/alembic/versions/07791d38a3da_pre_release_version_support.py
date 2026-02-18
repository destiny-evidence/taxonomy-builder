"""pre-release version support

Revision ID: 07791d38a3da
Revises: f439aa87ed1d
Create Date: 2026-02-18 16:35:02.147122

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY as PG_ARRAY


# revision identifiers, used by Alembic.
revision: str = '07791d38a3da'
down_revision: Union[str, Sequence[str], None] = 'f439aa87ed1d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

NEW_SORT_KEY_EXPR = (
    "CASE WHEN version LIKE '%-pre%' THEN"
    " string_to_array(split_part(version, '-pre', 1), '.')::int[]"
    " || ARRAY[split_part(version, '-pre', 2)::int]"
    " ELSE"
    " string_to_array(version, '.')::int[] || ARRAY[2147483647]"
    " END"
)

OLD_SORT_KEY_EXPR = "string_to_array(version, '.')::int[]"


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_index(
        "ix_one_draft_per_project",
        table_name="published_versions",
        postgresql_where="(NOT finalized)",
    )

    # Postgres cannot alter generated columns — drop and recreate.
    # Dropping the column also drops ix_latest_version_lookup which depends on it.
    op.drop_column("published_versions", "version_sort_key")
    op.add_column(
        "published_versions",
        sa.Column(
            "version_sort_key",
            PG_ARRAY(sa.Integer),
            sa.Computed(NEW_SORT_KEY_EXPR, persisted=True),
        ),
    )
    op.create_index(
        "ix_latest_version_lookup",
        "published_versions",
        ["project_id", "version_sort_key"],
        postgresql_where="finalized",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("published_versions", "version_sort_key")
    op.add_column(
        "published_versions",
        sa.Column(
            "version_sort_key",
            PG_ARRAY(sa.Integer),
            sa.Computed(OLD_SORT_KEY_EXPR, persisted=True),
        ),
    )
    op.create_index(
        "ix_latest_version_lookup",
        "published_versions",
        ["project_id", "version_sort_key"],
        postgresql_where="finalized",
    )

    op.create_index(
        "ix_one_draft_per_project",
        "published_versions",
        ["project_id"],
        unique=True,
        postgresql_where="(NOT finalized)",
    )
