"""Expand Block 12 block_assignments into template-derived HalfDayAssignments.

Uses the BlockAssignmentExpansionService to generate ~842 HDAs from rotation
templates. These serve as a baseline that the coordinator's handjam Excel
overwrites later (source priority: MANUAL > SOLVER > TEMPLATE).

The expansion service:
- Creates daily AM/PM assignments from rotation-specific patterns
- Respects existing absences (8 records overlapping Block 12)
- Skips locked slots (preload/manual)
- Applies 1-in-7 day-off rule
- Handles split-block residents (mid-block rotation transition)

Usage:
  1. Backup DB: ./checkpoint.sh pre_hda_expansion
  2. Run: backend/.venv/bin/python scripts/data/block12_import/expand_block12_hdas.py
  3. Verify: SELECT COUNT(*) FROM half_day_assignments
            WHERE date >= '2026-05-07' AND date <= '2026-06-03'
"""

import sys

# Add backend to path for imports
sys.path.insert(0, "backend")

from sqlalchemy import select, text

from app.db.session import SessionLocal
from app.models.half_day_assignment import HalfDayAssignment
from app.services.block_assignment_expansion_service import (
    BlockAssignmentExpansionService,
)

BLOCK_NUMBER = 12
ACADEMIC_YEAR = 2025
BLOCK_START = "2026-05-07"
BLOCK_END = "2026-06-03"


def count_existing_hdas(session):
    """Count HDAs already in Block 12 date range."""
    result = session.execute(
        text(
            "SELECT COUNT(*) FROM half_day_assignments "
            "WHERE date >= :start AND date <= :end"
        ),
        {"start": BLOCK_START, "end": BLOCK_END},
    )
    return result.scalar()


def count_hdas_by_source(session):
    """Count HDAs by source for Block 12."""
    result = session.execute(
        text(
            "SELECT source, COUNT(*) FROM half_day_assignments "
            "WHERE date >= :start AND date <= :end "
            "GROUP BY source ORDER BY source"
        ),
        {"start": BLOCK_START, "end": BLOCK_END},
    )
    return dict(result.fetchall())


def spot_check_nf_resident(session):
    """Spot-check a night float resident: should have OFF-AM / NF-PM pattern."""
    result = session.execute(
        text("""
            SELECT p.name, hda.date, hda.time_of_day,
                   a.display_abbreviation, hda.source
            FROM half_day_assignments hda
            JOIN people p ON hda.person_id = p.id
            LEFT JOIN activities a ON hda.activity_id = a.id
            JOIN block_assignments ba ON hda.block_assignment_id = ba.id
            JOIN rotation_templates rt ON ba.rotation_template_id = rt.id
            WHERE hda.date >= :start AND hda.date <= :end
              AND rt.abbreviation LIKE 'NF%%'
            ORDER BY p.name, hda.date, hda.time_of_day
            LIMIT 10
        """),
        {"start": BLOCK_START, "end": BLOCK_END},
    )
    return result.fetchall()


def main():
    print("=" * 70)
    print(f"Block {BLOCK_NUMBER} HDA Expansion (AY {ACADEMIC_YEAR})")
    print(f"Date range: {BLOCK_START} to {BLOCK_END}")
    print("=" * 70)

    session = SessionLocal()

    try:
        # Pre-expansion state
        existing_count = count_existing_hdas(session)
        print(f"\nPre-expansion HDA count (Block 12): {existing_count}")

        existing_by_source = count_hdas_by_source(session)
        if existing_by_source:
            for source, count in existing_by_source.items():
                print(f"  {source}: {count}")
        else:
            print("  (none)")

        # Run expansion
        print("\nRunning BlockAssignmentExpansionService.expand_block_assignments()...")
        service = BlockAssignmentExpansionService(session)
        assignments = service.expand_block_assignments(
            block_number=BLOCK_NUMBER,
            academic_year=ACADEMIC_YEAR,
            created_by="block12_hda_expansion",
            persist_half_day=True,
            apply_one_in_seven=True,
        )

        print(f"\nExpansion complete:")
        print(f"  Assignment records returned: {len(assignments)}")

        # Commit the session to persist HDAs
        session.commit()
        print("  Session committed successfully")

        # Post-expansion state
        new_count = count_existing_hdas(session)
        new_by_source = count_hdas_by_source(session)

        print(f"\nPost-expansion HDA count (Block 12): {new_count}")
        print(f"  New HDAs created: {new_count - existing_count}")
        for source, count in new_by_source.items():
            print(f"  {source}: {count}")

        # Spot-check NF residents
        print("\nSpot-check: Night Float residents (first 10 slots):")
        nf_rows = spot_check_nf_resident(session)
        if nf_rows:
            for name, dt, tod, activity, source in nf_rows:
                print(f"  {name[:25]:25s} {dt} {tod:2s} -> {activity or '(none)':10s} [{source}]")
        else:
            print("  (no NF residents found in HDAs)")

        # Summary
        print(f"\n{'=' * 70}")
        print(f"RESULT: {new_count - existing_count} new HDAs created for Block 12")
        print(f"Total Block 12 HDAs: {new_count}")
        print(f"Expected: ~842 (16 residents × 56 slots - absence days)")
        print(f"{'=' * 70}")

    except Exception as e:
        session.rollback()
        print(f"\nERROR: {type(e).__name__}: {e}")
        print("Session rolled back. No changes persisted.")
        sys.exit(1)
    finally:
        session.close()


if __name__ == "__main__":
    main()
