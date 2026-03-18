"""Drop domain_class scalar from properties.

Backfill the property_domain_class join table from the scalar column
for any property that doesn't already have entries, then drop the column.
The join table becomes the sole source of truth for property domain classes.

Revision ID: 848fa99ec415
Revises: d085863314a9
Create Date: 2026-03-18 07:55:06.366617

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "848fa99ec415"
down_revision: str | Sequence[str] | None = "d085863314a9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Backfill join table from scalar domain_class, then drop the column."""
    # Backfill: for each property without join table entries, insert one
    # from the scalar domain_class → matching ontology_classes row.
    op.execute(
        sa.text("""
            INSERT INTO property_domain_class (property_id, class_id)
            SELECT p.id, oc.id
            FROM properties p
            JOIN ontology_classes oc
                ON oc.project_id = p.project_id
                AND oc.uri = p.domain_class
            WHERE NOT EXISTS (
                SELECT 1 FROM property_domain_class pdc
                WHERE pdc.property_id = p.id
            )
        """)
    )

    op.drop_column("properties", "domain_class")


def downgrade() -> None:
    """Re-add domain_class column and populate from join table."""
    op.add_column(
        "properties",
        sa.Column("domain_class", sa.String(2048), nullable=True),
    )

    # Populate from join table (first entry by class URI order)
    op.execute(
        sa.text("""
            UPDATE properties p
            SET domain_class = (
                SELECT oc.uri
                FROM property_domain_class pdc
                JOIN ontology_classes oc ON oc.id = pdc.class_id
                WHERE pdc.property_id = p.id
                ORDER BY oc.uri
                LIMIT 1
            )
        """)
    )

    # Column was originally NOT NULL, but after multi-domain support
    # some properties may have no domain classes — keep nullable on downgrade.
    # op.alter_column("properties", "domain_class", nullable=False)
