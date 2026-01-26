#!/usr/bin/env python3
"""
Regenerate a single academic block using the canonical CP-SAT pipeline.

Workflow:
1) Optional clear of half_day_assignments + call_assignments for the block.
2) Run SchedulingEngine.generate() with CP-SAT (half-day pipeline).
3) Print a small, PII-free summary for quick audit.

Usage:
    python scripts/ops/block_regen.py --block 10 --academic-year 2026 --clear
    python scripts/ops/block_regen.py --block 10 --academic-year 2026 --clear --timeout 300
    python scripts/ops/block_regen.py --block 10 --academic-year 2026 --audit-only
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import timedelta
from pathlib import Path

from sqlalchemy import func, select

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = REPO_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.db.session import SessionLocal  # noqa: E402
from app.models.activity import Activity  # noqa: E402
from app.models.call_assignment import CallAssignment  # noqa: E402
from app.models.half_day_assignment import HalfDayAssignment  # noqa: E402
from app.scheduling.engine import SchedulingEngine  # noqa: E402
from app.utils.academic_blocks import get_block_dates  # noqa: E402


def _load_env() -> None:
    env_path = REPO_ROOT / ".env"
    if not env_path.exists():
        return

    for raw in env_path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key.strip(), value)

    if "DATABASE_URL" not in os.environ and "DB_PASSWORD" in os.environ:
        os.environ["DATABASE_URL"] = (
            f"postgresql://scheduler:{os.environ['DB_PASSWORD']}@localhost:5432/"
            "residency_scheduler"
        )


def _clear_block(session, start_date, end_date) -> dict[str, int]:
    next_day = end_date + timedelta(days=1)

    pcat_do_ids = [
        row[0]
        for row in session.execute(
            select(Activity.id).where(Activity.code.in_(["pcat", "do"]))
        ).all()
    ]

    hda_deleted = session.query(HalfDayAssignment).filter(
        HalfDayAssignment.date >= start_date,
        HalfDayAssignment.date <= end_date,
    ).delete(synchronize_session=False)

    call_deleted = session.query(CallAssignment).filter(
        CallAssignment.date >= start_date,
        CallAssignment.date <= end_date,
    ).delete(synchronize_session=False)

    pcat_do_next_deleted = 0
    if pcat_do_ids:
        pcat_do_next_deleted = session.query(HalfDayAssignment).filter(
            HalfDayAssignment.date == next_day,
            HalfDayAssignment.activity_id.in_(pcat_do_ids),
        ).delete(synchronize_session=False)

    session.commit()
    return {
        "half_day_assignments": hda_deleted,
        "call_assignments": call_deleted,
        "pcat_do_next_day": pcat_do_next_deleted,
    }


def _summary_counts(session, start_date, end_date) -> dict[str, int]:
    next_day = end_date + timedelta(days=1)

    totals = {
        "half_day_assignments": session.query(HalfDayAssignment)
        .filter(HalfDayAssignment.date >= start_date, HalfDayAssignment.date <= end_date)
        .count(),
        "call_assignments": session.query(CallAssignment)
        .filter(CallAssignment.date >= start_date, CallAssignment.date <= end_date)
        .count(),
    }

    source_rows = session.execute(
        select(HalfDayAssignment.source, func.count())
        .where(HalfDayAssignment.date >= start_date, HalfDayAssignment.date <= end_date)
        .group_by(HalfDayAssignment.source)
    ).all()
    for source, count in source_rows:
        totals[f"hda_source_{source}"] = int(count)

    activity_rows = session.execute(
        select(Activity.code, func.count())
        .join(HalfDayAssignment, HalfDayAssignment.activity_id == Activity.id)
        .where(HalfDayAssignment.date >= start_date, HalfDayAssignment.date <= end_date)
        .where(Activity.code.in_(["at", "pcat", "do"]))
        .group_by(Activity.code)
    ).all()
    for code, count in activity_rows:
        totals[f"hda_activity_{code}"] = int(count)

    pcat_do_ids = [
        row[0]
        for row in session.execute(
            select(Activity.id).where(Activity.code.in_(["pcat", "do"]))
        ).all()
    ]
    if pcat_do_ids:
        totals["pcat_do_next_day"] = (
            session.query(HalfDayAssignment)
            .filter(
                HalfDayAssignment.date == next_day,
                HalfDayAssignment.activity_id.in_(pcat_do_ids),
            )
            .count()
        )

    return totals


def main() -> int:
    parser = argparse.ArgumentParser(description="Regenerate a single block (CP-SAT)")
    parser.add_argument("--block", type=int, required=True)
    parser.add_argument("--academic-year", type=int, required=True)
    parser.add_argument("--timeout", type=float, default=300.0)
    parser.add_argument("--clear", action="store_true", help="Clear block data first")
    parser.add_argument("--audit-only", action="store_true", help="Skip generation")
    parser.add_argument(
        "--draft",
        action="store_true",
        help="Create a draft instead of writing live data",
    )
    parser.add_argument(
        "--skip-pcat-do-validate",
        action="store_true",
        help="Skip PCAT/DO integrity check",
    )

    args = parser.parse_args()
    _load_env()

    block_number = args.block
    academic_year = args.academic_year
    block_dates = get_block_dates(block_number, academic_year)
    start_date, end_date = block_dates.start_date, block_dates.end_date

    session = SessionLocal()
    try:
        print(f"Block {block_number} AY{academic_year}: {start_date} to {end_date}")

        if args.clear:
            cleared = _clear_block(session, start_date, end_date)
            print(
                "Cleared: "
                f"half_day={cleared['half_day_assignments']}, "
                f"call={cleared['call_assignments']}, "
                f"pcat_do_next_day={cleared['pcat_do_next_day']}"
            )

        if not args.audit_only:
            engine = SchedulingEngine(session, start_date, end_date)
            result = engine.generate(
                algorithm="cp_sat",
                timeout_seconds=args.timeout,
                expand_block_assignments=True,
                block_number=block_number,
                academic_year=academic_year,
                create_draft=args.draft,
                validate_pcat_do=not args.skip_pcat_do_validate,
                preserve_fmit=True,
                preserve_resident_inpatient=True,
                preserve_absence=True,
            )
            print(f"STATUS: {result.get('status')}")
            print(f"MESSAGE: {result.get('message')}")
            print(f"TOTAL_ASSIGNED: {result.get('total_assigned')}")
            print(f"RUN_ID: {result.get('run_id')}")
            if result.get("pcat_do_issues"):
                print(f"PCAT_DO_ISSUES: {result.get('pcat_do_issues')}")

        counts = _summary_counts(session, start_date, end_date)
        print("SUMMARY COUNTS:")
        for key in sorted(counts.keys()):
            print(f"  {key}: {counts[key]}")

        return 0
    finally:
        session.close()


if __name__ == "__main__":
    raise SystemExit(main())
