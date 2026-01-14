"""Add faculty constraint columns to people table.

Revision ID: 20260114_faculty_constraints
Revises: 20260113_add_secondary_rot, 20260113_approval_chain
Create Date: 2026-01-14

This migration adds columns to store faculty scheduling constraints
directly in the database (belt & suspenders approach).

Columns:
- clinic_min/max: Weekly clinic half-day limits
- at_min/max: Attending/supervision limits per block
- gme_min/max: GME admin half-day limits
- dfm_min/max: DFM admin half-day limits
- admin_type: Type of admin time (GME, DFM, SM)
- is_sm_faculty: Sports Medicine faculty flag
- has_split_admin: Split GME/DFM admin (e.g., Dahl)
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260114_faculty_constraints"
down_revision = ("20260113_add_secondary_rot", "20260113_approval_chain")
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add constraint columns to people table
    op.add_column("people", sa.Column("clinic_min", sa.Integer(), nullable=True))
    op.add_column("people", sa.Column("clinic_max", sa.Integer(), nullable=True))
    op.add_column("people", sa.Column("at_min", sa.Integer(), nullable=True))
    op.add_column("people", sa.Column("at_max", sa.Integer(), nullable=True))
    op.add_column("people", sa.Column("gme_min", sa.Integer(), nullable=True))
    op.add_column("people", sa.Column("gme_max", sa.Integer(), nullable=True))
    op.add_column("people", sa.Column("dfm_min", sa.Integer(), nullable=True))
    op.add_column("people", sa.Column("dfm_max", sa.Integer(), nullable=True))
    op.add_column("people", sa.Column("admin_type", sa.String(10), nullable=True))
    op.add_column(
        "people",
        sa.Column("is_sm_faculty", sa.Boolean(), nullable=True, server_default="false"),
    )
    op.add_column(
        "people",
        sa.Column(
            "has_split_admin", sa.Boolean(), nullable=True, server_default="false"
        ),
    )

    # Seed constraint data for existing faculty
    # Using raw SQL for data migration
    op.execute("""
        UPDATE people SET
            clinic_min = 0, clinic_max = 0,
            at_min = 1, at_max = 1,
            gme_min = 0, gme_max = 0,
            dfm_min = 0, dfm_max = 0,
            admin_type = 'GME',
            is_sm_faculty = false,
            has_split_admin = false
        WHERE name ILIKE '%Bevis%' AND type = 'faculty';
    """)

    op.execute("""
        UPDATE people SET
            clinic_min = 2, clinic_max = 4,
            at_min = 1, at_max = 3,
            gme_min = 2, gme_max = 3,
            dfm_min = 0, dfm_max = 0,
            admin_type = 'GME',
            is_sm_faculty = false,
            has_split_admin = false
        WHERE name ILIKE '%Kinkennon%' AND type = 'faculty';
    """)

    op.execute("""
        UPDATE people SET
            clinic_min = 2, clinic_max = 4,
            at_min = 1, at_max = 3,
            gme_min = 2, gme_max = 3,
            dfm_min = 0, dfm_max = 0,
            admin_type = 'GME',
            is_sm_faculty = false,
            has_split_admin = false
        WHERE name ILIKE '%LaBounty%' AND type = 'faculty';
    """)

    op.execute("""
        UPDATE people SET
            clinic_min = 2, clinic_max = 4,
            at_min = 1, at_max = 3,
            gme_min = 2, gme_max = 3,
            dfm_min = 0, dfm_max = 0,
            admin_type = 'GME',
            is_sm_faculty = false,
            has_split_admin = false
        WHERE name ILIKE '%McRae%' AND type = 'faculty';
    """)

    op.execute("""
        UPDATE people SET
            clinic_min = 2, clinic_max = 4,
            at_min = 1, at_max = 3,
            gme_min = 2, gme_max = 3,
            dfm_min = 0, dfm_max = 0,
            admin_type = 'GME',
            is_sm_faculty = false,
            has_split_admin = false
        WHERE name ILIKE '%Colgan%' AND type = 'faculty';
    """)

    op.execute("""
        UPDATE people SET
            clinic_min = 2, clinic_max = 4,
            at_min = 1, at_max = 3,
            gme_min = 2, gme_max = 3,
            dfm_min = 0, dfm_max = 0,
            admin_type = 'GME',
            is_sm_faculty = false,
            has_split_admin = false
        WHERE name ILIKE '%Chu%' AND type = 'faculty';
    """)

    op.execute("""
        UPDATE people SET
            clinic_min = 1, clinic_max = 2,
            at_min = 1, at_max = 3,
            gme_min = 3, gme_max = 4,
            dfm_min = 0, dfm_max = 0,
            admin_type = 'GME',
            is_sm_faculty = false,
            has_split_admin = false
        WHERE name ILIKE '%Montgomery%' AND type = 'faculty';
    """)

    op.execute("""
        UPDATE people SET
            clinic_min = 1, clinic_max = 2,
            at_min = 1, at_max = 3,
            gme_min = 1, gme_max = 2,
            dfm_min = 0, dfm_max = 0,
            admin_type = 'GME',
            is_sm_faculty = false,
            has_split_admin = true
        WHERE name ILIKE '%Dahl%' AND type = 'faculty';
    """)

    op.execute("""
        UPDATE people SET
            clinic_min = 1, clinic_max = 1,
            at_min = 1, at_max = 1,
            gme_min = 0, gme_max = 0,
            dfm_min = 0, dfm_max = 0,
            admin_type = 'DFM',
            is_sm_faculty = false,
            has_split_admin = false
        WHERE name ILIKE '%McGuire%' AND type = 'faculty';
    """)

    op.execute("""
        UPDATE people SET
            clinic_min = 0, clinic_max = 0,
            at_min = 1, at_max = 3,
            gme_min = 0, gme_max = 0,
            dfm_min = 0, dfm_max = 0,
            admin_type = 'SM',
            is_sm_faculty = true,
            has_split_admin = false
        WHERE name ILIKE '%Tagawa%' AND type = 'faculty';
    """)

    # Adjuncts: all zeros, manual only
    op.execute("""
        UPDATE people SET
            clinic_min = 0, clinic_max = 0,
            at_min = 0, at_max = 0,
            gme_min = 0, gme_max = 0,
            dfm_min = 0, dfm_max = 0,
            admin_type = 'GME',
            is_sm_faculty = false,
            has_split_admin = false
        WHERE faculty_role = 'adjunct' AND type = 'faculty';
    """)


def downgrade() -> None:
    op.drop_column("people", "has_split_admin")
    op.drop_column("people", "is_sm_faculty")
    op.drop_column("people", "admin_type")
    op.drop_column("people", "dfm_max")
    op.drop_column("people", "dfm_min")
    op.drop_column("people", "gme_max")
    op.drop_column("people", "gme_min")
    op.drop_column("people", "at_max")
    op.drop_column("people", "at_min")
    op.drop_column("people", "clinic_max")
    op.drop_column("people", "clinic_min")
