"""merge_heads_for_canonical_rotations

Revision ID: a32138fd921a
Revises: 20260309_annual_rot, 473e26e57e64
Create Date: 2026-03-10 22:34:02.883036

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a32138fd921a"
down_revision: str | None = ("20260309_annual_rot", "473e26e57e64")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
