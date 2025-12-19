"""Add template_id to email_logs table

Revision ID: 20251219_add_template_id
Revises: 20241217_add_fmit_phase2_tables
Create Date: 2025-12-19 00:00:00.000000

Adds template_id foreign key to email_logs table to track which
email template was used for sending an email. This completes the
email notification infrastructure for v1.1.0.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20251219_add_template_id'
down_revision: Union[str, None] = '20241217_add_fmit_phase2_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add template_id column to email_logs table."""

    # Add template_id column
    op.add_column(
        'email_logs',
        sa.Column(
            'template_id',
            postgresql.UUID(as_uuid=True),
            nullable=True
        )
    )

    # Add foreign key constraint
    op.create_foreign_key(
        'fk_email_logs_template_id',
        'email_logs',
        'email_templates',
        ['template_id'],
        ['id'],
        ondelete='SET NULL'
    )

    # Add index for better query performance
    op.create_index(
        'ix_email_logs_template_id',
        'email_logs',
        ['template_id']
    )


def downgrade() -> None:
    """Remove template_id column from email_logs table."""

    # Drop index
    op.drop_index('ix_email_logs_template_id', table_name='email_logs')

    # Drop foreign key constraint
    op.drop_constraint('fk_email_logs_template_id', 'email_logs', type_='foreignkey')

    # Drop column
    op.drop_column('email_logs', 'template_id')
