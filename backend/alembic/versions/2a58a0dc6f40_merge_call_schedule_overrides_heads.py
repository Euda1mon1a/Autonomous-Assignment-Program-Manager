"""merge_call_schedule_overrides_heads

Revision ID: 2a58a0dc6f40
Revises: 20260129_add_call_overrides, 20260129_add_schedule_overrides
Create Date: 2026-01-29 07:50:54.472789

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "2a58a0dc6f40"
down_revision: str | None = (
    "20260129_add_call_overrides",
    "20260129_add_schedule_overrides",
)
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
