"""Add rotation_halfday_requirements table.

Revision ID: 020_rotation_halfday
Revises: 20251219_add_template_id_to_email_logs
Create Date: 2025-12-21 14:00:00

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "020_rotation_halfday"
down_revision = "20251219_add_template_id_to_email_logs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create rotation_halfday_requirements table."""
    op.create_table(
        "rotation_halfday_requirements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "rotation_template_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("rotation_templates.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # Activity breakdown per block
        sa.Column("fm_clinic_halfdays", sa.Integer, default=4, nullable=False),
        sa.Column("specialty_halfdays", sa.Integer, default=5, nullable=False),
        sa.Column("specialty_name", sa.String(255)),
        sa.Column("academics_halfdays", sa.Integer, default=1, nullable=False),
        sa.Column("elective_halfdays", sa.Integer, default=0),
        # Constraints and preferences
        sa.Column("min_consecutive_specialty", sa.Integer, default=1),
        sa.Column("prefer_combined_clinic_days", sa.Boolean, default=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )

    # Index for faster lookups
    op.create_index(
        "idx_rotation_halfday_template",
        "rotation_halfday_requirements",
        ["rotation_template_id"],
        unique=True,  # Enforce one-to-one relationship
    )


def downgrade() -> None:
    """Drop rotation_halfday_requirements table."""
    op.drop_index("idx_rotation_halfday_template")
    op.drop_table("rotation_halfday_requirements")
