"""fix_faculty_schedule_preference_day_mapping

Revision ID: be2e66649140
Revises: 6a876bddd2d5
Create Date: 2026-02-27 12:20:47.578099

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "be2e66649140"
down_revision: str | None = "6a876bddd2d5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Shift days: Sunday (0) becomes 6. Monday (1) becomes 0, Tuesday (2) becomes 1, etc.
    op.execute("UPDATE faculty_schedule_preferences SET day_of_week = day_of_week - 1")
    op.execute(
        "UPDATE faculty_schedule_preferences SET day_of_week = 6 WHERE day_of_week = -1"
    )


def downgrade() -> None:
    # Reverse the shift
    op.execute(
        "UPDATE faculty_schedule_preferences SET day_of_week = 0 WHERE day_of_week = 6"
    )
    op.execute(
        "UPDATE faculty_schedule_preferences SET day_of_week = day_of_week + 1 WHERE day_of_week != 0"
    )
