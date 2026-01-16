"""Fix counts_toward_physical_capacity nullability.

Revision ID: 20260115_fix_capacity_null
Revises: 20260115_schedule_drafts
Create Date: 2026-01-15

Codex finding: ORM expects non-null but column was created nullable.
This migration backfills NULLs and alters the column to NOT NULL.
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260115_fix_capacity_null"
down_revision = "20260115_schedule_drafts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Backfill any NULLs to FALSE (safe default)
    op.execute("""
        UPDATE activities
        SET counts_toward_physical_capacity = false
        WHERE counts_toward_physical_capacity IS NULL
    """)

    # Alter column to NOT NULL with default
    op.alter_column(
        "activities",
        "counts_toward_physical_capacity",
        existing_type=sa.Boolean(),
        nullable=False,
        server_default=sa.text("false"),
    )


def downgrade() -> None:
    # Migration is irreversible - removing NOT NULL could break app
    raise NotImplementedError(
        "Downgrade not supported. Removing NOT NULL constraint could cause "
        "application errors due to ORM expecting non-null values."
    )
