"""Add template_category to rotation_templates.

Revision ID: 20260108_add_tmpl_cat
Revises: 20260107_add_week_num_weekly_patterns
Create Date: 2026-01-08

Categories:
- rotation: Clinical work (clinic, inpatient, outpatient, procedure)
- time_off: ACGME-protected rest (off, recovery)
- absence: Days away from program (absence activity type)
- educational: Structured learning (conference, education, lecture)
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260108_add_tmpl_cat"
down_revision = "20260107_add_week_num_weekly_patterns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add template_category column with default
    op.add_column(
        "rotation_templates",
        sa.Column(
            "template_category",
            sa.String(20),
            nullable=False,
            server_default="rotation",
        ),
    )

    # Create index for efficient filtering
    op.create_index(
        "ix_rotation_templates_template_category",
        "rotation_templates",
        ["template_category"],
    )

    # Backfill based on activity_type mapping
    op.execute("""
        UPDATE rotation_templates SET template_category = CASE
            WHEN activity_type IN ('clinic', 'inpatient', 'outpatient', 'procedure', 'procedures', 'clinical') THEN 'rotation'
            WHEN activity_type IN ('off', 'recovery') THEN 'time_off'
            WHEN activity_type = 'absence' THEN 'absence'
            WHEN activity_type IN ('conference', 'education', 'lecture', 'academic') THEN 'educational'
            ELSE 'rotation'
        END
    """)

    # Remove server default after backfill (optional, keeps schema clean)
    op.alter_column(
        "rotation_templates",
        "template_category",
        server_default=None,
    )


def downgrade() -> None:
    op.drop_index("ix_rotation_templates_template_category", table_name="rotation_templates")
    op.drop_column("rotation_templates", "template_category")
