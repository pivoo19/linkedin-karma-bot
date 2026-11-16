"""Add group_topics table for per-topic karma in forum supergroups

Revision ID: 004
Revises: 003
Create Date: 2026-11-16
"""
from alembic import op
import sqlalchemy as sa


revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'group_topics',
        sa.Column('chat_id', sa.BigInteger(), nullable=False),
        sa.Column('topic_id', sa.BigInteger(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('chat_id', 'topic_id'),
    )


def downgrade() -> None:
    op.drop_table('group_topics')
