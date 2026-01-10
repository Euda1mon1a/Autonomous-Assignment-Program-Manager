"""Add absence blocking flag and person capacity fields

Revision ID: 002
Revises: 001
Create Date: 2025-12-15 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: str | None = "001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """
    Add new fields to support:
    1. Blocking vs partial absences
    2. Individual person capacity targets
    """
    # Add is_blocking to absences table
    op.add_column(
        "absences",
        sa.Column("is_blocking", sa.Boolean(), server_default="false", nullable=True),
    )

    # Add target_clinical_blocks to people table
    op.add_column(
        "people", sa.Column("target_clinical_blocks", sa.Integer(), nullable=True)
    )


def downgrade() -> None:
    """Remove the added columns."""
    op.drop_column("absences", "is_blocking")
    op.drop_column("people", "target_clinical_blocks")
