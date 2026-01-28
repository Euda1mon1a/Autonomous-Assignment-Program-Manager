"""Normalize rotation_type to inpatient/outpatient for rotation templates.

Revision ID: 20260127_normalize_rotation_type_outpatient
Revises: 20260126_add_fmc_capacity_flag
Create Date: 2026-01-27
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "20260127_normalize_rotation_type_outpatient"
down_revision = "20260126_add_fmc_capacity_flag"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE rotation_templates
        SET rotation_type = 'outpatient'
        WHERE template_category = 'rotation'
          AND rotation_type IN ('procedures', 'procedure', 'clinic');
        """
    )


def downgrade() -> None:
    # Best-effort rollback: only restore procedures when explicitly required.
    op.execute(
        """
        UPDATE rotation_templates
        SET rotation_type = 'procedures'
        WHERE template_category = 'rotation'
          AND rotation_type = 'outpatient'
          AND requires_procedure_credential = true;
        """
    )
