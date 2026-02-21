"""make property domain_class nullable

Revision ID: 5a1c3e7f9b2d
Revises: 4837a613b04f
Create Date: 2026-02-21 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '5a1c3e7f9b2d'
down_revision: Union[str, Sequence[str], None] = '4837a613b04f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Allow NULL domain_class on properties (OWL properties may omit rdfs:domain)."""
    op.alter_column('properties', 'domain_class', nullable=True)

    # Convert empty strings to NULL
    op.execute("UPDATE properties SET domain_class = NULL WHERE domain_class = ''")


def downgrade() -> None:
    """Restore NOT NULL on domain_class."""
    op.execute("UPDATE properties SET domain_class = '' WHERE domain_class IS NULL")
    op.alter_column('properties', 'domain_class', nullable=False)
