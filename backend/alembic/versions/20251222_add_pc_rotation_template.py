"""Add Post-Call (PC) rotation template

Revision ID: 20251222_add_pc_template
Revises: 9d38e1388001
Create Date: 2025-12-22

PC (Post-Call) is a mandatory full-day recovery period after Night Float.
- leave_eligible = false (cannot take leave on PC day)
- is_block_half_rotation = false (it's a single day, not a block-half)
- activity_type = 'recovery'
"""
from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20251222_add_pc_template'
down_revision: Union[str, None] = '9d38e1388001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Insert PC rotation template (idempotent - skip if already exists)
    op.execute(
        sa.text("""
            INSERT INTO rotation_templates (
                id, name, abbreviation, activity_type,
                leave_eligible, is_block_half_rotation,
                supervision_required, max_supervision_ratio,
                created_at
            ) VALUES (
                :id, 'Post-Call Recovery', 'PC', 'recovery',
                false, false,
                false, NULL,
                NOW()
            )
            ON CONFLICT (abbreviation) DO NOTHING
        """).bindparams(id=str(uuid.uuid4()))
    )


def downgrade() -> None:
    # Remove PC rotation template
    op.execute(
        sa.text("DELETE FROM rotation_templates WHERE abbreviation = 'PC'")
    )
