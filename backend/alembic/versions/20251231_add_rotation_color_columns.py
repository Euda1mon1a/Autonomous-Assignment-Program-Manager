"""Add font_color and background_color to rotation_templates

Revision ID: 20251231_rotation_colors
Revises: 20260101_mod_columns
Create Date: 2025-12-31

Adds display color columns for rotation templates to support
Tailwind-based UI styling.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '20251231_rotation_colors'
down_revision: Union[str, None] = '20260101_mod_columns'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add font_color and background_color columns to rotation_templates."""
    op.add_column(
        'rotation_templates',
        sa.Column('font_color', sa.String(length=50), nullable=True)
    )
    op.add_column(
        'rotation_templates',
        sa.Column('background_color', sa.String(length=50), nullable=True)
    )


def downgrade() -> None:
    """Remove font_color and background_color columns from rotation_templates."""
    op.drop_column('rotation_templates', 'background_color')
    op.drop_column('rotation_templates', 'font_color')
