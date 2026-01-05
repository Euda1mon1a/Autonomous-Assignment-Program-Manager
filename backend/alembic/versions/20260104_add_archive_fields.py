"""add_archive_fields_to_rotation_templates

Revision ID: 20260104_add_archive_fields
Revises: 20260103_add_activity_log
Create Date: 2026-01-04 00:00:00.000000

Adds soft-delete (archive) capability to rotation templates:
- is_archived: Boolean flag for archived state
- archived_at: Timestamp when template was archived
- archived_by: FK to user who archived the template
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = '20260104_add_archive_fields'
down_revision: Union[str, None] = '20260103_add_activity_log'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add archive fields to rotation_templates
    op.add_column(
        'rotation_templates',
        sa.Column('is_archived', sa.Boolean(), nullable=False, server_default='false')
    )
    op.add_column(
        'rotation_templates',
        sa.Column('archived_at', sa.DateTime(), nullable=True)
    )
    op.add_column(
        'rotation_templates',
        sa.Column('archived_by', UUID(as_uuid=True), nullable=True)
    )

    # Add foreign key constraint for archived_by
    op.create_foreign_key(
        'fk_rotation_templates_archived_by_users',
        'rotation_templates',
        'users',
        ['archived_by'],
        ['id'],
        ondelete='SET NULL'
    )

    # Create index on is_archived for query performance
    op.create_index(
        'ix_rotation_templates_is_archived',
        'rotation_templates',
        ['is_archived']
    )


def downgrade() -> None:
    # Drop index
    op.drop_index('ix_rotation_templates_is_archived', table_name='rotation_templates')

    # Drop foreign key constraint
    op.drop_constraint(
        'fk_rotation_templates_archived_by_users',
        'rotation_templates',
        type_='foreignkey'
    )

    # Drop columns (order matters for FK constraints)
    op.drop_column('rotation_templates', 'archived_by')
    op.drop_column('rotation_templates', 'archived_at')
    op.drop_column('rotation_templates', 'is_archived')
