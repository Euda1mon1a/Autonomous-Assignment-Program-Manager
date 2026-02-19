"""Pre-flight validation for block schedule imports.

Reusable script that catches common gotchas before a handjam import:
1. block_assignments exist for the target block
2. No deployed/absent faculty have supervising assignments
3. Federal holidays are flagged in blocks table
4. No graduated/departed residents have stale assignments
5. All residents in block_assignments exist in people table
6. Split-block residents have secondary_rotation_template_id set

Designed to be run before any block import (not just Block 12).

Usage:
  backend/.venv/bin/python scripts/data/block_import_preflight.py 12
  backend/.venv/bin/python scripts/data/block_import_preflight.py 13 --academic-year 2025
"""

import argparse
import sys
from dataclasses import dataclass, field
from datetime import date

import psycopg2

sys.path.insert(0, "backend")
from app.utils.academic_blocks import get_block_dates
from app.utils.holidays import get_federal_holidays

CONN = "dbname=residency_scheduler user=scheduler host=localhost"


@dataclass
class PreflightResult:
    """Result of a pre-flight check."""

    name: str
    passed: bool
    details: list[str] = field(default_factory=list)
    severity: str = "INFO"  # INFO, WARNING, CRITICAL


def check_block_assignments_exist(cur, block_num: int, ay: int) -> PreflightResult:
    """Check that block_assignments exist for the target block."""
    cur.execute(
        "SELECT COUNT(*) FROM block_assignments WHERE block_number = %s AND academic_year = %s",
        (block_num, ay),
    )
    count = cur.fetchone()[0]

    if count == 0:
        return PreflightResult(
            name="block_assignments exist",
            passed=False,
            details=[f"No block_assignments found for Block {block_num} AY {ay}"],
            severity="CRITICAL",
        )

    # Check that all referenced residents exist in people table
    cur.execute("""
        SELECT ba.id, ba.resident_id
        FROM block_assignments ba
        LEFT JOIN people p ON ba.resident_id = p.id
        WHERE ba.block_number = %s AND ba.academic_year = %s
          AND p.id IS NULL
    """, (block_num, ay))
    orphans = cur.fetchall()

    details = [f"{count} block_assignments found"]
    if orphans:
        details.append(f"WARNING: {len(orphans)} block_assignments reference non-existent residents")
        return PreflightResult(
            name="block_assignments exist",
            passed=False,
            details=details,
            severity="CRITICAL",
        )

    return PreflightResult(name="block_assignments exist", passed=True, details=details)


def check_block_assignment_roster(cur, block_num: int, ay: int) -> PreflightResult:
    """List block_assignments for human review."""
    cur.execute("""
        SELECT p.name, rt.abbreviation, rt2.abbreviation
        FROM block_assignments ba
        JOIN people p ON ba.resident_id = p.id
        JOIN rotation_templates rt ON ba.rotation_template_id = rt.id
        LEFT JOIN rotation_templates rt2 ON ba.secondary_rotation_template_id = rt2.id
        WHERE ba.block_number = %s AND ba.academic_year = %s
        ORDER BY p.name
    """, (block_num, ay))
    rows = cur.fetchall()

    details = []
    for name, rot, sec in rows:
        sec_str = f" / {sec}" if sec else ""
        details.append(f"  {name:30s} -> {rot}{sec_str}")

    return PreflightResult(
        name="block_assignment roster",
        passed=True,
        details=details,
    )


def check_deployed_faculty(cur, block_start: date, block_end: date) -> PreflightResult:
    """Check that no deployed faculty have assignments in the block."""
    cur.execute("""
        SELECT DISTINCT p.name, a2.start_date, a2.end_date, COUNT(a.id) as asn_count
        FROM assignments a
        JOIN blocks b ON a.block_id = b.id
        JOIN people p ON a.person_id = p.id
        JOIN absences a2 ON a2.person_id = p.id
        WHERE a2.absence_type = 'deployment'
          AND b.date >= %s AND b.date <= %s
          AND b.date >= a2.start_date AND b.date <= a2.end_date
        GROUP BY p.name, a2.start_date, a2.end_date
    """, (block_start, block_end))
    rows = cur.fetchall()

    if rows:
        details = []
        for name, dep_start, dep_end, count in rows:
            details.append(f"  {name}: {count} assignments during deployment ({dep_start} – {dep_end})")
        return PreflightResult(
            name="deployed faculty check",
            passed=False,
            details=details,
            severity="WARNING",
        )

    return PreflightResult(
        name="deployed faculty check",
        passed=True,
        details=["No deployed faculty have assignments in this block"],
    )


def check_holidays_flagged(cur, block_start: date, block_end: date) -> PreflightResult:
    """Check that federal holidays within the block are flagged."""
    # Get federal holidays in the block's calendar years.
    # Include adjacent years to catch observed New Year's Day on Dec 31
    # (when Jan 1 falls on Saturday, OPM observes it on Friday Dec 31).
    years_to_check = {block_start.year, block_end.year, block_start.year - 1, block_end.year + 1}
    holidays_to_check = []
    seen_dates = set()
    for year in sorted(years_to_check):
        for holiday in get_federal_holidays(year):
            if block_start <= holiday.date <= block_end and holiday.date not in seen_dates:
                holidays_to_check.append(holiday)
                seen_dates.add(holiday.date)

    if not holidays_to_check:
        return PreflightResult(
            name="holidays flagged",
            passed=True,
            details=["No federal holidays fall within this block"],
        )

    details = []
    all_flagged = True
    for holiday in holidays_to_check:
        # Check ALL half-day rows (AM + PM) — both must be flagged
        cur.execute(
            "SELECT time_of_day, is_holiday, holiday_name FROM blocks WHERE date = %s ORDER BY time_of_day",
            (holiday.date,),
        )
        rows = cur.fetchall()
        if not rows:
            details.append(f"  {holiday.date} ({holiday.name}): NO BLOCK RECORD")
            all_flagged = False
        else:
            unflagged = [tod for tod, is_hol, _ in rows if not is_hol]
            if unflagged:
                slots = ", ".join(unflagged)
                details.append(f"  {holiday.date} ({holiday.name}): NOT FLAGGED on {slots}")
                all_flagged = False
            else:
                hol_name = rows[0][2] or holiday.name
                details.append(f"  {holiday.date} ({holiday.name}): OK (flagged as '{hol_name}')")

    return PreflightResult(
        name="holidays flagged",
        passed=all_flagged,
        details=details,
        severity="WARNING" if not all_flagged else "INFO",
    )


def check_stale_graduated_residents(cur, block_num: int, ay: int, block_start: date, block_end: date) -> PreflightResult:
    """Check for assignments belonging to residents not in block_assignments."""
    # Get residents who SHOULD be in this block
    cur.execute(
        "SELECT resident_id FROM block_assignments WHERE block_number = %s AND academic_year = %s",
        (block_num, ay),
    )
    expected_residents = {row[0] for row in cur.fetchall()}

    # Get residents who HAVE assignments in this block
    cur.execute("""
        SELECT DISTINCT a.person_id, p.name, COUNT(a.id) as asn_count
        FROM assignments a
        JOIN blocks b ON a.block_id = b.id
        JOIN people p ON a.person_id = p.id
        WHERE b.date >= %s AND b.date <= %s
          AND a.role = 'primary'
          AND a.person_id NOT IN (
              SELECT resident_id FROM block_assignments
              WHERE block_number = %s AND academic_year = %s
          )
        GROUP BY a.person_id, p.name
    """, (block_start, block_end, block_num, ay))
    stale = cur.fetchall()

    if stale:
        details = []
        for pid, name, count in stale:
            details.append(f"  {name}: {count} primary assignments but NO block_assignment")
        return PreflightResult(
            name="stale/graduated resident check",
            passed=False,
            details=details,
            severity="WARNING",
        )

    return PreflightResult(
        name="stale/graduated resident check",
        passed=True,
        details=["All residents with assignments have corresponding block_assignments"],
    )


def check_split_block_completeness(cur, block_num: int, ay: int) -> PreflightResult:
    """Check split-block residents have secondary_rotation_template_id set."""
    cur.execute("""
        SELECT p.name, rt.abbreviation,
               ba.secondary_rotation_template_id IS NOT NULL as has_secondary,
               rt2.abbreviation as secondary_abbr
        FROM block_assignments ba
        JOIN people p ON ba.resident_id = p.id
        JOIN rotation_templates rt ON ba.rotation_template_id = rt.id
        LEFT JOIN rotation_templates rt2 ON ba.secondary_rotation_template_id = rt2.id
        WHERE ba.block_number = %s AND ba.academic_year = %s
        ORDER BY p.name
    """, (block_num, ay))
    rows = cur.fetchall()

    details = []
    split_count = 0
    for name, rot, has_sec, sec_abbr in rows:
        if has_sec:
            split_count += 1
            details.append(f"  {name}: {rot} / {sec_abbr} (split-block)")

    if split_count == 0:
        details.append("No split-block residents found (all single-rotation)")

    return PreflightResult(
        name="split-block completeness",
        passed=True,
        details=details,
    )


def check_block_slots_exist(cur, block_start: date, block_end: date) -> PreflightResult:
    """Verify blocks table has slots for the entire date range."""
    expected_days = (block_end - block_start).days + 1
    expected_slots = expected_days * 2  # AM + PM

    cur.execute(
        "SELECT COUNT(*) FROM blocks WHERE date >= %s AND date <= %s",
        (block_start, block_end),
    )
    actual = cur.fetchone()[0]

    if actual != expected_slots:
        return PreflightResult(
            name="block slots exist",
            passed=False,
            details=[f"Expected {expected_slots} slots ({expected_days} days × 2), found {actual}"],
            severity="CRITICAL",
        )

    return PreflightResult(
        name="block slots exist",
        passed=True,
        details=[f"{actual} slots found ({expected_days} days × 2) — correct"],
    )


def run_preflight(block_num: int, ay: int) -> list[PreflightResult]:
    """Run all pre-flight checks for a block."""
    block_dates = get_block_dates(block_num, ay)
    block_start = block_dates.start_date
    block_end = block_dates.end_date

    conn = psycopg2.connect(CONN)
    cur = conn.cursor()

    results = []
    results.append(check_block_slots_exist(cur, block_start, block_end))
    results.append(check_block_assignments_exist(cur, block_num, ay))
    results.append(check_block_assignment_roster(cur, block_num, ay))
    results.append(check_holidays_flagged(cur, block_start, block_end))
    results.append(check_deployed_faculty(cur, block_start, block_end))
    results.append(check_stale_graduated_residents(cur, block_num, ay, block_start, block_end))
    results.append(check_split_block_completeness(cur, block_num, ay))

    cur.close()
    conn.close()

    return results


def main():
    parser = argparse.ArgumentParser(description="Pre-flight validation for block schedule imports")
    parser.add_argument("block_number", type=int, help="Block number (1-13)")
    parser.add_argument("--academic-year", type=int, default=2025, help="Academic year (default: 2025)")
    args = parser.parse_args()

    block_num = args.block_number
    ay = args.academic_year

    block_dates = get_block_dates(block_num, ay)
    print("=" * 70)
    print(f"PRE-FLIGHT: Block {block_num} (AY {ay})")
    print(f"Date range: {block_dates.start_date} – {block_dates.end_date} ({block_dates.duration_days} days)")
    print("=" * 70)

    results = run_preflight(block_num, ay)

    # Display results
    critical_failures = 0
    warnings = 0

    for r in results:
        icon = "PASS" if r.passed else "FAIL"
        severity = f" [{r.severity}]" if not r.passed else ""
        print(f"\n  [{icon}]{severity} {r.name}")
        for detail in r.details:
            print(f"    {detail}")

        if not r.passed:
            if r.severity == "CRITICAL":
                critical_failures += 1
            else:
                warnings += 1

    # Summary
    print(f"\n{'=' * 70}")
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    print(f"RESULTS: {passed}/{total} passed, {critical_failures} critical, {warnings} warnings")

    if critical_failures > 0:
        print("STATUS: BLOCKED — fix critical issues before import")
        sys.exit(1)
    elif warnings > 0:
        print("STATUS: PROCEED WITH CAUTION — review warnings")
        sys.exit(0)
    else:
        print("STATUS: READY FOR IMPORT")
        sys.exit(0)


if __name__ == "__main__":
    main()
