"""set C30 display abbreviation

Revision ID: 29c355a8e9a4
Revises: 20260305_learner_tables
Create Date: 2026-03-05 08:37:27.455053

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "29c355a8e9a4"
down_revision: str | None = "20260305_learner_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Set display abbreviation for C30
    op.execute(
        "UPDATE activities SET display_abbreviation = 'C30' WHERE code = 'c30' OR code = 'C30'"
    )


def downgrade() -> None:
    # We can't know for sure what it was before, but TODO says it was None
    op.execute(
        "UPDATE activities SET display_abbreviation = NULL WHERE code = 'c30' OR code = 'C30'"
    )
