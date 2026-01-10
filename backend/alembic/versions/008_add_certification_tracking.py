"""Add certification tracking tables

Revision ID: 008
Revises: 007
Create Date: 2025-12-16 00:00:00.000000

Creates tables for tracking personnel certifications (BLS, ACLS, PALS, etc.)
with automatic expiration reminder support:
- certification_types: Defines certification types with renewal periods
- person_certifications: Tracks individual certifications with expiration dates
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "008"
down_revision: str | None = "007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create certification tracking tables."""

    # Table 1: certification_types
    # Defines the types of certifications (BLS, ACLS, PALS, etc.)
    op.create_table(
        "certification_types",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("full_name", sa.String(255)),
        sa.Column("description", sa.Text()),
        # Renewal configuration
        sa.Column("renewal_period_months", sa.Integer(), server_default="24"),
        # Who needs this certification
        sa.Column("required_for_residents", sa.Boolean(), server_default="true"),
        sa.Column("required_for_faculty", sa.Boolean(), server_default="true"),
        sa.Column("required_for_specialties", sa.String(500)),
        # Reminder configuration (days before expiration)
        sa.Column("reminder_days_180", sa.Boolean(), server_default="true"),
        sa.Column("reminder_days_90", sa.Boolean(), server_default="true"),
        sa.Column("reminder_days_30", sa.Boolean(), server_default="true"),
        sa.Column("reminder_days_14", sa.Boolean(), server_default="true"),
        sa.Column("reminder_days_7", sa.Boolean(), server_default="true"),
        # Status
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        # Timestamps
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("idx_cert_types_name", "certification_types", ["name"])
    op.create_index("idx_cert_types_active", "certification_types", ["is_active"])

    # Table 2: person_certifications
    # Tracks individual certifications for each person
    op.create_table(
        "person_certifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        # Foreign keys
        sa.Column(
            "person_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "certification_type_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("certification_types.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # Certification details
        sa.Column("certification_number", sa.String(100)),
        sa.Column("issued_date", sa.Date(), nullable=False),
        sa.Column("expiration_date", sa.Date(), nullable=False),
        # Status
        sa.Column("status", sa.String(50), server_default="'current'"),
        # Verification
        sa.Column("verified_by", sa.String(255)),
        sa.Column("verified_date", sa.Date()),
        sa.Column("document_url", sa.String(500)),
        # Reminder tracking (timestamps when sent)
        sa.Column("reminder_180_sent", sa.DateTime()),
        sa.Column("reminder_90_sent", sa.DateTime()),
        sa.Column("reminder_30_sent", sa.DateTime()),
        sa.Column("reminder_14_sent", sa.DateTime()),
        sa.Column("reminder_7_sent", sa.DateTime()),
        # Notes
        sa.Column("notes", sa.Text()),
        # Timestamps
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
        # Constraints
        sa.UniqueConstraint(
            "person_id", "certification_type_id", name="uq_person_certification_type"
        ),
        sa.CheckConstraint(
            "status IN ('current', 'expiring_soon', 'expired', 'pending')",
            name="check_cert_status",
        ),
    )
    op.create_index("idx_person_certs_person", "person_certifications", ["person_id"])
    op.create_index(
        "idx_person_certs_type", "person_certifications", ["certification_type_id"]
    )
    op.create_index(
        "idx_person_certs_expiration", "person_certifications", ["expiration_date"]
    )
    op.create_index("idx_person_certs_status", "person_certifications", ["status"])

    # Insert default certification types
    op.execute("""
        INSERT INTO certification_types (id, name, full_name, description, renewal_period_months, required_for_residents, required_for_faculty)
        VALUES
        (gen_random_uuid(), 'BLS', 'Basic Life Support', 'CPR and basic emergency cardiovascular care', 24, true, true),
        (gen_random_uuid(), 'ACLS', 'Advanced Cardiovascular Life Support', 'Advanced emergency cardiovascular care for healthcare providers', 24, true, true),
        (gen_random_uuid(), 'PALS', 'Pediatric Advanced Life Support', 'Emergency assessment and treatment of pediatric patients', 24, true, true),
        (gen_random_uuid(), 'ALSO', 'Advanced Life Support in Obstetrics', 'Management of obstetric emergencies', 24, false, false),
        (gen_random_uuid(), 'NRP', 'Neonatal Resuscitation Program', 'Resuscitation of newborns', 24, false, false)
    """)


def downgrade() -> None:
    """Drop certification tracking tables."""
    op.drop_table("person_certifications")
    op.drop_table("certification_types")
