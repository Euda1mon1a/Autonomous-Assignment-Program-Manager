"""Add block_half column to block_assignments.

Enables half-block rotation assignments. Combined rotations (e.g., NF +
Cardiology) become two rows (block_half=1 and block_half=2) instead of
one row with secondary_rotation_template_id.

- block_half NULL = full-block assignment (backward compatible)
- block_half 1 = days 1-14 (first half)
- block_half 2 = days 15-28 (second half)

Replaces unique_resident_per_block with two partial unique indexes to
support both full-block and half-block rows.

Revision ID: 20260311_add_block_half
Revises: 20260311_drop_dead_rot_cols
Create Date: 2026-03-11
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260311_add_block_half"
down_revision: str = "20260311_drop_dead_rot_cols"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add block_half column
    op.add_column(
        "block_assignments",
        sa.Column("block_half", sa.SmallInteger(), nullable=True),
    )

    # Add CHECK constraint: block_half must be 1 or 2 (or NULL for full-block)
    op.create_check_constraint(
        "check_block_half_range",
        "block_assignments",
        "block_half IS NULL OR block_half IN (1, 2)",
    )

    # Drop old unique constraint
    op.drop_constraint("unique_resident_per_block", "block_assignments", type_="unique")

    # New partial unique indexes:
    # 1. Full-block: one row per resident per block when block_half IS NULL
    op.execute(
        sa.text(
            "CREATE UNIQUE INDEX uq_resident_block_full "
            "ON block_assignments (block_number, academic_year, resident_id) "
            "WHERE block_half IS NULL"
        )
    )
    # 2. Half-block: one row per resident per block per half when block_half IS NOT NULL
    op.execute(
        sa.text(
            "CREATE UNIQUE INDEX uq_resident_block_half "
            "ON block_assignments (block_number, academic_year, resident_id, block_half) "
            "WHERE block_half IS NOT NULL"
        )
    )

    # Exclusion: prevent both full-block and half-block rows for same resident/block.
    # If a full-block row exists (block_half IS NULL), no half-block rows can exist,
    # and vice versa. Enforced via a trigger since PostgreSQL partial unique indexes
    # can't cross-reference each other.
    op.execute(
        sa.text("""
        CREATE OR REPLACE FUNCTION check_block_half_exclusion()
        RETURNS TRIGGER AS $$
        BEGIN
            IF NEW.block_half IS NULL THEN
                -- Full-block row: ensure no half-block rows exist
                IF EXISTS (
                    SELECT 1 FROM block_assignments
                    WHERE block_number = NEW.block_number
                      AND academic_year = NEW.academic_year
                      AND resident_id = NEW.resident_id
                      AND block_half IS NOT NULL
                      AND id != NEW.id
                ) THEN
                    RAISE EXCEPTION 'Cannot create full-block assignment: half-block rows exist for this resident/block';
                END IF;
            ELSE
                -- Half-block row: ensure no full-block row exists
                IF EXISTS (
                    SELECT 1 FROM block_assignments
                    WHERE block_number = NEW.block_number
                      AND academic_year = NEW.academic_year
                      AND resident_id = NEW.resident_id
                      AND block_half IS NULL
                      AND id != NEW.id
                ) THEN
                    RAISE EXCEPTION 'Cannot create half-block assignment: full-block row exists for this resident/block';
                END IF;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER trg_block_half_exclusion
        BEFORE INSERT OR UPDATE ON block_assignments
        FOR EACH ROW
        EXECUTE FUNCTION check_block_half_exclusion();
        """)
    )


def downgrade() -> None:
    # Drop trigger and function
    op.execute(
        sa.text("DROP TRIGGER IF EXISTS trg_block_half_exclusion ON block_assignments")
    )
    op.execute(sa.text("DROP FUNCTION IF EXISTS check_block_half_exclusion()"))

    # Drop partial unique indexes
    op.execute(sa.text("DROP INDEX IF EXISTS uq_resident_block_half"))
    op.execute(sa.text("DROP INDEX IF EXISTS uq_resident_block_full"))

    # Restore original unique constraint
    op.create_unique_constraint(
        "unique_resident_per_block",
        "block_assignments",
        ["block_number", "academic_year", "resident_id"],
    )

    # Drop check constraint and column
    op.drop_constraint("check_block_half_range", "block_assignments", type_="check")
    op.drop_column("block_assignments", "block_half")
