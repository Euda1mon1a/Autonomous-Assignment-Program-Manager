"""Add rotation_template_id to HalfDayAssignment

Revision ID: 3b9aea05c82e
Revises: 20260312_block_half_not_null
Create Date: 2026-03-12 21:58:02.014422

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import app

# revision identifiers, used by Alembic.
revision: str = "3b9aea05c82e"
down_revision: str | None = "20260312_block_half_not_null"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "half_day_assignments",
        sa.Column(
            "rotation_template_id",
            app.db.types.GUID(),
            nullable=True,
            comment="Optional rotation template context for this assignment (enables counting clinic types)",
        ),
    )
    op.create_index(
        op.f("ix_half_day_assignments_rotation_template_id"),
        "half_day_assignments",
        ["rotation_template_id"],
        unique=False,
    )
    op.create_foreign_key(
        op.f("fk_half_day_assignments_rotation_template_id_rotation_templates"),
        "half_day_assignments",
        "rotation_templates",
        ["rotation_template_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("fk_half_day_assignments_rotation_template_id_rotation_templates"),
        "half_day_assignments",
        type_="foreignkey",
    )
    op.drop_index(
        op.f("ix_half_day_assignments_rotation_template_id"),
        table_name="half_day_assignments",
    )
    op.drop_column("half_day_assignments", "rotation_template_id")
