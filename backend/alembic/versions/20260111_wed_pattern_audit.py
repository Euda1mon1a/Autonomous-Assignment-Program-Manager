"""Fix Wednesday pattern audit findings

Revision ID: 20260111_wed_pattern_audit
Revises: 20260111_flex_clinic_reqs
Create Date: 2026-01-11

Data quality audit found templates missing standard Wednesday patterns:
- Standard pattern: LEC weeks 1-3 PM, LEC week 4 AM, ADV week 4 PM
- PCAT-AM and DO-PM are exceptions (they win over Wednesday activities)

Changes:
1. Fix 22 templates: Week 4 PM should be ADV, not LEC
2. Add ADV requirements for templates that were missing them
3. Add full Wednesday patterns for 7 templates with no patterns
4. Remove Wednesday patterns from PCAT-AM, DO-PM (they're special)
"""

from typing import Sequence

from alembic import op


revision: str = "20260111_wed_pattern_audit"
down_revision: str | None = "20260111_flex_clinic_reqs"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Templates that need Week 4 PM changed from LEC to ADV
TEMPLATES_FIX_ADV = [
    "SM-AM",
    "SM-PM",  # Sports Med
    "C+N",
    "D+N",  # Combo NF
    "ADV-PM",
    "AT-AM",
    "AT-PM",
    "C-AM",
    "COLP-AM",
    "COLP-PM",
    "C-PM",
    "DFM-AM",
    "DFM-PM",
    "DO-PM",
    "HC-AM",
    "HC-PM",
    "PCAT-AM",
    "BTX-AM",
    "BTX-PM",
    "PR-PM",
    "VAS-AM",
    "VAS-PM",
]

# Templates that need full Wednesday patterns added (had none)
TEMPLATES_ADD_FULL = [
    "ACS-AM",
    "CARDIO",
    "ENDO",
    "GERI",
    "NEURO",
    "PEDS-CLIN",
    "SEL-MED",
]

# Templates that should NOT have Wednesday patterns (they win over LEC/ADV)
TEMPLATES_NO_WED = ["PCAT-AM", "DO-PM"]


def upgrade() -> None:
    # =========================================================================
    # Step 1: Fix Week 4 PM from LEC to ADV for 22 templates
    # =========================================================================
    templates_str = "', '".join(TEMPLATES_FIX_ADV)
    op.execute(f"""
        UPDATE weekly_patterns
        SET activity_type = 'advising'
        WHERE rotation_template_id IN (
            SELECT id FROM rotation_templates WHERE abbreviation IN ('{templates_str}')
        )
        AND day_of_week = 3
        AND time_of_day = 'PM'
        AND week_number = 4
        AND activity_type = 'lecture'
    """)

    # =========================================================================
    # Step 2: Add ADV requirements for templates that were missing them
    # =========================================================================
    op.execute(f"""
        INSERT INTO rotation_activity_requirements (
            id, rotation_template_id, activity_id,
            min_halfdays, max_halfdays, target_halfdays,
            applicable_weeks, applicable_weeks_hash,
            prefer_full_days, priority, created_at, updated_at
        )
        SELECT
            gen_random_uuid(), rt.id,
            (SELECT id FROM activities WHERE code = 'advising'),
            1, 1, 1, NULL, '5eefc5da-40d2-5afc-af3a-e7b6c2730b0d'::uuid,
            false, 100, NOW(), NOW()
        FROM rotation_templates rt
        WHERE rt.abbreviation IN ('{templates_str}')
        AND NOT EXISTS (
            SELECT 1 FROM rotation_activity_requirements rar
            WHERE rar.rotation_template_id = rt.id
            AND rar.activity_id = (SELECT id FROM activities WHERE code = 'advising')
        )
    """)

    # =========================================================================
    # Step 3: Decrement LEC requirements by 1 (Week 4 PM is now ADV)
    # =========================================================================
    op.execute(f"""
        UPDATE rotation_activity_requirements
        SET min_halfdays = min_halfdays - 1,
            max_halfdays = max_halfdays - 1,
            target_halfdays = target_halfdays - 1
        WHERE rotation_template_id IN (
            SELECT id FROM rotation_templates WHERE abbreviation IN ('{templates_str}')
        )
        AND activity_id = (SELECT id FROM activities WHERE code = 'lec')
        AND min_halfdays > 1
    """)

    # =========================================================================
    # Step 4: Add full Wednesday patterns for 7 templates with no patterns
    # =========================================================================
    full_str = "', '".join(TEMPLATES_ADD_FULL)

    # LEC weeks 1-3 PM
    for week in [1, 2, 3]:
        op.execute(f"""
            INSERT INTO weekly_patterns (
                id, rotation_template_id, day_of_week, time_of_day, week_number,
                activity_type, is_protected, created_at, updated_at
            )
            SELECT gen_random_uuid(), rt.id, 3, 'PM', {week}, 'lecture', true, NOW(), NOW()
            FROM rotation_templates rt
            WHERE rt.abbreviation IN ('{full_str}')
            AND NOT EXISTS (
                SELECT 1 FROM weekly_patterns wp
                WHERE wp.rotation_template_id = rt.id AND wp.week_number = {week}
            )
        """)

    # LEC week 4 AM
    op.execute(f"""
        INSERT INTO weekly_patterns (
            id, rotation_template_id, day_of_week, time_of_day, week_number,
            activity_type, is_protected, created_at, updated_at
        )
        SELECT gen_random_uuid(), rt.id, 3, 'AM', 4, 'lecture', true, NOW(), NOW()
        FROM rotation_templates rt
        WHERE rt.abbreviation IN ('{full_str}')
        AND NOT EXISTS (
            SELECT 1 FROM weekly_patterns wp
            WHERE wp.rotation_template_id = rt.id AND wp.week_number = 4 AND wp.time_of_day = 'AM'
        )
    """)

    # ADV week 4 PM
    op.execute(f"""
        INSERT INTO weekly_patterns (
            id, rotation_template_id, day_of_week, time_of_day, week_number,
            activity_type, is_protected, created_at, updated_at
        )
        SELECT gen_random_uuid(), rt.id, 3, 'PM', 4, 'advising', true, NOW(), NOW()
        FROM rotation_templates rt
        WHERE rt.abbreviation IN ('{full_str}')
        AND NOT EXISTS (
            SELECT 1 FROM weekly_patterns wp
            WHERE wp.rotation_template_id = rt.id AND wp.activity_type = 'advising'
        )
    """)

    # Add LEC and ADV requirements for 7 templates
    op.execute(f"""
        INSERT INTO rotation_activity_requirements (
            id, rotation_template_id, activity_id,
            min_halfdays, max_halfdays, target_halfdays,
            applicable_weeks, applicable_weeks_hash,
            prefer_full_days, priority, created_at, updated_at
        )
        SELECT
            gen_random_uuid(), rt.id,
            (SELECT id FROM activities WHERE code = 'lec'),
            4, 4, 4, NULL, '5eefc5da-40d2-5afc-af3a-e7b6c2730b0d'::uuid,
            false, 100, NOW(), NOW()
        FROM rotation_templates rt
        WHERE rt.abbreviation IN ('{full_str}')
        AND NOT EXISTS (
            SELECT 1 FROM rotation_activity_requirements rar
            WHERE rar.rotation_template_id = rt.id
            AND rar.activity_id = (SELECT id FROM activities WHERE code = 'lec')
        )
    """)

    op.execute(f"""
        INSERT INTO rotation_activity_requirements (
            id, rotation_template_id, activity_id,
            min_halfdays, max_halfdays, target_halfdays,
            applicable_weeks, applicable_weeks_hash,
            prefer_full_days, priority, created_at, updated_at
        )
        SELECT
            gen_random_uuid(), rt.id,
            (SELECT id FROM activities WHERE code = 'advising'),
            1, 1, 1, NULL, '5eefc5da-40d2-5afc-af3a-e7b6c2730b0d'::uuid,
            false, 100, NOW(), NOW()
        FROM rotation_templates rt
        WHERE rt.abbreviation IN ('{full_str}')
        AND NOT EXISTS (
            SELECT 1 FROM rotation_activity_requirements rar
            WHERE rar.rotation_template_id = rt.id
            AND rar.activity_id = (SELECT id FROM activities WHERE code = 'advising')
        )
    """)

    # =========================================================================
    # Step 5: Remove Wednesday patterns from PCAT-AM, DO-PM
    # =========================================================================
    no_wed_str = "', '".join(TEMPLATES_NO_WED)
    op.execute(f"""
        DELETE FROM weekly_patterns
        WHERE rotation_template_id IN (
            SELECT id FROM rotation_templates WHERE abbreviation IN ('{no_wed_str}')
        )
        AND day_of_week = 3
    """)

    # Remove LEC and ADV requirements from PCAT-AM, DO-PM
    op.execute(f"""
        DELETE FROM rotation_activity_requirements
        WHERE rotation_template_id IN (
            SELECT id FROM rotation_templates WHERE abbreviation IN ('{no_wed_str}')
        )
        AND activity_id IN (SELECT id FROM activities WHERE code IN ('lec', 'advising'))
    """)


def downgrade() -> None:
    # Downgrade is complex - would need to restore original state
    # For safety, just document what was changed
    pass
