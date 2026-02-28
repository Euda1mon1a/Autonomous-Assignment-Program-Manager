"""Add 'adjunct' to faculty_role CHECK constraint and classify faculty.

Revision ID: 20260227_add_adjunct
Revises: 8b9cea518229
Create Date: 2026-02-27
"""

from alembic import op

revision = "20260227_add_adjunct"
down_revision = "8b9cea518229"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Drop old CHECK constraint and add new one with 'adjunct'
    op.execute(
        "ALTER TABLE people DROP CONSTRAINT IF EXISTS ck_people_check_faculty_role"
    )
    op.execute(
        """
        ALTER TABLE people ADD CONSTRAINT ck_people_check_faculty_role
        CHECK (
            faculty_role IS NULL
            OR faculty_role IN ('pd','apd','oic','dept_chief','sports_med','core','adjunct')
        )
        """
    )

    # 2. Classify known adjunct faculty
    op.execute(
        "UPDATE people SET faculty_role = 'adjunct' "
        "WHERE name IN ('Lisa Gomes', 'Anne Lamoureux') AND type = 'faculty'"
    )

    # 3. Backfill remaining NULL-role faculty as 'core' (excluding placeholders + Bohringer)
    op.execute(
        "UPDATE people SET faculty_role = 'core' "
        "WHERE type = 'faculty' AND faculty_role IS NULL "
        "AND name NOT LIKE 'Dr. Faculty-%%' AND name != 'Kate Bohringer'"
    )

    # 4. Insert Collette Ching as adjunct faculty
    op.execute(
        "INSERT INTO people (id, name, type, faculty_role, created_at, updated_at) "
        "VALUES (gen_random_uuid(), 'Collette Ching', 'faculty', 'adjunct', NOW(), NOW())"
    )


def downgrade() -> None:
    # Remove Collette Ching
    op.execute("DELETE FROM people WHERE name = 'Collette Ching' AND type = 'faculty'")

    # Revert adjunct → NULL
    op.execute(
        "UPDATE people SET faculty_role = NULL "
        "WHERE faculty_role = 'adjunct' AND type = 'faculty'"
    )

    # Revert backfilled core → NULL for previously-NULL faculty
    # (Can't perfectly reverse, but safe since NULL was already valid)
    op.execute(
        "UPDATE people SET faculty_role = NULL "
        "WHERE type = 'faculty' AND faculty_role = 'core' "
        "AND name IN ('Blake Van Brunt', 'Derrick Thiel', 'Joseph Napierala', 'Kyle Samblanet')"
    )

    # Restore old CHECK constraint without 'adjunct'
    op.execute(
        "ALTER TABLE people DROP CONSTRAINT IF EXISTS ck_people_check_faculty_role"
    )
    op.execute(
        """
        ALTER TABLE people ADD CONSTRAINT ck_people_check_faculty_role
        CHECK (
            faculty_role IS NULL
            OR faculty_role IN ('pd','apd','oic','dept_chief','sports_med','core')
        )
        """
    )
