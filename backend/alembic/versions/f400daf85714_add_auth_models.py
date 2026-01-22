"""add_auth_models

Revision ID: f400daf85714
Revises: 1029497287bd
Create Date: 2026-01-16 15:10:51.304984

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f400daf85714'
down_revision: Union[str, Sequence[str], None] = '1029497287bd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create users table for authentication."""
    op.create_table('users',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('keycloak_user_id', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('display_name', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('last_login_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('keycloak_user_id')
    )
    op.create_foreign_key(None, 'change_events', 'users', ['user_id'], ['id'], ondelete='SET NULL')


def downgrade() -> None:
    """Drop users table."""
    op.drop_constraint(None, 'change_events', type_='foreignkey')
    op.drop_table('users')
