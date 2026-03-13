"""Make block_half NOT NULL — every resident gets 2 rows per block.

Full-block rotations (FMIT, ICU, etc.) get the same rotation_template_id
in both rows. No more three-way NULL/1/2 branching in consumers.

Revision ID: 20260312_block_half_not_null
Revises: 20260312_archive_slash_nf
Create Date: 2026-03-12
"""

import sqlalchemy as sa
from alembic import op

revision = "20260312_block_half_not_null"
down_revision = "20260312_archive_slash_nf"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # Step 1: Drop trigger + function (blocks data migration otherwise)
    conn.execute(
        sa.text("DROP TRIGGER IF EXISTS trg_block_half_exclusion ON block_assignments")
    )
    conn.execute(sa.text("DROP FUNCTION IF EXISTS check_block_half_exclusion()"))

    # Step 2: Convert NULL block_half → 1
    conn.execute(
        sa.text("UPDATE block_assignments SET block_half = 1 WHERE block_half IS NULL")
    )

    # Step 3: Insert half=2 siblings for rows missing one
    conn.execute(
        sa.text("""
        INSERT INTO block_assignments (
            id, block_number, academic_year, academic_block_id,
            resident_id, rotation_template_id, block_half,
            assignment_reason, notes, created_by, created_at, updated_at
        )
        SELECT
            gen_random_uuid(),
            ba.block_number, ba.academic_year, ba.academic_block_id,
            ba.resident_id, ba.rotation_template_id, 2,
            ba.assignment_reason, ba.notes,
            ba.created_by, ba.created_at, now()
        FROM block_assignments ba
        WHERE ba.block_half = 1
          AND NOT EXISTS (
              SELECT 1 FROM block_assignments ba2
              WHERE ba2.block_number = ba.block_number
                AND ba2.academic_year = ba.academic_year
                AND ba2.resident_id = ba.resident_id
                AND ba2.block_half = 2
          )
        """)
    )

    # Step 4: Re-link HDAs for second-half dates to new half=2 rows
    conn.execute(
        sa.text("""
        UPDATE half_day_assignments AS hda
        SET block_assignment_id = h2.id
        FROM block_assignments h1
        JOIN block_assignments h2
            ON h2.block_half = 2
           AND h2.block_number = h1.block_number
           AND h2.academic_year = h1.academic_year
           AND h2.resident_id = h1.resident_id
        JOIN academic_blocks ab
            ON ab.block_number = h1.block_number
           AND ab.academic_year = h1.academic_year
        WHERE hda.block_assignment_id = h1.id
          AND h1.block_half = 1
          AND hda.person_id = h1.resident_id
          AND hda.date >= ab.start_date + INTERVAL '14 days'
        """)
    )

    # Step 5: Drop old partial unique indexes
    op.drop_index("uq_resident_block_full", "block_assignments", if_exists=True)
    op.drop_index("uq_resident_block_half", "block_assignments", if_exists=True)

    # Step 6: Drop old CHECK constraint
    op.drop_constraint("check_block_half_range", "block_assignments", type_="check")

    # Step 7: ALTER COLUMN block_half SET NOT NULL
    op.alter_column(
        "block_assignments",
        "block_half",
        existing_type=sa.SmallInteger(),
        nullable=False,
    )

    # Step 8: New CHECK constraint
    op.create_check_constraint(
        "check_block_half_range",
        "block_assignments",
        "block_half IN (1, 2)",
    )

    # Step 9: New unique index (non-partial)
    op.create_index(
        "uq_resident_block_half",
        "block_assignments",
        ["block_number", "academic_year", "resident_id", "block_half"],
        unique=True,
    )


def downgrade() -> None:
    conn = op.get_bind()

    # Step 1: Drop new unique index
    op.drop_index("uq_resident_block_half", "block_assignments", if_exists=True)

    # Step 2: Drop new CHECK constraint
    op.drop_constraint("check_block_half_range", "block_assignments", type_="check")

    # Step 3: Allow NULLs again
    op.alter_column(
        "block_assignments",
        "block_half",
        existing_type=sa.SmallInteger(),
        nullable=True,
    )

    # Step 4: Restore old CHECK constraint
    op.create_check_constraint(
        "check_block_half_range",
        "block_assignments",
        "block_half IS NULL OR block_half IN (1, 2)",
    )

    # Step 5: Re-link HDAs — point second-half HDAs back to the half=1 row
    # (which will become the full-block row after merge)
    conn.execute(
        sa.text("""
        UPDATE half_day_assignments AS hda
        SET block_assignment_id = h1.id
        FROM block_assignments h2
        JOIN block_assignments h1
            ON h1.block_half = 1
           AND h1.block_number = h2.block_number
           AND h1.academic_year = h2.academic_year
           AND h1.resident_id = h2.resident_id
        WHERE hda.block_assignment_id = h2.id
          AND h2.block_half = 2
          AND h2.rotation_template_id = h1.rotation_template_id
        """)
    )

    # Step 6: Merge paired identical-template rows back to NULL
    # Delete the half=2 copy, set half=1 back to NULL
    conn.execute(
        sa.text("""
        DELETE FROM block_assignments ba2
        USING block_assignments ba1
        WHERE ba2.block_half = 2
          AND ba1.block_half = 1
          AND ba1.block_number = ba2.block_number
          AND ba1.academic_year = ba2.academic_year
          AND ba1.resident_id = ba2.resident_id
          AND ba1.rotation_template_id = ba2.rotation_template_id
        """)
    )
    conn.execute(
        sa.text("""
        UPDATE block_assignments
        SET block_half = NULL
        WHERE block_half = 1
          AND NOT EXISTS (
              SELECT 1 FROM block_assignments ba2
              WHERE ba2.block_number = block_assignments.block_number
                AND ba2.academic_year = block_assignments.academic_year
                AND ba2.resident_id = block_assignments.resident_id
                AND ba2.block_half = 2
          )
        """)
    )

    # Step 7: Recreate partial unique indexes
    op.create_index(
        "uq_resident_block_full",
        "block_assignments",
        ["block_number", "academic_year", "resident_id"],
        unique=True,
        postgresql_where=sa.text("block_half IS NULL"),
    )
    op.create_index(
        "uq_resident_block_half",
        "block_assignments",
        ["block_number", "academic_year", "resident_id", "block_half"],
        unique=True,
        postgresql_where=sa.text("block_half IS NOT NULL"),
    )

    # Step 8: Recreate trigger + function
    conn.execute(
        sa.text("""
        CREATE OR REPLACE FUNCTION check_block_half_exclusion()
        RETURNS TRIGGER AS $$
        BEGIN
            IF NEW.block_half IS NULL THEN
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
        """)
    )
    conn.execute(
        sa.text("""
        CREATE TRIGGER trg_block_half_exclusion
        BEFORE INSERT OR UPDATE ON block_assignments
        FOR EACH ROW EXECUTE FUNCTION check_block_half_exclusion();
        """)
    )
