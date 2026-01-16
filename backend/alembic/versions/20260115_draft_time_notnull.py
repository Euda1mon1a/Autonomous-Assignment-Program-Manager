"""Fix time_of_day nullable in schedule_draft_assignments.

Revision ID: 20260115_draft_time_notnull
Revises: 20260115_fix_capacity_null
Create Date: 2026-01-15

Codex finding: time_of_day is nullable but part of unique constraint.
In Postgres, NULL != NULL allows duplicate (person, date, NULL) entries.
Solution: Use 'ALL' sentinel for full-day assignments, make NOT NULL.
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260115_draft_time_notnull"
down_revision = "20260115_fix_capacity_null"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Backfill NULL time_of_day to 'ALL' (sentinel for full-day)
    op.execute("""
        UPDATE schedule_draft_assignments
        SET time_of_day = 'ALL'
        WHERE time_of_day IS NULL
    """)

    # Alter column to NOT NULL with default
    op.alter_column(
        "schedule_draft_assignments",
        "time_of_day",
        existing_type=sa.String(10),
        nullable=False,
        server_default=sa.text("'ALL'"),
    )


def downgrade() -> None:
    # Migration is irreversible - removing NOT NULL could cause duplicate
    # entries in the unique constraint (NULL != NULL in Postgres)
    raise NotImplementedError(
        "Downgrade not supported. Removing NOT NULL from time_of_day would "
        "allow duplicate entries due to NULL != NULL in unique constraints."
    )
