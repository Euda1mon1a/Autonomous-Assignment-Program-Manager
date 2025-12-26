"""Change Leave Weekend activity_type to absence

Revision ID: 9c693e414966
Revises: 20251225_schema_ver
Create Date: 2025-12-25 15:31:06.237481

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9c693e414966'
down_revision: str | None = '20251225_schema_ver'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Change Leave/Weekend templates from 'outpatient' to 'absence' activity_type.

    These templates represent scheduled time off, not clinic rotations.
    The solver should preserve existing absence assignments rather than
    trying to optimize them as outpatient slots.
    """
    op.execute(
        """
        UPDATE rotation_templates
        SET activity_type = 'absence'
        WHERE name IN ('Leave AM', 'Leave PM', 'Weekend AM', 'Weekend PM')
        """
    )


def downgrade() -> None:
    """Revert Leave/Weekend templates back to 'outpatient'."""
    op.execute(
        """
        UPDATE rotation_templates
        SET activity_type = 'outpatient'
        WHERE name IN ('Leave AM', 'Leave PM', 'Weekend AM', 'Weekend PM')
        """
    )
