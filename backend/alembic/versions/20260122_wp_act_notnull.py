"""Add NOT NULL constraint to weekly_patterns.activity_id (EC-4).

Revision ID: 20260122_wp_act_notnull
Revises: 20260120_add_lv_activity
Create Date: 2026-01-22

Addresses EC-4: WeeklyPattern with NULL activity_id leads to cascading
NULL activity_id in half_day_assignments, which crashes XML export.

Pre-condition: All weekly_patterns rows must have non-NULL activity_id.
Run preflight check: ./scripts/preflight-block10.sh to verify before migration.
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260122_wp_act_notnull"
down_revision: str = "20260120_add_lv_activity"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add NOT NULL constraint to weekly_patterns.activity_id.

    Fails if any rows have NULL activity_id - this is intentional.
    Fix NULL values before running migration, not after.
    """
    # First verify no NULL values exist
    conn = op.get_bind()
    result = conn.execute(
        sa.text("SELECT COUNT(*) FROM weekly_patterns WHERE activity_id IS NULL")
    )
    null_count = result.scalar()

    if null_count > 0:
        raise Exception(
            f"Cannot add NOT NULL constraint: {null_count} weekly_patterns rows "
            f"have NULL activity_id. Fix data first, then retry migration. "
            f"Run: ./scripts/preflight-block10.sh to identify issues."
        )

    # Safe to add constraint
    op.alter_column(
        "weekly_patterns",
        "activity_id",
        existing_type=sa.dialects.postgresql.UUID(),
        nullable=False,
    )


def downgrade() -> None:
    """Remove NOT NULL constraint from weekly_patterns.activity_id."""
    op.alter_column(
        "weekly_patterns",
        "activity_id",
        existing_type=sa.dialects.postgresql.UUID(),
        nullable=True,
    )
