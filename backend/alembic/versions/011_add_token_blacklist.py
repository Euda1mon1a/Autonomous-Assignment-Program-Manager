"""Add token blacklist table

Revision ID: 011
Revises: 010
Create Date: 2025-12-16 00:00:00.000000

Creates table for JWT token blacklist to support stateful
token invalidation on logout.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '011'
down_revision: Union[str, None] = '010'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create token blacklist table."""

    op.create_table(
        'token_blacklist',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),

        # Token identifier
        sa.Column('jti', sa.String(36), unique=True, nullable=False),

        # Token metadata
        sa.Column('token_type', sa.String(20), server_default="'access'"),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),

        # Timestamps
        sa.Column('blacklisted_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),

        # Reason
        sa.Column('reason', sa.String(100), server_default="'logout'"),
    )

    # Indexes for efficient lookups
    op.create_index('idx_blacklist_jti', 'token_blacklist', ['jti'])
    op.create_index('idx_blacklist_expires', 'token_blacklist', ['expires_at'])
    op.create_index('idx_blacklist_jti_expires', 'token_blacklist', ['jti', 'expires_at'])


def downgrade() -> None:
    """Drop token blacklist table."""
    op.drop_table('token_blacklist')
