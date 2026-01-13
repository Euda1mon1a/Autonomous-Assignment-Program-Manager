"""Fix rotation_activity_requirements hash mismatch.

Migration 20260109_activity_requirements used wrong hash (NAMESPACE_DNS instead
of computed hash). This migration removes those rows so they can be recreated
with the correct hash.

Revision ID: 20260113_fix_req_hash
Revises: 20260111_halfblock_components
Create Date: 2026-01-13
"""

from alembic import op

revision = "20260113_fix_req_hash"
down_revision = "20260111_day_type_cols"
branch_labels = None
depends_on = None

# Wrong hash used in 20260109_activity_requirements
# This is uuid.NAMESPACE_DNS itself, not uuid.uuid5(uuid.NAMESPACE_DNS, "all")
WRONG_HASH = "6ba7b810-9dad-11d1-80b4-00c04fd430c8"


def upgrade():
    """Delete rows with wrong hash.

    The correct hash for 'all weeks' is:
    uuid.uuid5(uuid.NAMESPACE_DNS, "all") = 5eefc5da-40d2-5afc-af3a-e7b6c2730b0d

    Rows with the wrong hash will be recreated by the application's
    auto-compute logic or by running the hybrid_model migration's INSERT
    statements again.
    """
    op.execute(
        f"""
        DELETE FROM rotation_activity_requirements
        WHERE applicable_weeks_hash = '{WRONG_HASH}'::uuid
        """
    )


def downgrade():
    """Cannot restore deleted rows - they were created with wrong hash anyway."""
    pass
