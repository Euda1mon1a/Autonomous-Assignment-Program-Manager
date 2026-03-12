"""Drop secondary_rotation_template_id column.

Migrates any remaining old-format rows (secondary_rotation_template_id set,
block_half IS NULL) into two atomic rows with block_half=1 and block_half=2,
then drops the column, FK, and index.

Revision ID: 20260312_drop_secondary_rot
Revises: 20260311_add_block_half
Create Date: 2026-03-12
"""

import sqlalchemy as sa
from alembic import op

revision = "20260312_drop_secondary_rot"
down_revision = "20260311_add_block_half"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # Step 1: Mark the originals as half=1 FIRST (before inserting half=2),
    # because the trg_block_half_exclusion trigger prevents inserting
    # a half-block row when a full-block row (block_half IS NULL) exists.
    conn.execute(
        sa.text("""
        UPDATE block_assignments SET block_half = 1
        WHERE secondary_rotation_template_id IS NOT NULL
          AND block_half IS NULL
        """)
    )

    # Step 2: Create a half=2 row for each converted row.
    conn.execute(
        sa.text("""
        INSERT INTO block_assignments (
            id, block_number, academic_year, academic_block_id, resident_id,
            rotation_template_id, block_half, assignment_reason, notes,
            created_by, created_at, updated_at
        )
        SELECT
            gen_random_uuid(),
            block_number, academic_year, academic_block_id, resident_id,
            secondary_rotation_template_id, 2, assignment_reason, notes,
            created_by, created_at, now()
        FROM block_assignments
        WHERE secondary_rotation_template_id IS NOT NULL
          AND block_half = 1
        """)
    )

    # Step 3: Drop the FK constraint (if it exists), then the column
    conn.execute(
        sa.text("""
        DO $$
        BEGIN
            ALTER TABLE block_assignments
                DROP CONSTRAINT IF EXISTS block_assignments_secondary_rotation_template_id_fkey;
        EXCEPTION WHEN undefined_object THEN
            NULL;
        END $$;
        """)
    )
    op.drop_column("block_assignments", "secondary_rotation_template_id")


def downgrade() -> None:
    # Re-add the column
    op.add_column(
        "block_assignments",
        sa.Column(
            "secondary_rotation_template_id",
            sa.UUID(),
            nullable=True,
        ),
    )
    op.create_foreign_key(
        "block_assignments_secondary_rotation_template_id_fkey",
        "block_assignments",
        "rotation_templates",
        ["secondary_rotation_template_id"],
        ["id"],
        ondelete="SET NULL",
    )

    conn = op.get_bind()

    # Reverse: merge block_half=1 + block_half=2 pairs back into single rows.
    # Set secondary_rotation_template_id from the half=2 sibling.
    conn.execute(
        sa.text("""
        UPDATE block_assignments AS h1
        SET secondary_rotation_template_id = h2.rotation_template_id
        FROM block_assignments AS h2
        WHERE h1.block_half = 1
          AND h2.block_half = 2
          AND h1.block_number = h2.block_number
          AND h1.academic_year = h2.academic_year
          AND h1.resident_id = h2.resident_id
        """)
    )

    # Delete the half=2 rows (now merged into secondary)
    conn.execute(
        sa.text("""
        DELETE FROM block_assignments AS h2
        USING block_assignments AS h1
        WHERE h2.block_half = 2
          AND h1.block_half = 1
          AND h2.block_number = h1.block_number
          AND h2.academic_year = h1.academic_year
          AND h2.resident_id = h1.resident_id
        """)
    )

    # Clear block_half on rows that were converted back
    conn.execute(
        sa.text("""
        UPDATE block_assignments SET block_half = NULL
        WHERE secondary_rotation_template_id IS NOT NULL
          AND block_half = 1
        """)
    )
