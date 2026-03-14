"""Add call preference columns to people table.

Moves hardcoded avoid_tuesday_call and prefer_wednesday_call from
Python role-derived properties into DB columns so coordinators can
manage them per-person from the admin UI.

NULL means "use role-derived default".  Explicit True/False overrides
the role fallback.  The seed UPDATE below sets the columns for the
roles that had non-default values (PD/APD avoid Tuesday, Dept Chief
prefers Wednesday).

Revision ID: 20260314_call_pref_cols
Revises: 20260314_cal_policy_cols
Create Date: 2026-03-14
"""

from alembic import op
import sqlalchemy as sa

revision = "20260314_call_pref_cols"
down_revision = "20260314_cal_policy_cols"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "people",
        sa.Column(
            "call_pref_avoid_tuesday",
            sa.Boolean,
            nullable=True,
        ),
    )
    op.add_column(
        "people",
        sa.Column(
            "call_pref_prefer_wednesday",
            sa.Boolean,
            nullable=True,
        ),
    )

    # Seed from existing role defaults
    op.execute(
        """
        UPDATE people SET call_pref_avoid_tuesday = true
        WHERE type = 'faculty' AND faculty_role IN ('pd', 'apd')
        """
    )
    op.execute(
        """
        UPDATE people SET call_pref_prefer_wednesday = true
        WHERE type = 'faculty' AND faculty_role = 'dept_chief'
        """
    )


def downgrade() -> None:
    op.drop_column("people", "call_pref_prefer_wednesday")
    op.drop_column("people", "call_pref_avoid_tuesday")
