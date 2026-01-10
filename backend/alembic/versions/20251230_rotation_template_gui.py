"""Add rotation template GUI models

Revision ID: 20251230_rotation_gui
Revises: acfc96d01118
Create Date: 2025-12-30

This migration adds support for the rotation template GUI feature:

1. Extends rotation_templates table with:
   - pattern_type: regular, split, mirrored, alternating
   - setting_type: inpatient, outpatient
   - paired_template_id: For split rotations, links to the paired template
   - split_day: Day in block where split occurs (1-27)
   - is_mirror_primary: For mirrored splits, indicates primary pattern

2. Creates weekly_patterns table:
   - 7x2 grid of AM/PM slots for visual pattern editing
   - Links to rotation_templates
   - Supports protected slots (e.g., Wed AM conference)

3. Creates rotation_preferences table:
   - Soft scheduling constraints
   - Preference types: full_day_grouping, consecutive_specialty, etc.
   - Configurable weights: low, medium, high, required

GUI Features Enabled:
- Visual 7x2 weekly grid editor
- Split/mirrored rotation configuration
- Preference toggles with weight selection
- Inpatient vs outpatient mode toggle
- Leave eligibility toggle (existing field)
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "20251230_rotation_gui"
down_revision = "acfc96d01118"  # TODO: Update to actual latest revision
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ==========================================================================
    # 1. Extend rotation_templates table
    # ==========================================================================
    op.add_column(
        "rotation_templates",
        sa.Column(
            "pattern_type",
            sa.String(20),
            nullable=False,
            server_default="regular",
            comment="regular, split, mirrored, alternating",
        ),
    )
    op.add_column(
        "rotation_templates",
        sa.Column(
            "setting_type",
            sa.String(20),
            nullable=False,
            server_default="outpatient",
            comment="inpatient or outpatient",
        ),
    )
    op.add_column(
        "rotation_templates",
        sa.Column(
            "paired_template_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
            comment="For split rotations, the paired template",
        ),
    )
    op.add_column(
        "rotation_templates",
        sa.Column(
            "split_day",
            sa.Integer(),
            nullable=True,
            comment="Day in block where split occurs (1-27)",
        ),
    )
    op.add_column(
        "rotation_templates",
        sa.Column(
            "is_mirror_primary",
            sa.Boolean(),
            nullable=False,
            server_default="true",
            comment="For mirrored splits, is this the primary pattern?",
        ),
    )

    # Add foreign key for paired template (self-referential)
    op.create_foreign_key(
        "fk_rotation_template_paired",
        "rotation_templates",
        "rotation_templates",
        ["paired_template_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # ==========================================================================
    # 2. Create weekly_patterns table
    # ==========================================================================
    op.create_table(
        "weekly_patterns",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "rotation_template_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("rotation_templates.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "day_of_week",
            sa.Integer(),
            nullable=False,
            comment="0=Sunday, 1=Monday, ..., 6=Saturday",
        ),
        sa.Column(
            "time_of_day",
            sa.String(2),
            nullable=False,
            comment="AM or PM",
        ),
        sa.Column(
            "activity_type",
            sa.String(50),
            nullable=False,
            comment="fm_clinic, specialty, elective, conference, inpatient, call, procedure, off",
        ),
        sa.Column(
            "linked_template_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("rotation_templates.id", ondelete="SET NULL"),
            nullable=True,
            comment="Optional link to specific activity template",
        ),
        sa.Column(
            "is_protected",
            sa.Boolean(),
            nullable=False,
            default=False,
            comment="True for slots that cannot be changed (e.g., Wed AM conference)",
        ),
        sa.Column("notes", sa.String(200), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        # Unique constraint: one slot per day/time per template
        sa.UniqueConstraint(
            "rotation_template_id",
            "day_of_week",
            "time_of_day",
            name="uq_weekly_pattern_slot",
        ),
    )

    # ==========================================================================
    # 3. Create rotation_preferences table
    # ==========================================================================
    op.create_table(
        "rotation_preferences",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "rotation_template_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("rotation_templates.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "preference_type",
            sa.String(50),
            nullable=False,
            comment="full_day_grouping, consecutive_specialty, avoid_isolated, preferred_days, avoid_friday_pm, balance_weekly",
        ),
        sa.Column(
            "weight",
            sa.String(20),
            nullable=False,
            default="medium",
            comment="low, medium, high, required",
        ),
        sa.Column(
            "config_json",
            postgresql.JSONB(),
            nullable=False,
            server_default="{}",
            comment="Type-specific configuration parameters",
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            default=True,
        ),
        sa.Column("description", sa.String(200), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table("rotation_preferences")
    op.drop_table("weekly_patterns")

    # Drop foreign key and columns from rotation_templates
    op.drop_constraint(
        "fk_rotation_template_paired", "rotation_templates", type_="foreignkey"
    )
    op.drop_column("rotation_templates", "is_mirror_primary")
    op.drop_column("rotation_templates", "split_day")
    op.drop_column("rotation_templates", "paired_template_id")
    op.drop_column("rotation_templates", "setting_type")
    op.drop_column("rotation_templates", "pattern_type")
