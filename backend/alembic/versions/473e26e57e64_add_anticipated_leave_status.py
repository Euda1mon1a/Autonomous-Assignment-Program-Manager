"""Add anticipated leave status

Revision ID: 473e26e57e64
Revises: 0bbf98b972a6
Create Date: 2026-03-05 10:13:32.053938

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "473e26e57e64"
down_revision: str | None = "0bbf98b972a6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Drop the old constraint
    op.drop_constraint("check_absence_status", "absences", type_="check")

    # Add the new constraint with 'anticipated', 'confirmed', 'denied'
    op.create_check_constraint(
        "check_absence_status",
        "absences",
        "status IN ('pending', 'approved', 'rejected', 'cancelled', 'anticipated', 'confirmed', 'denied')",
    )


def downgrade() -> None:
    op.drop_constraint("check_absence_status", "absences", type_="check")
    op.create_check_constraint(
        "check_absence_status",
        "absences",
        "status IN ('pending', 'approved', 'rejected', 'cancelled')",
    )
