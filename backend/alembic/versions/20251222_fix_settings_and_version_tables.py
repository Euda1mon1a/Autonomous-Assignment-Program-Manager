"""Fix settings freeze columns and version table names

Revision ID: 20251222_fix_schema
Revises: 20251222_explain
Create Date: 2025-12-22 05:30:00.000000

Fixes two schema issues:

1. Adds missing freeze columns to application_settings:
   - freeze_horizon_days: How many days ahead to freeze schedule (0-30)
   - freeze_scope: What changes are blocked ('none', 'non_emergency_only', 'all_changes_require_override')

2. Renames version tables to match SQLAlchemy-Continuum naming convention:
   - schedule_run_version -> schedule_runs_version (matches schedule_runs table)

SQLAlchemy-Continuum creates version tables with the pattern: {tablename}_version
So schedule_runs table expects schedule_runs_version.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20251222_fix_schema"
down_revision: str | None = "20251222_explain"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add freeze columns and fix version table names."""

    # 1. Add freeze columns to application_settings
    op.add_column(
        "application_settings",
        sa.Column(
            "freeze_horizon_days", sa.Integer(), nullable=False, server_default="7"
        ),
    )
    op.add_column(
        "application_settings",
        sa.Column("freeze_scope", sa.String(50), nullable=False, server_default="none"),
    )

    # Add check constraints for freeze columns
    op.create_check_constraint(
        "check_freeze_horizon",
        "application_settings",
        "freeze_horizon_days >= 0 AND freeze_horizon_days <= 30",
    )
    op.create_check_constraint(
        "check_freeze_scope",
        "application_settings",
        "freeze_scope IN ('none', 'non_emergency_only', 'all_changes_require_override')",
    )

    # 2. Rename version tables to match Continuum convention
    # Continuum expects {tablename}_version, so:
    # - schedule_runs table -> schedule_runs_version (not schedule_run_version)
    # - assignments table -> assignments_version (not assignment_version)
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_tables WHERE tablename = 'schedule_run_version') THEN
                ALTER TABLE schedule_run_version RENAME TO schedule_runs_version;
            END IF;
            IF EXISTS (SELECT 1 FROM pg_tables WHERE tablename = 'assignment_version') THEN
                ALTER TABLE assignment_version RENAME TO assignments_version;
            END IF;
        END $$;
    """)

    # Update indexes to use new table names
    op.execute(
        "ALTER INDEX IF EXISTS idx_schedule_run_version_transaction RENAME TO idx_schedule_runs_version_transaction"
    )
    op.execute(
        "ALTER INDEX IF EXISTS idx_schedule_run_version_end_transaction RENAME TO idx_schedule_runs_version_end_transaction"
    )
    op.execute(
        "ALTER INDEX IF EXISTS idx_schedule_run_version_operation RENAME TO idx_schedule_runs_version_operation"
    )
    op.execute(
        "ALTER INDEX IF EXISTS idx_assignment_version_transaction RENAME TO idx_assignments_version_transaction"
    )
    op.execute(
        "ALTER INDEX IF EXISTS idx_assignment_version_end_transaction RENAME TO idx_assignments_version_end_transaction"
    )
    op.execute(
        "ALTER INDEX IF EXISTS idx_assignment_version_operation RENAME TO idx_assignments_version_operation"
    )


def downgrade() -> None:
    """Remove freeze columns and restore original table names."""

    # Rename tables back
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_tables WHERE tablename = 'schedule_runs_version') THEN
                ALTER TABLE schedule_runs_version RENAME TO schedule_run_version;
            END IF;
            IF EXISTS (SELECT 1 FROM pg_tables WHERE tablename = 'assignments_version') THEN
                ALTER TABLE assignments_version RENAME TO assignment_version;
            END IF;
        END $$;
    """)

    # Restore index names
    op.execute(
        "ALTER INDEX IF EXISTS idx_schedule_runs_version_transaction RENAME TO idx_schedule_run_version_transaction"
    )
    op.execute(
        "ALTER INDEX IF EXISTS idx_schedule_runs_version_end_transaction RENAME TO idx_schedule_run_version_end_transaction"
    )
    op.execute(
        "ALTER INDEX IF EXISTS idx_schedule_runs_version_operation RENAME TO idx_schedule_run_version_operation"
    )
    op.execute(
        "ALTER INDEX IF EXISTS idx_assignments_version_transaction RENAME TO idx_assignment_version_transaction"
    )
    op.execute(
        "ALTER INDEX IF EXISTS idx_assignments_version_end_transaction RENAME TO idx_assignment_version_end_transaction"
    )
    op.execute(
        "ALTER INDEX IF EXISTS idx_assignments_version_operation RENAME TO idx_assignment_version_operation"
    )

    # Drop constraints
    op.drop_constraint("check_freeze_scope", "application_settings")
    op.drop_constraint("check_freeze_horizon", "application_settings")

    # Drop columns
    op.drop_column("application_settings", "freeze_scope")
    op.drop_column("application_settings", "freeze_horizon_days")
