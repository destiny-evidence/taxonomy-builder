"""add_comments_table

Revision ID: 6f1b1b748eb1
Revises: f400daf85714
Create Date: 2026-01-29 22:33:06.929269

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '6f1b1b748eb1'
down_revision: Union[str, Sequence[str], None] = 'f400daf85714'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('comments',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('concept_id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['concept_id'], ['concepts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_comments_concept_deleted', 'comments', ['concept_id', 'deleted_at'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_comments_concept_deleted', table_name='comments')
    op.drop_table('comments')
