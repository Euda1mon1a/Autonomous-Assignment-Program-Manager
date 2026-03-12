"""Drop 5 dead columns from rotation_templates.

These columns were added by the GUI experiment migration (20251230) but
never referenced in the ORM model or any scheduling logic. They are
DB-only ghosts.

Revision ID: 20260311_drop_dead_rot_cols
Revises: 07e395bd6a1f
Create Date: 2026-03-11
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260311_drop_dead_rot_cols"
down_revision: str = "07e395bd6a1f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_column("rotation_templates", "pattern_type")
    op.drop_column("rotation_templates", "setting_type")
    op.drop_column("rotation_templates", "paired_template_id")
    op.drop_column("rotation_templates", "split_day")
    op.drop_column("rotation_templates", "is_mirror_primary")


def downgrade() -> None:
    op.add_column(
        "rotation_templates",
        sa.Column(
            "is_mirror_primary",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )
    op.add_column(
        "rotation_templates",
        sa.Column("split_day", sa.Integer(), nullable=True),
    )
    op.add_column(
        "rotation_templates",
        sa.Column("paired_template_id", sa.dialects.postgresql.UUID(), nullable=True),
    )
    op.add_column(
        "rotation_templates",
        sa.Column(
            "setting_type",
            sa.String(length=20),
            nullable=False,
            server_default=sa.text("'outpatient'"),
        ),
    )
    op.add_column(
        "rotation_templates",
        sa.Column(
            "pattern_type",
            sa.String(length=20),
            nullable=False,
            server_default=sa.text("'regular'"),
        ),
    )
