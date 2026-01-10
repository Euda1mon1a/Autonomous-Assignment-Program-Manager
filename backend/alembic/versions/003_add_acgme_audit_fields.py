"""Add ACGME audit fields for override tracking

Revision ID: 003
Revises: 002
Create Date: 2025-12-15 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "003"
down_revision: str | None = "002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """
    Add ACGME audit fields:
    1. override_reason and override_acknowledged_at to assignments table
    2. acgme_override_count to schedule_runs table
    """
    # Add override fields to assignments table
    op.add_column("assignments", sa.Column("override_reason", sa.Text(), nullable=True))
    op.add_column(
        "assignments",
        sa.Column("override_acknowledged_at", sa.DateTime(), nullable=True),
    )

    # Add acgme_override_count to schedule_runs table
    op.add_column(
        "schedule_runs",
        sa.Column(
            "acgme_override_count", sa.Integer(), server_default="0", nullable=True
        ),
    )


def downgrade() -> None:
    """Remove the added columns."""
    op.drop_column("assignments", "override_reason")
    op.drop_column("assignments", "override_acknowledged_at")
    op.drop_column("schedule_runs", "acgme_override_count")
