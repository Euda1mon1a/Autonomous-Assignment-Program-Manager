"""Add assignment_backups table for rollback support.

Revision ID: 20260118_assignment_backups
Revises: 20260117_perf_idx
Create Date: 2026-01-18

This migration adds the assignment_backups table to store original assignment
data before MODIFY and DELETE operations, enabling complete rollback capability.

Critical Gap Fixed:
- schedule_draft_service.py lines 915-939 log warnings about inability to
  restore deleted/modified assignments because original data was not preserved.
- This table provides that preservation layer.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260118_assignment_backups"
down_revision: str | None = "20260117_perf_idx"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create assignment_backups table for rollback support."""
    op.create_table(
        "assignment_backups",
        # Primary key
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        # Link to the draft assignment that triggered backup
        sa.Column(
            "draft_assignment_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("schedule_draft_assignments.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        # Original assignment being modified/deleted (may be null for HalfDayAssignment)
        sa.Column(
            "original_assignment_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        # Type of operation that required backup
        sa.Column(
            "backup_type",
            sa.String(20),
            nullable=False,
            comment="MODIFY or DELETE",
        ),
        # Original assignment data as JSON for complete restoration
        sa.Column(
            "original_data_json",
            postgresql.JSONB,
            nullable=False,
            comment="Complete original assignment data for restoration",
        ),
        # Source table - assignments or half_day_assignments
        sa.Column(
            "source_table",
            sa.String(50),
            nullable=False,
            default="half_day_assignments",
        ),
        # Audit fields
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "restored_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="When this backup was used for restoration",
        ),
        sa.Column(
            "restored_by_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        # Check constraint for backup_type
        sa.CheckConstraint(
            "backup_type IN ('MODIFY', 'DELETE')",
            name="ck_assignment_backups_backup_type",
        ),
    )

    # Index for finding backups by draft assignment
    op.create_index(
        "idx_assignment_backups_draft_assignment",
        "assignment_backups",
        ["draft_assignment_id"],
    )

    # Index for finding unrestored backups (restoration queue)
    op.create_index(
        "idx_assignment_backups_unrestored",
        "assignment_backups",
        ["draft_assignment_id"],
        postgresql_where=sa.text("restored_at IS NULL"),
    )


def downgrade() -> None:
    """Remove assignment_backups table."""
    op.drop_index("idx_assignment_backups_unrestored", table_name="assignment_backups")
    op.drop_index(
        "idx_assignment_backups_draft_assignment", table_name="assignment_backups"
    )
    op.drop_table("assignment_backups")
