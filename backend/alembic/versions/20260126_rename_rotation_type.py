"""Rename rotation_templates.activity_type to rotation_type.

Revision ID: 20260126_rename_rotation_type
Revises: 20260122_wp_act_notnull
Create Date: 2026-01-26
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260126_rename_rotation_type"
down_revision = "20260122_wp_act_notnull"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Rename activity_type column to rotation_type."""
    # Use batch alter for SQLite compatibility in tests
    with op.batch_alter_table("rotation_templates") as batch_op:
        batch_op.alter_column("activity_type", new_column_name="rotation_type")


def downgrade() -> None:
    """Revert rotation_type back to activity_type."""
    with op.batch_alter_table("rotation_templates") as batch_op:
        batch_op.alter_column("rotation_type", new_column_name="activity_type")
