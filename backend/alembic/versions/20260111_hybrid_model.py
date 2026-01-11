"""Hybrid model: protected patterns + activity requirements

Revision ID: 20260111_hybrid_model
Revises: 20260111_halfblock_components
Create Date: 2026-01-11

Implements the hybrid scheduling model:
- Layer 1: Protected patterns define WHERE activities go (locked, solver cannot change)
- Layer 2: Activity requirements define HOW MANY half-days of each activity
- Layer 3: Solver fills remaining slots based on rotation's activity_type

Key changes:
1. Mark all weekly_patterns as protected (is_protected=true)
2. Create rotation_activity_requirements from pattern aggregates
3. Rename NF templates to follow naming convention
"""

from typing import Sequence

from alembic import op


revision: str = "20260111_hybrid_model"
down_revision: str | None = "20260111_halfblock_components"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # =========================================================================
    # Phase 1: Mark ALL patterns as protected
    # =========================================================================
    # All pre-loaded patterns define protected time - solver cannot change them
    op.execute("UPDATE weekly_patterns SET is_protected = true")

    # =========================================================================
    # Phase 2: Create activity requirements from pattern aggregates
    # =========================================================================
    # Derive requirements from patterns: count patterns by template+activity
    # min=max=target (exact counts required)
    #
    # Maps activity_type (in patterns) to activity code (in activities table):
    # - 'lecture' -> 'lec'
    # - 'advising' -> 'advising'
    # - 'fm_clinic' -> 'fm_clinic'
    # - 'fm_clinic_i' -> 'fm_clinic_i'

    # Create requirements for lecture patterns
    op.execute("""
        INSERT INTO rotation_activity_requirements (
            id, rotation_template_id, activity_id,
            min_halfdays, max_halfdays, target_halfdays,
            applicable_weeks, applicable_weeks_hash,
            prefer_full_days, priority, created_at, updated_at
        )
        SELECT
            gen_random_uuid(),
            wp.rotation_template_id,
            (SELECT id FROM activities WHERE code = 'lec'),
            COUNT(*),
            COUNT(*),
            COUNT(*),
            NULL,
            '550e8400-e29b-41d4-a716-446655440000'::uuid,
            false,
            100,
            NOW(), NOW()
        FROM weekly_patterns wp
        WHERE wp.activity_type = 'lecture'
        GROUP BY wp.rotation_template_id
    """)

    # Create requirements for advising patterns
    op.execute("""
        INSERT INTO rotation_activity_requirements (
            id, rotation_template_id, activity_id,
            min_halfdays, max_halfdays, target_halfdays,
            applicable_weeks, applicable_weeks_hash,
            prefer_full_days, priority, created_at, updated_at
        )
        SELECT
            gen_random_uuid(),
            wp.rotation_template_id,
            (SELECT id FROM activities WHERE code = 'advising'),
            COUNT(*),
            COUNT(*),
            COUNT(*),
            NULL,
            '550e8400-e29b-41d4-a716-446655440000'::uuid,
            false,
            100,
            NOW(), NOW()
        FROM weekly_patterns wp
        WHERE wp.activity_type = 'advising'
        GROUP BY wp.rotation_template_id
    """)

    # Create requirements for fm_clinic patterns
    op.execute("""
        INSERT INTO rotation_activity_requirements (
            id, rotation_template_id, activity_id,
            min_halfdays, max_halfdays, target_halfdays,
            applicable_weeks, applicable_weeks_hash,
            prefer_full_days, priority, created_at, updated_at
        )
        SELECT
            gen_random_uuid(),
            wp.rotation_template_id,
            (SELECT id FROM activities WHERE code = 'fm_clinic'),
            COUNT(*),
            COUNT(*),
            COUNT(*),
            NULL,
            '550e8400-e29b-41d4-a716-446655440000'::uuid,
            true,
            80,
            NOW(), NOW()
        FROM weekly_patterns wp
        WHERE wp.activity_type = 'fm_clinic'
        GROUP BY wp.rotation_template_id
    """)

    # Create requirements for fm_clinic_i patterns
    op.execute("""
        INSERT INTO rotation_activity_requirements (
            id, rotation_template_id, activity_id,
            min_halfdays, max_halfdays, target_halfdays,
            applicable_weeks, applicable_weeks_hash,
            prefer_full_days, priority, created_at, updated_at
        )
        SELECT
            gen_random_uuid(),
            wp.rotation_template_id,
            (SELECT id FROM activities WHERE code = 'fm_clinic_i'),
            COUNT(*),
            COUNT(*),
            COUNT(*),
            NULL,
            '550e8400-e29b-41d4-a716-446655440000'::uuid,
            true,
            80,
            NOW(), NOW()
        FROM weekly_patterns wp
        WHERE wp.activity_type = 'fm_clinic_i'
        GROUP BY wp.rotation_template_id
    """)

    # =========================================================================
    # Phase 3: Rename NF templates to follow naming convention
    # =========================================================================
    # Convention: NF-{SPECIALTY} or NF-{SPECIALTY}-{PGY}
    op.execute("""
        UPDATE rotation_templates SET abbreviation = 'NF-CARDIO'
        WHERE abbreviation = 'NF+';
    """)
    op.execute("""
        UPDATE rotation_templates SET abbreviation = 'NF-FMIT-PGY1'
        WHERE abbreviation = 'NFI';
    """)
    op.execute("""
        UPDATE rotation_templates SET abbreviation = 'NF-DERM-PGY2'
        WHERE abbreviation = 'NF-DERM';
    """)
    op.execute("""
        UPDATE rotation_templates SET abbreviation = 'NF-MED-SEL'
        WHERE abbreviation = 'NF-MED';
    """)
    op.execute("""
        UPDATE rotation_templates SET abbreviation = 'NF-NICU-PGY1'
        WHERE abbreviation = 'NF-NICU';
    """)


def downgrade() -> None:
    # =========================================================================
    # Revert Phase 3: Restore old NF template names
    # =========================================================================
    op.execute("""
        UPDATE rotation_templates SET abbreviation = 'NF+'
        WHERE abbreviation = 'NF-CARDIO';
    """)
    op.execute("""
        UPDATE rotation_templates SET abbreviation = 'NFI'
        WHERE abbreviation = 'NF-FMIT-PGY1';
    """)
    op.execute("""
        UPDATE rotation_templates SET abbreviation = 'NF-DERM'
        WHERE abbreviation = 'NF-DERM-PGY2';
    """)
    op.execute("""
        UPDATE rotation_templates SET abbreviation = 'NF-MED'
        WHERE abbreviation = 'NF-MED-SEL';
    """)
    op.execute("""
        UPDATE rotation_templates SET abbreviation = 'NF-NICU'
        WHERE abbreviation = 'NF-NICU-PGY1';
    """)

    # =========================================================================
    # Revert Phase 2: Delete generated activity requirements
    # =========================================================================
    # Delete requirements for activities used by patterns
    op.execute("""
        DELETE FROM rotation_activity_requirements
        WHERE activity_id IN (
            SELECT id FROM activities
            WHERE code IN ('lec', 'advising', 'fm_clinic', 'fm_clinic_i')
        )
    """)

    # =========================================================================
    # Revert Phase 1: Unprotect all patterns
    # =========================================================================
    op.execute("UPDATE weekly_patterns SET is_protected = false")
