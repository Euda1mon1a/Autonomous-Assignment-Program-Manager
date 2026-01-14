"""Add sm_min and sm_max columns for Sports Medicine faculty.

Revision ID: 20260114_sm_constraints
Revises: 20260114_faculty_constraints
Create Date: 2026-01-14

SM faculty (Tagawa) needs explicit min/max for SM clinic half-days.
When no resident is on SM rotation, Tagawa should have 2-4 SM half-days/week.
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260114_sm_constraints"
down_revision = "20260114_faculty_constraints"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add SM constraint columns
    op.add_column("people", sa.Column("sm_min", sa.Integer(), nullable=True))
    op.add_column("people", sa.Column("sm_max", sa.Integer(), nullable=True))

    # Seed Tagawa with SM constraints (2-4 half-days/week when no resident on SM)
    op.execute("""
        UPDATE people SET
            sm_min = 2,
            sm_max = 4
        WHERE name ILIKE '%Tagawa%' AND type = 'faculty';
    """)

    # All other faculty get 0/0 for SM
    op.execute("""
        UPDATE people SET
            sm_min = 0,
            sm_max = 0
        WHERE (name NOT ILIKE '%Tagawa%' OR name IS NULL) AND type = 'faculty';
    """)


def downgrade() -> None:
    op.drop_column("people", "sm_max")
    op.drop_column("people", "sm_min")
