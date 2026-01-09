"""Add includes_weekend_work to rotation_templates.

Revision ID: 20260108_add_weekend_config
Revises: 20260108_add_away_prog
Create Date: 2026-01-08

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260108_add_weekend_config"
down_revision = "20260108_add_away_prog"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add includes_weekend_work column to rotation_templates."""
    op.add_column(
        "rotation_templates",
        sa.Column(
            "includes_weekend_work",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
            comment="True if rotation includes weekend assignments",
        ),
    )

    # Set True for known weekend rotations based on activity_type or name patterns
    op.execute(
        """
        UPDATE rotation_templates
        SET includes_weekend_work = TRUE
        WHERE activity_type = 'inpatient'
           OR name ILIKE '%night float%'
           OR name ILIKE '%FMIT%'
           OR name ILIKE '%call%'
           OR name ILIKE '%weekend%'
        """
    )


def downgrade() -> None:
    """Remove includes_weekend_work column."""
    op.drop_column("rotation_templates", "includes_weekend_work")
