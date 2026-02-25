"""Create person_academic_years table and seed from Person.pgy_level.

Revision ID: 20260224_person_ay
Revises: 20260224_annual_batch
Create Date: 2026-02-24 12:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260224_person_ay"
down_revision = "20260224_annual_batch"
branch_labels = None
depends_on = None


def upgrade():
    # Create person_academic_years table
    op.create_table(
        "person_academic_years",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "person_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("academic_year", sa.Integer(), nullable=False, index=True),
        sa.Column("pgy_level", sa.Integer(), nullable=True),
        sa.Column("is_graduated", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("clinic_min", sa.Integer(), nullable=True),
        sa.Column("clinic_max", sa.Integer(), nullable=True),
        sa.Column(
            "sunday_call_count", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column(
            "weekday_call_count", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column("fmit_weeks_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "person_id", "academic_year", name="uq_person_academic_year"
        ),
        sa.CheckConstraint(
            "pgy_level IS NULL OR pgy_level BETWEEN 1 AND 3",
            name="check_ay_pgy_level",
        ),
    )

    # Seed from current Person.pgy_level for AY 2025 (current academic year)
    # Uses raw SQL to insert one PersonAcademicYear per resident
    op.execute(
        """
        INSERT INTO person_academic_years (id, person_id, academic_year, pgy_level, is_graduated)
        SELECT
            gen_random_uuid(),
            p.id,
            2025,
            p.pgy_level,
            false
        FROM people p
        WHERE p.type = 'resident'
          AND p.pgy_level IS NOT NULL
        """
    )


def downgrade():
    op.drop_table("person_academic_years")
