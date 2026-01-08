"""Add week_number to weekly_patterns for week-by-week editing.

Revision ID: 20260107_add_week_num_weekly_patterns
Revises: 20260105_add_import_staged_absences
Create Date: 2026-01-07

Allows rotation templates to have different patterns for each week
within a 4-week block. week_number=NULL means same pattern all weeks.
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260107_add_week_num_weekly_patterns"
down_revision = "20260105_add_import_staged_absences"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add week_number column and update unique constraint."""
    # Add week_number column (nullable - NULL means same pattern all weeks)
    op.add_column(
        "weekly_patterns",
        sa.Column(
            "week_number",
            sa.Integer(),
            nullable=True,
            comment="Week 1-4 within the block. NULL = same pattern all weeks",
        ),
    )

    # Drop old unique constraint
    op.drop_constraint("uq_weekly_pattern_slot", "weekly_patterns", type_="unique")

    # Create new unique constraint including week_number
    op.create_unique_constraint(
        "uq_weekly_pattern_slot_v2",
        "weekly_patterns",
        ["rotation_template_id", "day_of_week", "time_of_day", "week_number"],
    )


def downgrade() -> None:
    """Remove week_number column and revert unique constraint."""
    # Drop new unique constraint
    op.drop_constraint("uq_weekly_pattern_slot_v2", "weekly_patterns", type_="unique")

    # Recreate old unique constraint
    op.create_unique_constraint(
        "uq_weekly_pattern_slot",
        "weekly_patterns",
        ["rotation_template_id", "day_of_week", "time_of_day"],
    )

    # Remove week_number column
    op.drop_column("weekly_patterns", "week_number")
