"""drop_legacy_leave_columns_from_block_assignments

Revision ID: 8b9cea518229
Revises: 20260224_person_ay
Create Date: 2026-02-25 06:17:40.824824

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8b9cea518229"
down_revision: str | None = "20260224_person_ay"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_column("block_assignments", "leave_days")
    op.drop_column("block_assignments", "has_leave")


def downgrade() -> None:
    op.add_column(
        "block_assignments",
        sa.Column(
            "has_leave",
            sa.BOOLEAN(),
            server_default=sa.text("false"),
            autoincrement=False,
            nullable=False,
        ),
    )
    op.add_column(
        "block_assignments",
        sa.Column(
            "leave_days",
            sa.INTEGER(),
            server_default=sa.text("0"),
            autoincrement=False,
            nullable=False,
        ),
    )
