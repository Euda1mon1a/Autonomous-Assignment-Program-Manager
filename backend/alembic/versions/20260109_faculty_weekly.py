"""Add faculty weekly templates and activity permissions tables.

Revision ID: 20260109_faculty_weekly
Revises: 20260109_activity_requirements
Create Date: 2026-01-09

Faculty Weekly Activity Editor:
- faculty_weekly_templates: Default weekly patterns per faculty member (7x2 grid)
- faculty_weekly_overrides: Week-specific exceptions to templates
- faculty_activity_permissions: Role -> Activity mapping for auto-suggest

Also adds new faculty-specific activities:
- AT (Attending Time) - clinical supervision
- GME (Graduate Medical Education) - administrative
- DFM (Dept Family Medicine) - administrative
- PCAT (Post-Call Attending Time) - clinical supervision
- DO (Direct Observation) - clinical supervision

And adds `provides_supervision` field to activities table.
"""

import uuid
from datetime import datetime

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260109_faculty_weekly"
down_revision = "20260109_activity_requirements"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create faculty weekly tables and seed faculty activities."""

    # 1. Add provides_supervision column to activities table
    op.add_column(
        "activities",
        sa.Column(
            "provides_supervision",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
            comment="True for supervision activities (AT, PCAT, DO) that count toward supervision ratios",
        ),
    )

    # 2. Create faculty_weekly_templates table
    op.create_table(
        "faculty_weekly_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "person_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "day_of_week",
            sa.Integer(),
            nullable=False,
            comment="0=Sunday, 6=Saturday",
        ),
        sa.Column(
            "time_of_day",
            sa.String(2),
            nullable=False,
            comment="AM or PM",
        ),
        sa.Column(
            "week_number",
            sa.Integer(),
            nullable=True,
            comment="Week 1-4 within block. NULL = same pattern all weeks",
        ),
        sa.Column(
            "activity_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("activities.id", ondelete="RESTRICT"),
            nullable=True,
            comment="Activity assigned to this slot (NULL = unassigned)",
        ),
        sa.Column(
            "is_locked",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
            comment="HARD constraint - solver cannot change",
        ),
        sa.Column(
            "priority",
            sa.Integer(),
            nullable=False,
            server_default="50",
            comment="Soft preference 0-100 (higher = more important)",
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        # Unique constraint: one slot per person/day/time/week
        sa.UniqueConstraint(
            "person_id",
            "day_of_week",
            "time_of_day",
            "week_number",
            name="uq_faculty_weekly_template_slot",
        ),
    )

    # Create index on activity_id for joins
    op.create_index(
        "ix_faculty_weekly_templates_activity_id",
        "faculty_weekly_templates",
        ["activity_id"],
    )

    # 3. Create faculty_weekly_overrides table
    op.create_table(
        "faculty_weekly_overrides",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "person_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "effective_date",
            sa.Date(),
            nullable=False,
            comment="Week start date (Monday) for this override",
        ),
        sa.Column(
            "day_of_week",
            sa.Integer(),
            nullable=False,
            comment="0=Sunday, 6=Saturday",
        ),
        sa.Column(
            "time_of_day",
            sa.String(2),
            nullable=False,
            comment="AM or PM",
        ),
        sa.Column(
            "activity_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("activities.id", ondelete="RESTRICT"),
            nullable=True,
            comment="Activity for this override (NULL = clear slot)",
        ),
        sa.Column(
            "is_locked",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
            comment="HARD constraint for this specific week",
        ),
        sa.Column(
            "override_reason",
            sa.Text(),
            nullable=True,
            comment="Why this override was created",
        ),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people.id", ondelete="SET NULL"),
            nullable=True,
            comment="Who created this override",
        ),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        # Unique constraint: one override per person/date/day/time
        sa.UniqueConstraint(
            "person_id",
            "effective_date",
            "day_of_week",
            "time_of_day",
            name="uq_faculty_weekly_override_slot",
        ),
    )

    # Create index for date-based queries
    op.create_index(
        "ix_faculty_weekly_overrides_effective_date",
        "faculty_weekly_overrides",
        ["effective_date"],
    )

    # 4. Create faculty_activity_permissions table (role -> activity mapping)
    op.create_table(
        "faculty_activity_permissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "faculty_role",
            sa.String(20),
            nullable=False,
            comment="FacultyRole enum value (pd, apd, oic, dept_chief, sports_med, core, adjunct)",
        ),
        sa.Column(
            "activity_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("activities.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "is_default",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
            comment="Auto-assign this activity to new templates for this role",
        ),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        # Unique constraint: one permission per role/activity
        sa.UniqueConstraint(
            "faculty_role",
            "activity_id",
            name="uq_faculty_activity_permission",
        ),
    )

    # Create index on faculty_role for lookups
    op.create_index(
        "ix_faculty_activity_permissions_role",
        "faculty_activity_permissions",
        ["faculty_role"],
    )

    # 5. Seed new faculty activities
    now = datetime.utcnow().isoformat()

    # Activity IDs for later reference in permissions
    at_id = str(uuid.uuid4())
    gme_id = str(uuid.uuid4())
    dfm_id = str(uuid.uuid4())
    pcat_id = str(uuid.uuid4())
    do_id = str(uuid.uuid4())
    sm_clinic_id = str(uuid.uuid4())

    activities = [
        # Supervision activities (AT, PCAT, DO all count toward supervision ratios)
        {
            "id": at_id,
            "name": "Attending Time",
            "code": "at",
            "display_abbreviation": "AT",
            "activity_category": "clinical",
            "font_color": "white",
            "background_color": "blue-500",
            "requires_supervision": False,  # Faculty don't need supervision
            "is_protected": False,
            "counts_toward_clinical_hours": True,
            "provides_supervision": True,  # This IS supervision
            "display_order": 5,
        },
        {
            "id": pcat_id,
            "name": "Post-Call Attending Time",
            "code": "pcat",
            "display_abbreviation": "PCAT",
            "activity_category": "clinical",
            "font_color": "black",
            "background_color": "amber-400",
            "requires_supervision": False,
            "is_protected": False,
            "counts_toward_clinical_hours": True,
            "provides_supervision": True,  # Supervision after call
            "display_order": 6,
        },
        {
            "id": do_id,
            "name": "Direct Observation",
            "code": "do",
            "display_abbreviation": "DO",
            "activity_category": "clinical",
            "font_color": "white",
            "background_color": "teal-500",
            "requires_supervision": False,
            "is_protected": False,
            "counts_toward_clinical_hours": True,
            "provides_supervision": True,  # Direct supervision
            "display_order": 7,
        },
        # Administrative activities
        {
            "id": gme_id,
            "name": "Graduate Medical Education",
            "code": "gme",
            "display_abbreviation": "GME",
            "activity_category": "administrative",
            "font_color": "white",
            "background_color": "purple-500",
            "requires_supervision": False,
            "is_protected": False,
            "counts_toward_clinical_hours": False,
            "provides_supervision": False,
            "display_order": 150,
        },
        {
            "id": dfm_id,
            "name": "Dept Family Medicine",
            "code": "dfm",
            "display_abbreviation": "DFM",
            "activity_category": "administrative",
            "font_color": "white",
            "background_color": "indigo-500",
            "requires_supervision": False,
            "is_protected": False,
            "counts_toward_clinical_hours": False,
            "provides_supervision": False,
            "display_order": 151,
        },
        # Sports Medicine clinic (if not already exists - check first)
        {
            "id": sm_clinic_id,
            "name": "Sports Medicine Clinic",
            "code": "sm_clinic",
            "display_abbreviation": "SM",
            "activity_category": "clinical",
            "font_color": "white",
            "background_color": "orange-500",
            "requires_supervision": False,  # Faculty activity
            "is_protected": False,
            "counts_toward_clinical_hours": True,
            "provides_supervision": True,  # SM faculty supervise
            "display_order": 15,
        },
    ]

    # Build INSERT statement
    activities_table = sa.table(
        "activities",
        sa.column("id", postgresql.UUID),
        sa.column("name", sa.String),
        sa.column("code", sa.String),
        sa.column("display_abbreviation", sa.String),
        sa.column("activity_category", sa.String),
        sa.column("font_color", sa.String),
        sa.column("background_color", sa.String),
        sa.column("requires_supervision", sa.Boolean),
        sa.column("is_protected", sa.Boolean),
        sa.column("counts_toward_clinical_hours", sa.Boolean),
        sa.column("provides_supervision", sa.Boolean),
        sa.column("display_order", sa.Integer),
        sa.column("is_archived", sa.Boolean),
        sa.column("created_at", sa.DateTime),
        sa.column("updated_at", sa.DateTime),
    )

    for activity in activities:
        # Use INSERT ... ON CONFLICT DO NOTHING to skip if already exists
        op.execute(
            sa.text("""
                INSERT INTO activities (id, name, code, display_abbreviation, activity_category,
                    font_color, background_color, requires_supervision, is_protected,
                    counts_toward_clinical_hours, provides_supervision, display_order,
                    is_archived, created_at, updated_at)
                VALUES (:id, :name, :code, :display_abbreviation, :activity_category,
                    :font_color, :background_color, :requires_supervision, :is_protected,
                    :counts_toward_clinical_hours, :provides_supervision, :display_order,
                    false, :created_at, :updated_at)
                ON CONFLICT (code) DO NOTHING
            """).bindparams(
                id=activity["id"],
                name=activity["name"],
                code=activity["code"],
                display_abbreviation=activity["display_abbreviation"],
                activity_category=activity["activity_category"],
                font_color=activity["font_color"],
                background_color=activity["background_color"],
                requires_supervision=activity["requires_supervision"],
                is_protected=activity["is_protected"],
                counts_toward_clinical_hours=activity["counts_toward_clinical_hours"],
                provides_supervision=activity["provides_supervision"],
                display_order=activity["display_order"],
                created_at=now,
                updated_at=now,
            )
        )

    # 6. Seed faculty activity permissions (role -> activity mapping)
    # First, get activity IDs for existing activities (fm_clinic already exists)
    permissions_table = sa.table(
        "faculty_activity_permissions",
        sa.column("id", postgresql.UUID),
        sa.column("faculty_role", sa.String),
        sa.column("activity_id", postgresql.UUID),
        sa.column("is_default", sa.Boolean),
        sa.column("created_at", sa.DateTime),
    )

    # We need to look up fm_clinic ID since it was seeded in earlier migration
    # For now, seed permissions for the new activities we just created

    permissions = [
        # PD: GME only (0 clinic)
        {"role": "pd", "activity_id": gme_id, "is_default": True},
        {"role": "pd", "activity_id": at_id, "is_default": False},
        {"role": "pd", "activity_id": pcat_id, "is_default": False},
        {"role": "pd", "activity_id": do_id, "is_default": False},
        # APD: GME + clinic (2/week)
        {"role": "apd", "activity_id": gme_id, "is_default": True},
        {"role": "apd", "activity_id": at_id, "is_default": False},
        {"role": "apd", "activity_id": pcat_id, "is_default": False},
        {"role": "apd", "activity_id": do_id, "is_default": False},
        # OIC: DFM + GME + clinic (2/week)
        {"role": "oic", "activity_id": dfm_id, "is_default": True},
        {
            "role": "oic",
            "activity_id": gme_id,
            "is_default": False,
        },  # OIC also gets some GME
        {"role": "oic", "activity_id": at_id, "is_default": False},
        {"role": "oic", "activity_id": pcat_id, "is_default": False},
        {"role": "oic", "activity_id": do_id, "is_default": False},
        # Dept Chief: DFM + clinic (1/week)
        {"role": "dept_chief", "activity_id": dfm_id, "is_default": True},
        {"role": "dept_chief", "activity_id": at_id, "is_default": False},
        {"role": "dept_chief", "activity_id": pcat_id, "is_default": False},
        {"role": "dept_chief", "activity_id": do_id, "is_default": False},
        # Sports Med: SM Clinic (4/week), no regular FM
        {"role": "sports_med", "activity_id": sm_clinic_id, "is_default": True},
        {"role": "sports_med", "activity_id": at_id, "is_default": False},
        {"role": "sports_med", "activity_id": pcat_id, "is_default": False},
        {"role": "sports_med", "activity_id": do_id, "is_default": False},
        # Core: GME + clinic (up to 4/week)
        {"role": "core", "activity_id": gme_id, "is_default": False},
        {"role": "core", "activity_id": at_id, "is_default": False},
        {"role": "core", "activity_id": pcat_id, "is_default": False},
        {"role": "core", "activity_id": do_id, "is_default": False},
        # Adjunct: Not auto-scheduled but can have these activities
        {"role": "adjunct", "activity_id": at_id, "is_default": False},
        {"role": "adjunct", "activity_id": pcat_id, "is_default": False},
        {"role": "adjunct", "activity_id": do_id, "is_default": False},
    ]

    for perm in permissions:
        op.execute(
            permissions_table.insert().values(
                id=str(uuid.uuid4()),
                faculty_role=perm["role"],
                activity_id=perm["activity_id"],
                is_default=perm["is_default"],
                created_at=now,
            )
        )

    # 7. Link fm_clinic to roles that get it
    # This requires a subquery to get fm_clinic's ID
    op.execute(
        sa.text("""
            INSERT INTO faculty_activity_permissions (id, faculty_role, activity_id, is_default, created_at)
            SELECT gen_random_uuid(), role, (SELECT id FROM activities WHERE code = 'fm_clinic'), is_default, NOW()
            FROM (VALUES
                ('apd', true),
                ('oic', true),
                ('dept_chief', true),
                ('core', true)
            ) AS roles(role, is_default)
            WHERE EXISTS (SELECT 1 FROM activities WHERE code = 'fm_clinic')
            ON CONFLICT (faculty_role, activity_id) DO NOTHING
        """)
    )


def downgrade() -> None:
    """Drop faculty weekly tables and remove faculty activities."""
    # Drop permissions table
    op.drop_index(
        "ix_faculty_activity_permissions_role",
        table_name="faculty_activity_permissions",
    )
    op.drop_table("faculty_activity_permissions")

    # Drop overrides table
    op.drop_index(
        "ix_faculty_weekly_overrides_effective_date",
        table_name="faculty_weekly_overrides",
    )
    op.drop_table("faculty_weekly_overrides")

    # Drop templates table
    op.drop_index(
        "ix_faculty_weekly_templates_activity_id", table_name="faculty_weekly_templates"
    )
    op.drop_table("faculty_weekly_templates")

    # Remove faculty activities (be careful not to delete if in use)
    op.execute(
        sa.text("""
            DELETE FROM activities
            WHERE code IN ('at', 'gme', 'dfm', 'pcat', 'do', 'sm_clinic')
            AND NOT EXISTS (
                SELECT 1 FROM weekly_patterns WHERE activity_id = activities.id
            )
        """)
    )

    # Drop provides_supervision column
    op.drop_column("activities", "provides_supervision")
