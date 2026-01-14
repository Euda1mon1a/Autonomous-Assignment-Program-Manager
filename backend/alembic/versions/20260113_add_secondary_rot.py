"""Add secondary_rotation_template_id for mid-block transitions.

Revision ID: 20260113_add_secondary_rot
Revises: 20260113_fix_req_hash
Create Date: 2026-01-13

Supports residents who switch rotations mid-block (e.g., NEURO weeks 1-2, NF weeks 3-4).
Column 1 in Excel = primary rotation, Column 2 = secondary rotation.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260113_add_secondary_rot"
down_revision = "20260113_fix_req_hash"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add secondary_rotation_template_id to block_assignments."""
    op.add_column(
        "block_assignments",
        sa.Column(
            "secondary_rotation_template_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("rotation_templates.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )

    # Add index for the new FK
    op.create_index(
        "ix_block_assignments_secondary_rotation",
        "block_assignments",
        ["secondary_rotation_template_id"],
    )


def downgrade() -> None:
    """Remove secondary_rotation_template_id."""
    op.drop_index("ix_block_assignments_secondary_rotation", "block_assignments")
    op.drop_column("block_assignments", "secondary_rotation_template_id")
