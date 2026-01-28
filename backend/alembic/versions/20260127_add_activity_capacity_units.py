"""Add capacity_units to activities for FMC physical capacity tracking.

Revision ID: 20260127_add_activity_capacity_units
Revises: 20260127_normalize_rotation_type_outpatient
Create Date: 2026-01-27
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260127_add_activity_capacity_units"
down_revision = "20260127_normalize_rotation_type_outpatient"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "activities",
        sa.Column(
            "capacity_units",
            sa.Integer(),
            nullable=False,
            server_default="1",
        ),
    )

    # Default non-physical categories to 0
    op.execute(
        """
        UPDATE activities
        SET capacity_units = 0
        WHERE activity_category IN ('educational', 'administrative', 'time_off');
        """
    )

    # Explicitly zero out non-physical clinical/supervision/admin/education codes
    op.execute(
        """
        UPDATE activities
        SET capacity_units = 0
        WHERE upper(code) IN (
              'CV','AT','PCAT','DO',
              'GME','DFM','LEC','ADV','ADVISING','CONF','SIM','PI','MM','CLC','HAFP',
              'USAFP','BLS','ADM','FLX','DEP','TDY','W','HOL','HOLIDAY','OFF','LV','LV-AM','LV-PM','REC'
        )
           OR upper(display_abbreviation) IN (
              'CV','AT','PCAT','DO',
              'GME','DFM','LEC','ADV','CONF','SIM','PI','MM','CLC','HAFP',
              'USAFP','BLS','ADM','FLX','DEP','TDY','W','HOL','OFF','LV','REC'
        );
        """
    )


def downgrade() -> None:
    op.drop_column("activities", "capacity_units")
