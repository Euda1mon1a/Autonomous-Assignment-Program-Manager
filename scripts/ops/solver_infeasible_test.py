#!/usr/bin/env python3
"""
Run a CP-SAT infeasibility test without writing to live schedule data.

This keeps half-day constraints enabled (which the engine normally disables)
so the solver should return INFEASIBLE. Uses draft mode to avoid live writes.
A failure snapshot is written to /tmp unless SCHEDULE_FAILURE_SNAPSHOT_DIR is set.

Usage:
    python3.11 scripts/ops/solver_infeasible_test.py --block 10 --academic-year 2026
    python3.11 scripts/ops/solver_infeasible_test.py --block 10 --academic-year 2026 --timeout 30
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = REPO_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.db.session import SessionLocal  # noqa: E402
from app.scheduling.constraints import ConstraintManager  # noqa: E402
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
        key = key.strip()
        existing = os.environ.get(key)
        if key == "CORS_ORIGINS":
            if not existing or '"' not in existing:
                os.environ[key] = value
            continue
        if not existing:
            os.environ[key] = value

    if not os.environ.get("DATABASE_URL") and os.environ.get("DB_PASSWORD"):
        os.environ["DATABASE_URL"] = (
            f"postgresql://scheduler:{os.environ['DB_PASSWORD']}@localhost:5432/"
            "residency_scheduler"
        )


def _force_constraints(manager: ConstraintManager, keep_enabled: set[str]) -> None:
    original_disable = manager.disable

    def _disable(name: str) -> ConstraintManager:
        if name in keep_enabled:
            return manager
        return original_disable(name)

    manager.disable = _disable  # type: ignore[assignment]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run CP-SAT infeasibility test")
    parser.add_argument("--block", type=int, required=True)
    parser.add_argument("--academic-year", type=int, required=True)
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument(
        "--snapshot-dir",
        type=str,
        default=None,
        help="Override snapshot output dir (default /tmp)",
    )

    args = parser.parse_args()
    _load_env()

    if args.snapshot_dir:
        os.environ["SCHEDULE_FAILURE_SNAPSHOT_DIR"] = args.snapshot_dir

    block_dates = get_block_dates(args.block, args.academic_year)

    keep_enabled = {
        "OnePersonPerBlock",
        "MaxPhysiciansInClinic",
        "WednesdayAMInternOnly",
        "WednesdayPMSingleFaculty",
        "InvertedWednesday",
        "ProtectedSlot",
        "1in7Rule",
        "80HourRule",
    }

    session = SessionLocal()
    try:
        manager = ConstraintManager.create_default()
        _force_constraints(manager, keep_enabled)

        engine = SchedulingEngine(
            session,
            block_dates.start_date,
            block_dates.end_date,
            constraint_manager=manager,
        )
        result = engine.generate(
            algorithm="cp_sat",
            timeout_seconds=args.timeout,
            block_number=args.block,
            academic_year=args.academic_year,
            create_draft=True,
        )

        print(f"STATUS: {result.get('status')}")
        print(f"MESSAGE: {result.get('message')}")
        if result.get("pre_solver_validation"):
            print("PRE_SOLVER_VALIDATION:", result.get("pre_solver_validation"))
    finally:
        session.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
