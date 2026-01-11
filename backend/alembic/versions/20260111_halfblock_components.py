"""Add half-block component template references

Revision ID: 20260111_halfblock_components
Revises: 20260110_feature_flags
Create Date: 2026-01-11

Half-block rotations (NF+Endo, NEURO+NF) inherit leave eligibility
from their component templates. This enables checking leave eligibility
based on which half of the block the requested leave falls in.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260111_halfblock_components"
down_revision: str | None = "20260110_feature_flags"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add component template references for half-block rotations
    op.add_column(
        "rotation_templates",
        sa.Column(
            "first_half_component_id", postgresql.UUID(as_uuid=True), nullable=True
        ),
    )
    op.add_column(
        "rotation_templates",
        sa.Column(
            "second_half_component_id", postgresql.UUID(as_uuid=True), nullable=True
        ),
    )

    # Add foreign key constraints
    op.create_foreign_key(
        "fk_rotation_first_half_component",
        "rotation_templates",
        "rotation_templates",
        ["first_half_component_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_rotation_second_half_component",
        "rotation_templates",
        "rotation_templates",
        ["second_half_component_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Add index for efficient lookups
    op.create_index(
        "ix_rotation_templates_half_components",
        "rotation_templates",
        ["first_half_component_id", "second_half_component_id"],
        postgresql_where=sa.text("is_block_half_rotation = true"),
    )


def downgrade() -> None:
    op.drop_index("ix_rotation_templates_half_components", "rotation_templates")
    op.drop_constraint(
        "fk_rotation_second_half_component", "rotation_templates", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_rotation_first_half_component", "rotation_templates", type_="foreignkey"
    )
    op.drop_column("rotation_templates", "second_half_component_id")
    op.drop_column("rotation_templates", "first_half_component_id")
