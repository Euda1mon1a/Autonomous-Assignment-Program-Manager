"""Add lock window settings and break-glass approval fields.

Revision ID: 20260204_lock_window_break_glass
Revises: 20260203_add_absence_status
Create Date: 2026-02-04
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "20260204_lock_window_break_glass"
down_revision = "20260203_add_absence_status"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Extend enums (Postgres only)
    op.execute("ALTER TYPE draft_source_type ADD VALUE IF NOT EXISTS 'resilience'")
    op.execute(
        "ALTER TYPE draft_flag_type ADD VALUE IF NOT EXISTS 'lock_window_violation'"
    )

    # Application settings: lock date
    op.add_column(
        "application_settings",
        sa.Column("schedule_lock_date", sa.Date(), nullable=True),
    )

    # Schedule drafts: break-glass approval fields
    op.add_column(
        "schedule_drafts",
        sa.Column("approved_at", sa.DateTime(), nullable=True),
    )
    op.add_column(
        "schedule_drafts",
        sa.Column(
            "approved_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
    )
    op.add_column(
        "schedule_drafts",
        sa.Column("approval_reason", sa.Text(), nullable=True),
    )
    op.add_column(
        "schedule_drafts",
        sa.Column("lock_date_at_approval", sa.Date(), nullable=True),
    )


def downgrade() -> None:
    # Note: enum values are not removed on downgrade.
    op.drop_column("schedule_drafts", "lock_date_at_approval")
    op.drop_column("schedule_drafts", "approval_reason")
    op.drop_column("schedule_drafts", "approved_by_id")
    op.drop_column("schedule_drafts", "approved_at")
    op.drop_column("application_settings", "schedule_lock_date")
