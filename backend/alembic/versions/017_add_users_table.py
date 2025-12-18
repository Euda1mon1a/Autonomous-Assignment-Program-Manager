"""Add users table

Revision ID: 017
Revises: 016
Create Date: 2025-12-18 00:00:00.000000

Creates the users table for authentication and authorization.

Supports 8 user roles:
- admin: Full access to all features
- coordinator: Can manage schedules and people
- faculty: Can view schedules and manage own availability
- clinical_staff: General clinical staff
- rn: Registered Nurse
- lpn: Licensed Practical Nurse
- msa: Medical Support Assistant
- resident: Resident physician
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '017'
down_revision: Union[str, None] = '016'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create users table."""

    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('username', sa.String(100), unique=True, nullable=False),
        sa.Column('email', sa.String(255), unique=True, nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('role', sa.String(50), nullable=False, server_default='coordinator'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('last_login', sa.DateTime(), nullable=True),

        # Check constraint for valid roles
        sa.CheckConstraint(
            "role IN ('admin', 'coordinator', 'faculty', 'clinical_staff', 'rn', 'lpn', 'msa', 'resident')",
            name='check_user_role'
        ),
    )

    # Create indexes
    op.create_index('ix_users_username', 'users', ['username'])
    op.create_index('ix_users_email', 'users', ['email'])


def downgrade() -> None:
    """Drop users table."""

    # Drop indexes first
    op.drop_index('ix_users_email', table_name='users')
    op.drop_index('ix_users_username', table_name='users')

    # Drop table
    op.drop_table('users')
