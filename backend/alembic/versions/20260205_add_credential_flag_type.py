"""Add credential_missing draft flag type.

Revision ID: 20260205_add_credential_flag_type
Revises: 20260204_lock_window_break_glass
Create Date: 2026-02-05
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260205_add_credential_flag_type"
down_revision = "20260204_lock_window_break_glass"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Extend enum (Postgres only)
    op.execute(
        "ALTER TYPE draft_flag_type ADD VALUE IF NOT EXISTS 'credential_missing'"
    )


def downgrade() -> None:
    # Note: enum values are not removed on downgrade.
    pass
