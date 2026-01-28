"""Add FMC capacity flag to half-day assignments.

Revision ID: 20260126_add_fmc_capacity_flag
Revises: 20260126_rename_rotation_type
Create Date: 2026-01-26
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260126_add_fmc_capacity_flag"
down_revision = "20260126_rename_rotation_type"
branch_labels = None
depends_on = None


FMC_CODES = [
    "C",
    "C-N",
    "C-I",
    "FM_CLINIC",
    "V1",
    "V2",
    "V3",
    "PROC",
    "PR",
    "PROCEDURE",
    "VAS",
    "SM",
    "SM_CLINIC",
    "ASM",
]


def upgrade() -> None:
    op.add_column(
        "half_day_assignments",
        sa.Column(
            "counts_toward_fmc_capacity",
            sa.Boolean(),
            nullable=True,
        ),
    )

    codes = ", ".join([f"'{code}'" for code in FMC_CODES])
    op.execute(
        f"""
        UPDATE half_day_assignments h
        SET counts_toward_fmc_capacity = true
        FROM activities a
        WHERE h.activity_id = a.id
          AND UPPER(a.code) IN ({codes});
        """
    )


def downgrade() -> None:
    op.drop_column("half_day_assignments", "counts_toward_fmc_capacity")
