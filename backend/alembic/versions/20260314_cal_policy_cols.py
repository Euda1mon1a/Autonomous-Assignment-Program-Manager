"""Add calendar policy columns to application_settings.

Revision ID: 20260314_cal_policy_cols
Revises: 20260314_primary_duty_tbl
Create Date: 2026-03-14
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "20260314_cal_policy_cols"
down_revision = "20260314_primary_duty_tbl"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "application_settings",
        sa.Column(
            "overnight_call_weekdays",
            JSONB,
            nullable=False,
            server_default="[0,1,2,3,6]",
        ),
    )
    op.add_column(
        "application_settings",
        sa.Column(
            "fmit_week_start_weekday",
            sa.Integer,
            nullable=False,
            server_default="4",
        ),
    )


def downgrade() -> None:
    op.drop_column("application_settings", "fmit_week_start_weekday")
    op.drop_column("application_settings", "overnight_call_weekdays")
