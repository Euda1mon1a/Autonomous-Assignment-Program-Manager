"""merge block0 and main heads

Revision ID: e46cd3bee350
Revises: 20251226_block0, 9c693e414966
Create Date: 2025-12-26 14:50:06.980654

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e46cd3bee350'
down_revision: Union[str, None] = ('20251226_block0', '9c693e414966')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
