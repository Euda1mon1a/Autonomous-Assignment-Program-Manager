"""Add is_block_half_rotation to rotation_templates

Revision ID: 9d38e1388001
Revises: 20251222_fix_schema
Create Date: 2025-12-22 23:35:47.656701

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9d38e1388001"
down_revision: str | None = "20251222_fix_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add is_block_half_rotation column for split rotations like Night Float
    op.add_column(
        "rotation_templates",
        sa.Column(
            "is_block_half_rotation",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
    )


def downgrade() -> None:
    op.drop_column("rotation_templates", "is_block_half_rotation")
