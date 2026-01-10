"""Add procedure credentialing tables

Revision ID: 007
Revises: 006
Create Date: 2025-12-16 00:00:00.000000

Creates tables for procedure credentialing system:
- procedures: Medical procedures that require credentialed supervision
- procedure_credentials: Faculty credentials for specific procedures
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "007"
down_revision: str | None = "006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create procedure credentialing tables."""

    # Table 1: procedures
    # Defines medical procedures that require credentialed supervision
    op.create_table(
        "procedures",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False, unique=True),
        sa.Column("description", sa.Text()),
        # Categorization
        sa.Column(
            "category", sa.String(100)
        ),  # 'surgical', 'office', 'obstetric', 'clinic'
        sa.Column(
            "specialty", sa.String(100)
        ),  # 'Sports Medicine', 'OB/GYN', 'Dermatology'
        # Supervision requirements
        sa.Column(
            "supervision_ratio", sa.Integer(), server_default="1"
        ),  # Max residents per faculty
        sa.Column("requires_certification", sa.Boolean(), server_default="true"),
        # Complexity/training
        sa.Column("complexity_level", sa.String(50), server_default="'standard'"),
        sa.Column("min_pgy_level", sa.Integer(), server_default="1"),
        # Status
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        # Timestamps
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
        # Constraints
        sa.CheckConstraint(
            "complexity_level IN ('basic', 'standard', 'advanced', 'complex')",
            name="check_complexity_level",
        ),
        sa.CheckConstraint(
            "min_pgy_level BETWEEN 1 AND 3", name="check_procedure_pgy_level"
        ),
        sa.CheckConstraint("supervision_ratio >= 1", name="check_supervision_ratio"),
    )
    op.create_index("idx_procedures_name", "procedures", ["name"])
    op.create_index("idx_procedures_specialty", "procedures", ["specialty"])
    op.create_index("idx_procedures_category", "procedures", ["category"])
    op.create_index("idx_procedures_active", "procedures", ["is_active"])

    # Table 2: procedure_credentials
    # Links faculty to procedures they are credentialed to supervise
    op.create_table(
        "procedure_credentials",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        # Foreign keys
        sa.Column(
            "person_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "procedure_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("procedures.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # Credential status
        sa.Column("status", sa.String(50), nullable=False, server_default="'active'"),
        # Competency level
        sa.Column("competency_level", sa.String(50), server_default="'qualified'"),
        # Dates
        sa.Column("issued_date", sa.Date(), server_default=sa.func.current_date()),
        sa.Column("expiration_date", sa.Date()),  # NULL = no expiration
        sa.Column("last_verified_date", sa.Date()),
        # Supervision capacity (overrides procedure defaults)
        sa.Column(
            "max_concurrent_residents", sa.Integer()
        ),  # NULL uses procedure default
        sa.Column("max_per_week", sa.Integer()),  # NULL = unlimited
        sa.Column("max_per_academic_year", sa.Integer()),  # NULL = unlimited
        # Notes
        sa.Column("notes", sa.Text()),
        # Timestamps
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
        # Constraints
        sa.UniqueConstraint(
            "person_id", "procedure_id", name="uq_person_procedure_credential"
        ),
        sa.CheckConstraint(
            "status IN ('active', 'expired', 'suspended', 'pending')",
            name="check_credential_status",
        ),
        sa.CheckConstraint(
            "competency_level IN ('trainee', 'qualified', 'expert', 'master')",
            name="check_competency_level",
        ),
    )
    op.create_index("idx_credentials_person", "procedure_credentials", ["person_id"])
    op.create_index(
        "idx_credentials_procedure", "procedure_credentials", ["procedure_id"]
    )
    op.create_index("idx_credentials_status", "procedure_credentials", ["status"])
    op.create_index(
        "idx_credentials_expiration", "procedure_credentials", ["expiration_date"]
    )


def downgrade() -> None:
    """Drop procedure credentialing tables in reverse order."""
    op.drop_table("procedure_credentials")
    op.drop_table("procedures")
