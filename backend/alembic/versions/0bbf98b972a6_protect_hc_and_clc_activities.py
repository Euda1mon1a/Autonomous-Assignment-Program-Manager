"""protect hc and clc activities

Revision ID: 0bbf98b972a6
Revises: 29c355a8e9a4
Create Date: 2026-03-05 08:43:59.238300

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0bbf98b972a6"
down_revision: str | None = "29c355a8e9a4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "UPDATE activities SET is_protected = TRUE WHERE code IN ('hc', 'HC', 'clc', 'CLC', 'hlc', 'HLC')"
    )


def downgrade() -> None:
    op.execute(
        "UPDATE activities SET is_protected = FALSE WHERE code IN ('hc', 'HC', 'clc', 'CLC', 'hlc', 'HLC')"
    )
