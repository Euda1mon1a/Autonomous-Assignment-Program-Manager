"""Add composite performance indexes for scheduling queries.

DEBT-004: Additional composite indexes for complex query patterns.

Note: Single-column indexes were added in 12b3fa4f11ec_add_performance_indexes.py.
This migration adds composite indexes for multi-column query patterns that benefit
from index covering.

These indexes significantly improve query performance for:
- Assignment person/block lookups (common in schedule loading)
- Role-based assignment queries by block
- Temporal queries on assignments
- Block assignment lookups by year

Revision ID: 20260117_perf_idx
Revises: 20260116_wellness_tables
Create Date: 2026-01-17
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260117_perf_idx"
down_revision = "20260116_wellness_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add composite performance indexes (idempotent)."""
    # Composite index for assignment lookups by person and block
    # Speeds up: "Get all assignments for person X in block Y"
    op.create_index(
        "idx_assignments_person_block",
        "assignments",
        ["person_id", "block_id"],
        unique=False,
        if_not_exists=True,
    )

    # Composite index for role-based queries within a block
    # Speeds up: "Get all supervising faculty for block Y"
    op.create_index(
        "idx_assignments_block_role",
        "assignments",
        ["block_id", "role"],
        unique=False,
        if_not_exists=True,
    )

    # Index on created_at for temporal queries
    # Speeds up: "Get assignments created after X"
    op.create_index(
        "idx_assignments_created_at",
        "assignments",
        ["created_at"],
        unique=False,
        if_not_exists=True,
    )

    # Composite index for person's recent assignments
    # Speeds up: "Get person's most recent assignments"
    op.create_index(
        "idx_assignments_person_created",
        "assignments",
        ["person_id", "created_at"],
        unique=False,
        if_not_exists=True,
    )

    # Block assignments indexes
    op.create_index(
        "idx_block_assignments_resident",
        "block_assignments",
        ["resident_id"],
        unique=False,
        if_not_exists=True,
    )

    op.create_index(
        "idx_block_assignments_block_year",
        "block_assignments",
        ["block_number", "academic_year"],
        unique=False,
        if_not_exists=True,
    )

    op.create_index(
        "idx_block_assignments_rotation",
        "block_assignments",
        ["rotation_template_id"],
        unique=False,
        if_not_exists=True,
    )


def downgrade() -> None:
    """Remove composite performance indexes."""
    op.drop_index(
        "idx_block_assignments_rotation",
        table_name="block_assignments",
        if_exists=True,
    )
    op.drop_index(
        "idx_block_assignments_block_year",
        table_name="block_assignments",
        if_exists=True,
    )
    op.drop_index(
        "idx_block_assignments_resident",
        table_name="block_assignments",
        if_exists=True,
    )
    op.drop_index(
        "idx_assignments_person_created",
        table_name="assignments",
        if_exists=True,
    )
    op.drop_index(
        "idx_assignments_created_at",
        table_name="assignments",
        if_exists=True,
    )
    op.drop_index(
        "idx_assignments_block_role",
        table_name="assignments",
        if_exists=True,
    )
    op.drop_index(
        "idx_assignments_person_block",
        table_name="assignments",
        if_exists=True,
    )
