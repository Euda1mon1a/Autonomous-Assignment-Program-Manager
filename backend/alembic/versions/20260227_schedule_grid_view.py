"""Create schedule_grid SQL view for spatial schedule validation.

Pivots half_day_assignments into a person × date grid with AM/PM columns,
enabling spatial pattern detection (weekend work, all-GME, coverage gaps)
via SQL queries instead of requiring XLSX generation.

Revision ID: 20260227_sched_grid
Revises: 20260227_add_adjunct
Create Date: 2026-02-27
"""

from alembic import op

revision = "20260227_sched_grid"
down_revision = "20260227_add_adjunct"
branch_labels = None
depends_on = None

SCHEDULE_GRID_VIEW = """
CREATE OR REPLACE VIEW schedule_grid AS
SELECT
    p.id AS person_id,
    p.name,
    p.type AS person_type,
    p.faculty_role,
    p.pgy_level,
    hda.date,
    EXTRACT(DOW FROM hda.date)::int AS day_of_week,
    EXTRACT(ISODOW FROM hda.date)::int AS iso_day_of_week,
    MAX(CASE WHEN hda.time_of_day = 'AM' THEN a.code END) AS am_code,
    MAX(CASE WHEN hda.time_of_day = 'PM' THEN a.code END) AS pm_code,
    MAX(CASE WHEN hda.time_of_day = 'AM' THEN a.display_abbreviation END) AS am_display,
    MAX(CASE WHEN hda.time_of_day = 'PM' THEN a.display_abbreviation END) AS pm_display,
    MAX(CASE WHEN hda.time_of_day = 'AM' THEN hda.source END) AS am_source,
    MAX(CASE WHEN hda.time_of_day = 'PM' THEN hda.source END) AS pm_source,
    MAX(CASE WHEN hda.time_of_day = 'AM' THEN hda.is_override::int END)::boolean AS am_override,
    MAX(CASE WHEN hda.time_of_day = 'PM' THEN hda.is_override::int END)::boolean AS pm_override
FROM half_day_assignments hda
JOIN people p ON hda.person_id = p.id
LEFT JOIN activities a ON hda.activity_id = a.id
GROUP BY p.id, p.name, p.type, p.faculty_role, p.pgy_level, hda.date
"""


def upgrade() -> None:
    op.execute(SCHEDULE_GRID_VIEW)


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS schedule_grid")
