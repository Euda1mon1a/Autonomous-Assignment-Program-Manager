"""add clinical staff roles

Revision ID: 012_add_clinical_staff_roles
Revises: 011_add_token_blacklist
Create Date: 2025-12-17

Description:
    Add support for clinical staff roles (rn, lpn, msa, clinical_staff, resident)
    to the users table. This enables role-based filtering for different user types.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '012_add_clinical_staff_roles'
down_revision = '011_add_token_blacklist'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add new roles to user role check constraint."""
    # Drop the old constraint
    op.drop_constraint('check_user_role', 'users', type_='check')

    # Add the new constraint with additional roles
    op.create_check_constraint(
        'check_user_role',
        'users',
        "role IN ('admin', 'coordinator', 'faculty', 'clinical_staff', 'rn', 'lpn', 'msa', 'resident')"
    )


def downgrade() -> None:
    """Revert to original role constraint."""
    # Drop the new constraint
    op.drop_constraint('check_user_role', 'users', type_='check')

    # Restore the old constraint
    op.create_check_constraint(
        'check_user_role',
        'users',
        "role IN ('admin', 'coordinator', 'faculty')"
    )
