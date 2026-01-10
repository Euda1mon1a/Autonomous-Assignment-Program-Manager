"""Add rotation_activity_requirements table.

Revision ID: 20260109_activity_requirements
Revises: 20260109_weekly_pattern_fk
Create Date: 2026-01-09

This table enables dynamic per-activity requirements for rotation templates:
- Replace fixed fields (fm_clinic_halfdays, specialty_halfdays) with flexible rows
- Support week-specific requirements (LEC weeks 1-3, Advising week 4)
- Include soft constraints (priority, prefer_full_days, preferred_days)

Migrates existing data from rotation_halfday_requirements table.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260109_activity_requirements"
down_revision = "20260109_weekly_pattern_fk"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create rotation_activity_requirements table and migrate existing data."""
    # Create the new table
    op.create_table(
        "rotation_activity_requirements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "rotation_template_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("rotation_templates.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "activity_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("activities.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        # Quantity requirements
        sa.Column("min_halfdays", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_halfdays", sa.Integer(), nullable=False, server_default="14"),
        sa.Column("target_halfdays", sa.Integer(), nullable=True),
        # Week scope
        sa.Column("applicable_weeks", postgresql.JSONB(), nullable=True),
        sa.Column(
            "applicable_weeks_hash",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        # Scheduling preferences
        sa.Column(
            "prefer_full_days", sa.Boolean(), nullable=False, server_default=sa.true()
        ),
        sa.Column("preferred_days", postgresql.JSONB(), nullable=True),
        sa.Column("avoid_days", postgresql.JSONB(), nullable=True),
        # Priority for soft constraints
        sa.Column("priority", sa.Integer(), nullable=False, server_default="50"),
        # Timestamps
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        # Unique constraint
        sa.UniqueConstraint(
            "rotation_template_id",
            "activity_id",
            "applicable_weeks_hash",
            name="uq_rotation_activity_req",
        ),
    )

    # Create indexes
    op.create_index(
        "ix_rotation_activity_req_template",
        "rotation_activity_requirements",
        ["rotation_template_id"],
    )
    op.create_index(
        "ix_rotation_activity_req_activity",
        "rotation_activity_requirements",
        ["activity_id"],
    )

    # Migrate data from rotation_halfday_requirements
    # This creates rows for fm_clinic, specialty, academics, elective activities
    # using the existing counts from the old table
    op.execute("""
        INSERT INTO rotation_activity_requirements (
            id, rotation_template_id, activity_id,
            min_halfdays, max_halfdays, target_halfdays,
            applicable_weeks, applicable_weeks_hash,
            prefer_full_days, preferred_days, avoid_days, priority,
            created_at, updated_at
        )
        SELECT
            gen_random_uuid(),
            rhr.rotation_template_id,
            a.id,
            rhr.fm_clinic_halfdays,
            rhr.fm_clinic_halfdays,
            rhr.fm_clinic_halfdays,
            NULL,
            '6ba7b810-9dad-11d1-80b4-00c04fd430c8'::uuid, -- 'all' weeks hash
            rhr.prefer_combined_clinic_days,
            NULL,
            NULL,
            80,
            COALESCE(rhr.created_at, NOW()),
            COALESCE(rhr.updated_at, NOW())
        FROM rotation_halfday_requirements rhr
        JOIN activities a ON a.code = 'fm_clinic'
        WHERE rhr.fm_clinic_halfdays > 0;

        INSERT INTO rotation_activity_requirements (
            id, rotation_template_id, activity_id,
            min_halfdays, max_halfdays, target_halfdays,
            applicable_weeks, applicable_weeks_hash,
            prefer_full_days, preferred_days, avoid_days, priority,
            created_at, updated_at
        )
        SELECT
            gen_random_uuid(),
            rhr.rotation_template_id,
            a.id,
            rhr.specialty_halfdays,
            rhr.specialty_halfdays,
            rhr.specialty_halfdays,
            NULL,
            '6ba7b810-9dad-11d1-80b4-00c04fd430c8'::uuid,
            rhr.prefer_combined_clinic_days,
            NULL,
            NULL,
            70,
            COALESCE(rhr.created_at, NOW()),
            COALESCE(rhr.updated_at, NOW())
        FROM rotation_halfday_requirements rhr
        JOIN activities a ON a.code = 'specialty'
        WHERE rhr.specialty_halfdays > 0;

        INSERT INTO rotation_activity_requirements (
            id, rotation_template_id, activity_id,
            min_halfdays, max_halfdays, target_halfdays,
            applicable_weeks, applicable_weeks_hash,
            prefer_full_days, preferred_days, avoid_days, priority,
            created_at, updated_at
        )
        SELECT
            gen_random_uuid(),
            rhr.rotation_template_id,
            a.id,
            rhr.academics_halfdays,
            rhr.academics_halfdays,
            rhr.academics_halfdays,
            NULL,
            '6ba7b810-9dad-11d1-80b4-00c04fd430c8'::uuid,
            false,
            NULL,
            NULL,
            100, -- Academics is protected/highest priority
            COALESCE(rhr.created_at, NOW()),
            COALESCE(rhr.updated_at, NOW())
        FROM rotation_halfday_requirements rhr
        JOIN activities a ON a.code = 'lec'
        WHERE rhr.academics_halfdays > 0;

        INSERT INTO rotation_activity_requirements (
            id, rotation_template_id, activity_id,
            min_halfdays, max_halfdays, target_halfdays,
            applicable_weeks, applicable_weeks_hash,
            prefer_full_days, preferred_days, avoid_days, priority,
            created_at, updated_at
        )
        SELECT
            gen_random_uuid(),
            rhr.rotation_template_id,
            a.id,
            0, -- min = 0 (elective is flexible)
            rhr.elective_halfdays,
            rhr.elective_halfdays,
            NULL,
            '6ba7b810-9dad-11d1-80b4-00c04fd430c8'::uuid,
            true,
            NULL,
            NULL,
            30, -- Low priority
            COALESCE(rhr.created_at, NOW()),
            COALESCE(rhr.updated_at, NOW())
        FROM rotation_halfday_requirements rhr
        JOIN activities a ON a.code = 'elective'
        WHERE COALESCE(rhr.elective_halfdays, 0) > 0;
    """)


def downgrade() -> None:
    """Drop rotation_activity_requirements table."""
    op.drop_index(
        "ix_rotation_activity_req_activity", table_name="rotation_activity_requirements"
    )
    op.drop_index(
        "ix_rotation_activity_req_template", table_name="rotation_activity_requirements"
    )
    op.drop_table("rotation_activity_requirements")
