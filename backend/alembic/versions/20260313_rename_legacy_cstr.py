"""Rename legacy constraint_configurations rows to match ConstraintManager names.

Revision ID: 20260313_rename_legacy_cstr
Revises: 20260313_task_hist_4cols
Create Date: 2026-03-13
"""

from alembic import op

revision = "20260313_rename_legacy_cstr"
down_revision = "20260313_task_hist_4cols"
branch_labels = None
depends_on = None

RENAMES = {
    "EightyHourRule": "80HourRule",
    "OneInSevenRule": "1in7Rule",
    "OnePersonPerBlock": "ResidentInpatientHeadcount",
}


def upgrade() -> None:
    for old_name, new_name in RENAMES.items():
        op.execute(
            f"UPDATE constraint_configurations SET name = '{new_name}' "
            f"WHERE name = '{old_name}'"
        )


def downgrade() -> None:
    for old_name, new_name in RENAMES.items():
        op.execute(
            f"UPDATE constraint_configurations SET name = '{old_name}' "
            f"WHERE name = '{new_name}'"
        )
