"""add_resident_weekly_requirements_table

Revision ID: 20260105_add_resident_weekly_requirements
Revises: 20260104_add_archive_fields
Create Date: 2026-01-05 00:00:00.000000

Adds resident weekly scheduling requirements model:
- Agnostic per-week half-day scheduling constraints per rotation
- FM clinic min/max requirements (ACGME: min 2 on outpatient)
- Specialty half-day requirements
- Academic time protection
- Protected slots and allowed clinic days
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision: str = "20260105_add_resident_weekly_requirements"
down_revision: str | None = "20260105_ext_ver_col"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create resident_weekly_requirements table
    op.create_table(
        "resident_weekly_requirements",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "rotation_template_id",
            UUID(as_uuid=True),
            sa.ForeignKey("rotation_templates.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # FM Clinic requirements (ACGME: min 2 on outpatient)
        sa.Column(
            "fm_clinic_min_per_week", sa.Integer(), nullable=False, server_default="2"
        ),
        sa.Column(
            "fm_clinic_max_per_week", sa.Integer(), nullable=False, server_default="3"
        ),
        # Specialty requirements
        sa.Column(
            "specialty_min_per_week", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column(
            "specialty_max_per_week", sa.Integer(), nullable=False, server_default="10"
        ),
        # Academic time
        sa.Column(
            "academics_required", sa.Boolean(), nullable=False, server_default="true"
        ),
        # JSON fields for protected slots and allowed days
        sa.Column("protected_slots", JSONB, nullable=False, server_default="{}"),
        sa.Column("allowed_clinic_days", JSONB, nullable=False, server_default="[]"),
        # Optional descriptive fields
        sa.Column("specialty_name", sa.String(255), nullable=True),
        sa.Column("description", sa.String(1024), nullable=True),
        # Timestamps
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
    )

    # Create unique constraint for one-to-one relationship
    op.create_unique_constraint(
        "uq_resident_weekly_requirement_template",
        "resident_weekly_requirements",
        ["rotation_template_id"],
    )

    # Create index on rotation_template_id for faster lookups
    op.create_index(
        "ix_resident_weekly_requirements_template_id",
        "resident_weekly_requirements",
        ["rotation_template_id"],
    )


def downgrade() -> None:
    # Drop index
    op.drop_index(
        "ix_resident_weekly_requirements_template_id",
        table_name="resident_weekly_requirements",
    )

    # Drop unique constraint
    op.drop_constraint(
        "uq_resident_weekly_requirement_template",
        "resident_weekly_requirements",
        type_="unique",
    )

    # Drop table
    op.drop_table("resident_weekly_requirements")
