"""20260115_merge_heads

Revision ID: ae892630526b
Revises: 20260114_half_day_tables, 20260115_draft_time_notnull
Create Date: 2026-01-16 03:02:03.001626

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "ae892630526b"
down_revision: str | None = ("20260114_half_day_tables", "20260115_draft_time_notnull")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
