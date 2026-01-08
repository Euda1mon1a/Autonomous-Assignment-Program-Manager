"""Add is_away_from_program to absences.

Revision ID: 20260108_add_away_prog
Revises: 20260108_add_tmpl_cat
Create Date: 2026-01-08

Tracks time away from program for training extension threshold:
- Residents: TRUE for all absence types (28-day max per academic year)
- Faculty: FALSE (no away-from-program tracking for faculty)
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260108_add_away_prog"
down_revision = "20260108_add_tmpl_cat"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add is_away_from_program column with default TRUE
    # (Will be corrected for faculty in backfill)
    op.add_column(
        "absences",
        sa.Column(
            "is_away_from_program",
            sa.Boolean(),
            nullable=False,
            server_default="true",
        ),
    )

    # Backfill: Faculty absences should be FALSE
    # Residents (and all others) should be TRUE
    op.execute("""
        UPDATE absences a
        SET is_away_from_program = CASE
            WHEN p.role = 'faculty' THEN FALSE
            ELSE TRUE
        END
        FROM people p
        WHERE a.person_id = p.id
    """)

    # Remove server default after backfill
    op.alter_column(
        "absences",
        "is_away_from_program",
        server_default=None,
    )


def downgrade() -> None:
    op.drop_column("absences", "is_away_from_program")
