"""drop legacy feedback response columns

Revision ID: c9909d9448ce
Revises: d383f5418089
Create Date: 2026-07-13 11:45:00.992870

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'c9909d9448ce'
down_revision: Union[str, Sequence[str], None] = 'd383f5418089'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Drop the legacy scalar response columns superseded by feedback_response.

    Contract step of the expand/contract started in d383f5418089. Responses
    live entirely in feedback_response by now, so these columns carry no data
    the thread table doesn't already hold.
    """
    op.drop_constraint(op.f('feedback_responded_by_fkey'), 'feedback', type_='foreignkey')
    op.drop_column('feedback', 'response_content')
    op.drop_column('feedback', 'responded_by')
    op.drop_column('feedback', 'responded_by_name')
    op.drop_column('feedback', 'responded_at')


def downgrade() -> None:
    """Re-add the scalar columns and backfill the latest response per item."""
    op.add_column('feedback', sa.Column('response_content', sa.TEXT(), nullable=True))
    op.add_column('feedback', sa.Column('responded_at', sa.TIMESTAMP(), nullable=True))
    op.add_column(
        'feedback', sa.Column('responded_by_name', sa.VARCHAR(length=255), nullable=True)
    )
    op.add_column('feedback', sa.Column('responded_by', sa.Uuid(), nullable=True))
    op.create_foreign_key(
        op.f('feedback_responded_by_fkey'),
        'feedback',
        'users',
        ['responded_by'],
        ['id'],
        ondelete='SET NULL',
    )

    op.execute(
        """
        UPDATE feedback f SET
            response_content = r.content,
            responded_by = r.responded_by,
            responded_by_name = r.responded_by_name,
            responded_at = r.created_at
        FROM (
            SELECT DISTINCT ON (feedback_id)
                feedback_id, content, responded_by, responded_by_name, created_at
            FROM feedback_response
            ORDER BY feedback_id, created_at DESC, id DESC
        ) r
        WHERE f.id = r.feedback_id
        """
    )
