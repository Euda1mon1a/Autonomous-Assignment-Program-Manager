"""Add flexible clinic requirements for specialty rotations

Revision ID: 20260111_flex_clinic_reqs
Revises: 20260111_hybrid_model
Create Date: 2026-01-11

PGY-2/3 residents on specialty rotations have flexible clinic:
- They get 3 half-days of fm_clinic per block
- The solver decides WHERE to place them (not fixed to a specific day)
- This completes the hybrid model: protected patterns + flexible requirements

Rotations affected: DERM, ELEC, GYN, NEURO, ENDO, CARDIO, GERI, SURG,
PEDS-SUB, PEDS-CLIN, and other outpatient rotations without clinic patterns.
"""

from typing import Sequence

from alembic import op


revision: str = "20260111_flex_clinic_reqs"
down_revision: str | None = "20260111_hybrid_model"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add 3 half-day flexible clinic requirements for outpatient rotations
    # that don't already have clinic patterns (specialty rotations for PGY-2/3)
    op.execute("""
        INSERT INTO rotation_activity_requirements (
            id, rotation_template_id, activity_id,
            min_halfdays, max_halfdays, target_halfdays,
            applicable_weeks, applicable_weeks_hash,
            prefer_full_days, priority, created_at, updated_at
        )
        SELECT
            gen_random_uuid(),
            rt.id,
            (SELECT id FROM activities WHERE code = 'fm_clinic'),
            3, 3, 3,
            NULL,
            '5eefc5da-40d2-5afc-af3a-e7b6c2730b0d'::uuid,
            true,
            80,
            NOW(), NOW()
        FROM rotation_templates rt
        WHERE rt.activity_type = 'outpatient'
          AND rt.abbreviation NOT LIKE '%FAC%'
          AND NOT EXISTS (
              SELECT 1 FROM rotation_activity_requirements rar
              WHERE rar.rotation_template_id = rt.id
              AND rar.activity_id = (SELECT id FROM activities WHERE code = 'fm_clinic')
          )
    """)


def downgrade() -> None:
    # Remove the flexible clinic requirements for outpatient rotations
    # that were added by this migration (those without clinic patterns)
    op.execute("""
        DELETE FROM rotation_activity_requirements
        WHERE activity_id = (SELECT id FROM activities WHERE code = 'fm_clinic')
          AND rotation_template_id IN (
              SELECT rt.id FROM rotation_templates rt
              WHERE rt.activity_type = 'outpatient'
                AND rt.abbreviation NOT LIKE '%FAC%'
                AND NOT EXISTS (
                    SELECT 1 FROM weekly_patterns wp
                    WHERE wp.rotation_template_id = rt.id
                    AND wp.activity_type = 'fm_clinic'
                )
          )
    """)
