"""Add bot delivery tracking fields to users table

Revision ID: 003
Revises: 002
Create Date: 2026-05-07
"""
from alembic import op
import sqlalchemy as sa


revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('bot_started_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('bot_active', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('users', sa.Column('bot_last_message_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'bot_last_message_at')
    op.drop_column('users', 'bot_active')
    op.drop_column('users', 'bot_started_at')
