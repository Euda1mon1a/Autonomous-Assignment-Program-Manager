"""Add performance indexes for schedule views, assignment lookups, and swap operations.

Revision ID: 12b3fa4f11ec
Revises: acfc96d01118
Create Date: 2025-12-30 05:15:52.943582

DEBT-004: Missing indexes causing slow queries on schedule views, assignment lookups,
and swap operations.

Note: Most of these indexes already exist from prior migrations (001_initial_schema.py
and 20241217_add_fmit_phase2_tables.py). This migration uses if_not_exists=True to be
idempotent - it will create any missing indexes without failing on existing ones.

Existing indexes:
- idx_blocks_date (blocks.date) - from 001
- idx_assignments_block (assignments.block_id) - from 001
- idx_assignments_person (assignments.person_id) - from 001
- ix_swap_records_source_faculty_id (swap_records.source_faculty_id) - from FMIT phase 2
- ix_swap_records_target_faculty_id (swap_records.target_faculty_id) - from FMIT phase 2
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "12b3fa4f11ec"
down_revision: str | None = "acfc96d01118"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add performance indexes (idempotent - uses if_not_exists).

    Creates indexes for:
    - blocks.date: Fast date-based schedule lookups
    - assignments.person_id: Fast person assignment queries
    - assignments.block_id: Fast block assignment queries
    - swap_records.source_faculty_id: Fast swap source lookups
    - swap_records.target_faculty_id: Fast swap target lookups
    """
    # Block date index for schedule views
    op.create_index("idx_block_date", "blocks", ["date"], if_not_exists=True)

    # Assignment indexes for lookup performance
    op.create_index(
        "idx_assignment_person_id", "assignments", ["person_id"], if_not_exists=True
    )
    op.create_index(
        "idx_assignment_block_id", "assignments", ["block_id"], if_not_exists=True
    )

    # Swap record indexes for swap operations
    op.create_index(
        "idx_swap_source_faculty",
        "swap_records",
        ["source_faculty_id"],
        if_not_exists=True,
    )
    op.create_index(
        "idx_swap_target_faculty",
        "swap_records",
        ["target_faculty_id"],
        if_not_exists=True,
    )


def downgrade() -> None:
    """Remove performance indexes.

    Note: Only drops indexes created by this migration. Does not affect
    the existing indexes with different names from prior migrations.
    """
    op.drop_index("idx_swap_target_faculty", "swap_records", if_exists=True)
    op.drop_index("idx_swap_source_faculty", "swap_records", if_exists=True)
    op.drop_index("idx_assignment_block_id", "assignments", if_exists=True)
    op.drop_index("idx_assignment_person_id", "assignments", if_exists=True)
    op.drop_index("idx_block_date", "blocks", if_exists=True)
