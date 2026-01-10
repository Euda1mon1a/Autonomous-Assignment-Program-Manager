"""Add activity_id FK to weekly_patterns.

Revision ID: 20260109_weekly_pattern_fk
Revises: 20260109_add_activities
Create Date: 2026-01-09

This migration:
1. Adds activity_id column (nullable initially)
2. Backfills activity_id from activity_type string mapping
3. Creates index for efficient queries

Note: activity_id remains nullable for backward compatibility.
A future migration will make it NOT NULL after verifying data integrity.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260109_weekly_pattern_fk"
down_revision = "20260109_add_activities"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add activity_id FK to weekly_patterns and backfill from activity_type."""
    # Add activity_id column (nullable for migration)
    op.add_column(
        "weekly_patterns",
        sa.Column(
            "activity_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
            comment="FK to activities table - the activity assigned to this slot",
        ),
    )

    # Create FK constraint
    op.create_foreign_key(
        "fk_weekly_patterns_activity_id",
        "weekly_patterns",
        "activities",
        ["activity_id"],
        ["id"],
        ondelete="RESTRICT",
    )

    # Create index
    op.create_index(
        "ix_weekly_patterns_activity_id",
        "weekly_patterns",
        ["activity_id"],
    )

    # Backfill activity_id from activity_type using string mapping
    # Maps legacy activity_type strings to Activity.code values
    op.execute("""
        UPDATE weekly_patterns wp
        SET activity_id = a.id
        FROM activities a
        WHERE wp.activity_id IS NULL
        AND (
            -- Direct code matches
            (wp.activity_type = a.code)
            -- Handle legacy variations
            OR (wp.activity_type = 'conference' AND a.code = 'lec')
            OR (wp.activity_type = 'lecture' AND a.code = 'lec')
            OR (wp.activity_type = 'academic' AND a.code = 'lec')
            OR (wp.activity_type = 'procedures' AND a.code = 'procedure')
        )
    """)

    # Log any unmapped activity_types for manual review
    # (These will have activity_id = NULL)


def downgrade() -> None:
    """Remove activity_id FK from weekly_patterns."""
    op.drop_index("ix_weekly_patterns_activity_id", table_name="weekly_patterns")
    op.drop_constraint(
        "fk_weekly_patterns_activity_id", "weekly_patterns", type_="foreignkey"
    )
    op.drop_column("weekly_patterns", "activity_id")
