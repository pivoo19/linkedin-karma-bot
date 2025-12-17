"""Add first_post_at field to users table

Revision ID: 001
Revises:
Create Date: 2025-12-14
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add first_post_at column to users table."""
    op.add_column(
        'users',
        sa.Column('first_post_at', sa.DateTime(), nullable=True)
    )


def downgrade() -> None:
    """Remove first_post_at column from users table."""
    op.drop_column('users', 'first_post_at')
