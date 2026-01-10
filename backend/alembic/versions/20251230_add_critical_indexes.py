"""Add critical indexes for performance optimization

Revision ID: 20251230_critical_idx
Revises: 20251230_block_assign
Create Date: 2025-12-30

Addresses Session 030 findings - adding indexes not covered by 12b3fa4f11ec:
- Missing FK index on Assignment.rotation_template_id
- Missing composite indexes for common query patterns
- Missing FK indexes on Absence and CallAssignment tables

This migration is idempotent - uses if_not_exists=True to avoid conflicts
with existing indexes from prior migrations.

Already covered by migration 12b3fa4f11ec:
- idx_block_date (blocks.date)
- idx_assignment_person_id (assignments.person_id)
- idx_assignment_block_id (assignments.block_id)
- idx_swap_source_faculty (swap_records.source_faculty_id)
- idx_swap_target_faculty (swap_records.target_faculty_id)
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20251230_critical_idx"
down_revision: str | None = "20251230_block_assign"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add performance-critical indexes (idempotent).

    Creates indexes for:
    - assignments.rotation_template_id: Fast rotation template lookups
    - assignments(person_id, block_id): Composite index for assignment queries
    - blocks(date, time_of_day): Composite index for specific half-day lookups
    - absences.person_id: Fast person absence queries
    - call_assignments.person_id: Fast person call queries
    - call_assignments.date: Fast date-based call queries
    """

    # Assignment table - rotation template FK index (not covered by 12b3fa4f11ec)
    op.create_index(
        "idx_assignment_rotation_template_id",
        "assignments",
        ["rotation_template_id"],
        if_not_exists=True,
    )

    # Composite indexes for common query patterns
    op.create_index(
        "idx_assignment_person_block",
        "assignments",
        ["person_id", "block_id"],
        if_not_exists=True,
    )

    # Block table - composite index for specific half-day lookups
    # (12b3fa4f11ec only covers single-column date index)
    op.create_index(
        "idx_block_date_time_of_day",
        "blocks",
        ["date", "time_of_day"],
        if_not_exists=True,
    )

    # Absence table - person_id FK index
    op.create_index(
        "idx_absence_person_id", "absences", ["person_id"], if_not_exists=True
    )

    # CallAssignment table - person_id and date indexes
    op.create_index(
        "idx_call_assignment_person_id",
        "call_assignments",
        ["person_id"],
        if_not_exists=True,
    )
    op.create_index(
        "idx_call_assignment_date", "call_assignments", ["date"], if_not_exists=True
    )


def downgrade() -> None:
    """Remove indexes created by this migration.

    Note: Only drops indexes created by this migration. Does not affect
    the existing indexes with different names from prior migrations.
    """
    op.drop_index("idx_call_assignment_date", "call_assignments", if_exists=True)
    op.drop_index("idx_call_assignment_person_id", "call_assignments", if_exists=True)
    op.drop_index("idx_absence_person_id", "absences", if_exists=True)
    op.drop_index("idx_block_date_time_of_day", "blocks", if_exists=True)
    op.drop_index("idx_assignment_person_block", "assignments", if_exists=True)
    op.drop_index("idx_assignment_rotation_template_id", "assignments", if_exists=True)
