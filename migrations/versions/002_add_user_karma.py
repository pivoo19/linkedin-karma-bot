"""Add user_karma table for per-group karma tracking

Revision ID: 002
Revises: 001
Create Date: 2025-12-14
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create user_karma table for storing karma per group/chat."""
    op.create_table(
        'user_karma',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('chat_id', sa.BigInteger(), nullable=False),
        sa.Column('karma_total', sa.Integer(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['user_id'], ['users.telegram_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'chat_id', name='uq_user_karma_user_chat')
    )


def downgrade() -> None:
    """Remove user_karma table."""
    op.drop_table('user_karma')




