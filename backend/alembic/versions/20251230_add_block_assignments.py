"""Add block assignments table for leave-eligible rotation scheduling

Revision ID: 20251230_block_assign
Revises: 20251230_rotation_gui
Create Date: 2025-12-30

This migration adds the block_assignments table for tracking
resident rotation assignments at the academic block level (1-13).

Key features:
- Links residents to rotation templates per block
- Tracks leave status (has_leave, leave_days)
- Records assignment reason (leave_eligible_match, coverage_priority, etc.)
- Unique constraint prevents duplicate assignments

The block scheduler uses this to:
1. Auto-assign residents with leave to leave_eligible rotations
2. Ensure coverage for non-leave-eligible rotations (FMIT, inpatient)
3. Balance workload across remaining residents
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "20251230_block_assign"
down_revision = "20251230_rotation_gui"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create block_assignments table
    op.create_table(
        "block_assignments",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        # Block identification
        sa.Column(
            "block_number",
            sa.Integer(),
            nullable=False,
            comment="Academic block number (0-13, where 0 is orientation)",
        ),
        sa.Column(
            "academic_year",
            sa.Integer(),
            nullable=False,
            comment="Academic year starting July 1 (e.g., 2025)",
        ),
        # Assignment links
        sa.Column(
            "resident_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "rotation_template_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("rotation_templates.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        # Leave tracking
        sa.Column(
            "has_leave",
            sa.Boolean(),
            nullable=False,
            server_default="false",
            comment="Does resident have approved leave during this block?",
        ),
        sa.Column(
            "leave_days",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment="Number of leave days in this block",
        ),
        # Assignment metadata
        sa.Column(
            "assignment_reason",
            sa.String(50),
            nullable=False,
            server_default="balanced",
            comment="leave_eligible_match, coverage_priority, balanced, manual, specialty_match",
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        # Audit fields
        sa.Column("created_by", sa.String(255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        # Constraints
        sa.UniqueConstraint(
            "block_number",
            "academic_year",
            "resident_id",
            name="unique_resident_per_block",
        ),
        sa.CheckConstraint(
            "block_number >= 0 AND block_number <= 13",
            name="check_block_number_range",
        ),
        sa.CheckConstraint(
            "leave_days >= 0",
            name="check_leave_days_positive",
        ),
        sa.CheckConstraint(
            "assignment_reason IN ('leave_eligible_match', 'coverage_priority', "
            "'balanced', 'manual', 'specialty_match')",
            name="check_assignment_reason",
        ),
    )

    # Create indexes for common queries
    op.create_index(
        "ix_block_assignments_block_year",
        "block_assignments",
        ["block_number", "academic_year"],
    )
    op.create_index(
        "ix_block_assignments_has_leave",
        "block_assignments",
        ["has_leave"],
        postgresql_where=sa.text("has_leave = true"),
    )


def downgrade() -> None:
    op.drop_index("ix_block_assignments_has_leave", table_name="block_assignments")
    op.drop_index("ix_block_assignments_block_year", table_name="block_assignments")
    op.drop_table("block_assignments")
