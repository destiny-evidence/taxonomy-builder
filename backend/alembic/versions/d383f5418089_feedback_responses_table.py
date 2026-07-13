"""feedback responses table

Revision ID: d383f5418089
Revises: ac5e25c4a2e5
Create Date: 2026-07-09 16:52:11.975270

"""
from typing import Sequence, Union
from uuid import uuid7

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'd383f5418089'
down_revision: Union[str, Sequence[str], None] = 'ac5e25c4a2e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add the feedback_response thread table and backfill existing responses.

    Expand step only: the legacy scalar response columns on ``feedback`` are
    left in place and dropped by a later (contract) migration, so an app
    rollback still finds them.
    """
    op.create_table(
        'feedback_response',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('feedback_id', sa.Uuid(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('responded_by', sa.Uuid(), nullable=True),
        sa.Column('responded_by_name', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['feedback_id'], ['feedback.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['responded_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_feedback_response_feedback_id'),
        'feedback_response',
        ['feedback_id'],
        unique=False,
    )

    # Backfill existing single responses into the new table. Ids are generated
    # as uuid7 in Python to match the app's default rather than gen_random_uuid().
    bind = op.get_bind()
    rows = bind.execute(
        sa.text(
            "SELECT id, response_content, responded_by, responded_by_name, "
            "COALESCE(responded_at, created_at) AS created_at "
            "FROM feedback WHERE response_content IS NOT NULL"
        )
    ).fetchall()
    for r in rows:
        bind.execute(
            sa.text(
                "INSERT INTO feedback_response (id, feedback_id, content, "
                "responded_by, responded_by_name, created_at) VALUES "
                "(:id, :fid, :content, :rb, :rbn, :created_at)"
            ),
            {
                "id": uuid7(),
                "fid": r.id,
                "content": r.response_content,
                "rb": r.responded_by,
                "rbn": r.responded_by_name,
                "created_at": r.created_at,
            },
        )


def downgrade() -> None:
    """Collapse the thread back to the latest response per item, drop the table.

    The legacy scalar columns still exist (this migration never dropped them),
    so restore the most recent response into them to capture any responses
    added while the thread table was live.
    """
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

    op.drop_index(op.f('ix_feedback_response_feedback_id'), table_name='feedback_response')
    op.drop_table('feedback_response')
