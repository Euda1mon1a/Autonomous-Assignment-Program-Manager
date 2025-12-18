"""Add absence tracking fields and rotation leave eligibility

Revision ID: 015
Revises: 014
Create Date: 2025-12-18 00:00:00.000000

Changes:
1. Absence model:
   - return_date_tentative: Flag for Hawaii-reality where return dates are often unknown
   - created_by_id: Track which admin entered the absence (for on-behalf-of workflow)
   - Expanded absence_type enum with emergency-appropriate types

2. RotationTemplate model:
   - leave_eligible: Whether scheduled leave is allowed on this rotation

New absence types:
- bereavement: Death in family (auto-blocking, Hawaii = 7+ days travel)
- emergency_leave: Urgent personal emergency (auto-blocking)
- sick: Short-term illness (duration-based blocking)
- convalescent: Post-surgery/injury recovery (auto-blocking)
- maternity_paternity: Parental leave (auto-blocking)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '015'
down_revision: Union[str, None] = '014'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add absence tracking and rotation leave eligibility fields."""

    # 1. Add return_date_tentative to absences
    op.add_column(
        'absences',
        sa.Column('return_date_tentative', sa.Boolean(), server_default='false', nullable=False)
    )

    # 2. Add created_by_id to absences (FK to people - tracks admin who entered it)
    op.add_column(
        'absences',
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.create_foreign_key(
        'fk_absence_created_by',
        'absences',
        'people',
        ['created_by_id'],
        ['id'],
        ondelete='SET NULL'
    )

    # 3. Add leave_eligible to rotation_templates
    op.add_column(
        'rotation_templates',
        sa.Column('leave_eligible', sa.Boolean(), server_default='true', nullable=False)
    )

    # 4. Drop old absence_type constraint and add expanded one
    op.drop_constraint('check_absence_type', 'absences', type_='check')
    op.create_check_constraint(
        'check_absence_type',
        'absences',
        "absence_type IN ('vacation', 'deployment', 'tdy', 'medical', 'family_emergency', "
        "'conference', 'bereavement', 'emergency_leave', 'sick', 'convalescent', 'maternity_paternity')"
    )


def downgrade() -> None:
    """Remove the added columns and restore original constraint."""

    # Remove expanded constraint and restore original
    op.drop_constraint('check_absence_type', 'absences', type_='check')
    op.create_check_constraint(
        'check_absence_type',
        'absences',
        "absence_type IN ('vacation', 'deployment', 'tdy', 'medical', 'family_emergency', 'conference')"
    )

    # Remove leave_eligible from rotation_templates
    op.drop_column('rotation_templates', 'leave_eligible')

    # Remove created_by_id from absences
    op.drop_constraint('fk_absence_created_by', 'absences', type_='foreignkey')
    op.drop_column('absences', 'created_by_id')

    # Remove return_date_tentative from absences
    op.drop_column('absences', 'return_date_tentative')
