"""add_parent_comment_id_for_threading

Revision ID: 6701f9190cd7
Revises: 6f1b1b748eb1
Create Date: 2026-01-31 10:13:24.212009

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6701f9190cd7'
down_revision: Union[str, Sequence[str], None] = '6f1b1b748eb1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add parent_comment_id column for threading
    op.add_column(
        'comments',
        sa.Column('parent_comment_id', sa.Uuid(), nullable=True)
    )

    # Add foreign key constraint to comments table (self-referencing)
    op.create_foreign_key(
        'fk_comments_parent_comment_id',
        'comments',
        'comments',
        ['parent_comment_id'],
        ['id'],
        ondelete='CASCADE'
    )

    # Add index for query performance
    op.create_index(
        'ix_comments_parent_comment_id',
        'comments',
        ['parent_comment_id'],
        unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_comments_parent_comment_id', table_name='comments')
    op.drop_constraint('fk_comments_parent_comment_id', 'comments', type_='foreignkey')
    op.drop_column('comments', 'parent_comment_id')
