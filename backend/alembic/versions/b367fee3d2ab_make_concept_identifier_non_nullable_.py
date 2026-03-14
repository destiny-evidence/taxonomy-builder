"""Make concept identifier non-nullable with full unique index

Revision ID: b367fee3d2ab
Revises: 9817166d9a32
Create Date: 2026-03-14 10:13:08.766693

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'b367fee3d2ab'
down_revision: str | Sequence[str] | None = '9817166d9a32'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Must match project_service.IDENTIFIER_WIDTH
_IDENTIFIER_WIDTH = 6
_DEFAULT_PREFIX = "C"


def _backfill_null_identifiers() -> None:
    """Backfill NULL identifiers so the column can become NOT NULL.

    1. Assigns a default prefix ('C') to any project that lacks one
    2. Reconciles each project's counter against existing identifiers
    3. Assigns sequential {prefix}{counter:06d} identifiers to NULLs
    """
    conn = op.get_bind()

    # Ensure every project has a prefix — default to 'C'
    conn.execute(
        sa.text(
            "UPDATE projects SET identifier_prefix = :default_prefix "
            "WHERE identifier_prefix IS NULL"
        ),
        {"default_prefix": _DEFAULT_PREFIX},
    )

    # Now all projects have a prefix — backfill NULL identifiers
    projects = conn.execute(
        sa.text(
            "SELECT id, identifier_prefix, identifier_counter "
            "FROM projects"
        )
    ).fetchall()

    for project_id, prefix, counter in projects:
        # Find the highest existing numeric identifier matching this prefix
        start_pos = len(prefix) + 1  # 1-based index past the prefix
        max_existing = conn.execute(
            sa.text(
                "SELECT COALESCE(MAX("
                "  CAST(SUBSTRING(c.identifier FROM :start_pos) AS INTEGER)"
                "), 0) "
                "FROM concepts c "
                "JOIN concept_schemes cs ON c.scheme_id = cs.id "
                "WHERE cs.project_id = :project_id "
                "AND c.identifier LIKE :like_pattern "
                "AND SUBSTRING(c.identifier FROM :start_pos) ~ '^[0-9]+$'"
            ),
            {
                "project_id": project_id,
                "like_pattern": f"{prefix}%",
                "start_pos": start_pos,
            },
        ).scalar() or 0

        current_counter = max(counter, max_existing)

        # Find NULL-identifier concepts for this project
        null_concepts = conn.execute(
            sa.text(
                "SELECT c.id "
                "FROM concepts c "
                "JOIN concept_schemes cs ON c.scheme_id = cs.id "
                "WHERE cs.project_id = :project_id "
                "AND c.identifier IS NULL "
                "ORDER BY c.created_at"
            ),
            {"project_id": project_id},
        ).fetchall()

        for i, (concept_id,) in enumerate(null_concepts, start=1):
            identifier = f"{prefix}{current_counter + i:0{_IDENTIFIER_WIDTH}d}"
            conn.execute(
                sa.text(
                    "UPDATE concepts SET identifier = :identifier WHERE id = :id"
                ),
                {"identifier": identifier, "id": concept_id},
            )

        final_counter = current_counter + len(null_concepts)
        if final_counter > counter:
            conn.execute(
                sa.text(
                    "UPDATE projects SET identifier_counter = :counter "
                    "WHERE id = :id"
                ),
                {"counter": final_counter, "id": project_id},
            )


def upgrade() -> None:
    """Upgrade schema."""
    _backfill_null_identifiers()

    op.alter_column(
        'concepts', 'identifier',
        existing_type=sa.VARCHAR(length=255),
        nullable=False,
    )
    op.drop_index(
        op.f('uq_concept_scheme_identifier'),
        table_name='concepts',
        postgresql_where='(identifier IS NOT NULL)',
    )
    op.create_unique_constraint(
        'uq_concept_scheme_identifier', 'concepts', ['scheme_id', 'identifier'],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('uq_concept_scheme_identifier', 'concepts', type_='unique')
    op.create_index(
        op.f('uq_concept_scheme_identifier'),
        'concepts', ['scheme_id', 'identifier'],
        unique=True,
        postgresql_where='(identifier IS NOT NULL)',
    )
    op.alter_column(
        'concepts', 'identifier',
        existing_type=sa.VARCHAR(length=255),
        nullable=True,
    )
