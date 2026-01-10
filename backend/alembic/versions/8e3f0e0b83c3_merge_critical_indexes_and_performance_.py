"""merge_critical_indexes_and_performance_indexes

Revision ID: 8e3f0e0b83c3
Revises: 12b3fa4f11ec, 20251230_critical_idx
Create Date: 2025-12-30 20:37:55.625022

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8e3f0e0b83c3"
down_revision: str | None = ("12b3fa4f11ec", "20251230_critical_idx")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
