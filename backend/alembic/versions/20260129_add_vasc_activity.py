"""Add VASC activity for vasectomy counseling.

Revision ID: 20260129_add_vasc_activity
Revises: 20260127_add_activity_capacity_units
Create Date: 2026-01-29
"""

import uuid
from datetime import datetime

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260129_add_vasc_activity"
down_revision = "20260127_add_activity_capacity_units"
branch_labels = None
depends_on = None


def upgrade() -> None:
    now = datetime.utcnow().isoformat()
    activity_id = str(uuid.uuid4())
    op.execute(
        sa.text(
            """
            INSERT INTO activities (
                id,
                code,
                display_abbreviation,
                name,
                activity_category,
                requires_supervision,
                is_protected,
                counts_toward_clinical_hours,
                provides_supervision,
                counts_toward_physical_capacity,
                capacity_units,
                display_order,
                is_archived,
                created_at,
                updated_at
            ) VALUES (
                :id,
                :code,
                :abbrev,
                :name,
                :category,
                :requires_supervision,
                :is_protected,
                :counts_clinical,
                :provides_supervision,
                :counts_physical,
                :capacity_units,
                :display_order,
                :is_archived,
                :created_at,
                :updated_at
            )
            ON CONFLICT (code) DO NOTHING
            """
        ).bindparams(
            id=activity_id,
            code="VASC",
            abbrev="VASC",
            name="Vasectomy Counseling",
            category="clinical",
            requires_supervision=True,
            is_protected=False,
            counts_clinical=True,
            provides_supervision=False,
            counts_physical=True,
            capacity_units=1,
            display_order=0,
            is_archived=False,
            created_at=now,
            updated_at=now,
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text("DELETE FROM activities WHERE code = :code").bindparams(code="VASC")
    )
