"""Archive unused /NF canonical templates.

These 8 templates (CARDIO/NF, DERM/NF, etc.) were created by a stale
migration that was never committed. They have zero FK references in
block_assignments, assignments, or half_day_assignments.

Revision ID: 20260312_archive_slash_nf
Revises: 20260312_drop_secondary_rot
Create Date: 2026-03-12
"""

import sqlalchemy as sa
from alembic import op

revision = "20260312_archive_slash_nf"
down_revision = "20260312_drop_secondary_rot"
branch_labels = None
depends_on = None

_SLASH_NF_ABBREVS = [
    "CARDIO/NF",
    "DERM/NF",
    "ENDO/NF",
    "MED/NF",
    "NICU/NF",
    "NEURO/NF",
    "PEDSW/NF",
    "L&D/NF",
]


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text("""
        UPDATE rotation_templates SET is_archived = true
        WHERE abbreviation = ANY(:abbrevs)
          AND NOT is_archived
        """),
        {"abbrevs": _SLASH_NF_ABBREVS},
    )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text("""
        UPDATE rotation_templates SET is_archived = false
        WHERE abbreviation = ANY(:abbrevs)
          AND is_archived
        """),
        {"abbrevs": _SLASH_NF_ABBREVS},
    )
