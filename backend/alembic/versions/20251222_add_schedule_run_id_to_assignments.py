"""Add schedule_run_id to assignments for provenance tracking.

Revision ID: 20251222_provenance
Revises: 20251222_fix_schema
Create Date: 2025-12-22
"""

from typing import Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = "20251222_provenance"
down_revision: Union[str, None] = "20251222_fix_schema"
branch_labels: Union[str, tuple, None] = None
depends_on: Union[str, tuple, None] = None


def upgrade() -> None:
    """Add schedule_run_id column to assignments table."""
    # Add the column
    op.add_column(
        "assignments",
        sa.Column("schedule_run_id", UUID(as_uuid=True), nullable=True),
    )

    # Add foreign key constraint
    op.create_foreign_key(
        "fk_assignments_schedule_run",
        "assignments",
        "schedule_runs",
        ["schedule_run_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Add index for efficient queries
    op.create_index(
        "idx_assignments_schedule_run",
        "assignments",
        ["schedule_run_id"],
    )

    # Also add to assignments_version table for SQLAlchemy-Continuum
    op.add_column(
        "assignments_version",
        sa.Column("schedule_run_id", UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "assignments_version",
        sa.Column("schedule_run_id_mod", sa.Boolean(), nullable=True),
    )


def downgrade() -> None:
    """Remove schedule_run_id column from assignments table."""
    # Remove from version table first
    op.drop_column("assignments_version", "schedule_run_id_mod")
    op.drop_column("assignments_version", "schedule_run_id")

    # Remove from main table
    op.drop_index("idx_assignments_schedule_run", table_name="assignments")
    op.drop_constraint("fk_assignments_schedule_run", "assignments", type_="foreignkey")
    op.drop_column("assignments", "schedule_run_id")
