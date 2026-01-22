"""Add LV-AM and LV-PM (Leave) activities for absence tracking.

Adds the LV-AM and LV-PM activity codes needed by SyncPreloadService
to mark slots where personnel are on leave/absent.

Revision ID: 20260120_add_lv_activity
Revises: 20260120_academic_blocks
Create Date: 2026-01-20
"""

import uuid
from datetime import datetime

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260120_add_lv_activity"
down_revision = "20260120_academic_blocks"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add LV-AM and LV-PM (Leave) activities."""
    now = datetime.utcnow().isoformat()

    # LV-AM (Leave - Morning)
    op.execute(
        sa.text(
            """
            INSERT INTO activities (
                id, code, display_abbreviation, name, activity_category,
                requires_supervision, is_protected, counts_toward_clinical_hours,
                provides_supervision, counts_toward_physical_capacity,
                display_order, is_archived, created_at, updated_at
            ) VALUES (
                :id, 'LV-AM', 'LV', 'Leave AM', 'time_off',
                false, true, false,
                false, false,
                205, false, :now, :now
            )
            ON CONFLICT (code) DO NOTHING
            """
        ).bindparams(id=str(uuid.uuid4()), now=now)
    )

    # LV-PM (Leave - Afternoon)
    op.execute(
        sa.text(
            """
            INSERT INTO activities (
                id, code, display_abbreviation, name, activity_category,
                requires_supervision, is_protected, counts_toward_clinical_hours,
                provides_supervision, counts_toward_physical_capacity,
                display_order, is_archived, created_at, updated_at
            ) VALUES (
                :id, 'LV-PM', 'LV', 'Leave PM', 'time_off',
                false, true, false,
                false, false,
                206, false, :now, :now
            )
            ON CONFLICT (code) DO NOTHING
            """
        ).bindparams(id=str(uuid.uuid4()), now=now)
    )


def downgrade() -> None:
    """Remove LV-AM and LV-PM activities."""
    op.execute(sa.text("DELETE FROM activities WHERE code IN ('LV-AM', 'LV-PM')"))
