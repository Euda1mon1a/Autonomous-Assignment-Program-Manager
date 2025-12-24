"""Merge multiple heads into single head.

Revision ID: 20251224_merge
Revises: 20251222_add_pc_template, 20251222_provenance
Create Date: 2025-12-24

This migration merges two parallel migration branches:
- 20251222_add_pc_template (PC rotation template)
- 20251222_provenance (schedule_run_id for assignments)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20251224_merge'
down_revision: Union[str, tuple, None] = ('20251222_add_pc_template', '20251222_provenance')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Merge migration - no schema changes needed."""
    pass


def downgrade() -> None:
    """Merge migration - no schema changes needed."""
    pass
