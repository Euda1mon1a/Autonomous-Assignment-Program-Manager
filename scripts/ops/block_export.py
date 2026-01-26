#!/usr/bin/env python3
"""
Export a single academic block using the canonical JSON → XLSX pipeline.

Usage:
    python scripts/ops/block_export.py --block 10 --academic-year 2026
    python scripts/ops/block_export.py --block 10 --academic-year 2026 --output /tmp/block10.xlsx
    python scripts/ops/block_export.py --block 10 --academic-year 2026 --no-faculty
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
from app.services.canonical_schedule_export_service import (  # noqa: E402
    CanonicalScheduleExportService,
)


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


def main() -> int:
    parser = argparse.ArgumentParser(description="Export a block schedule (canonical)")
    parser.add_argument("--block", type=int, required=True)
    parser.add_argument("--academic-year", type=int, required=True)
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to write XLSX (defaults to Block{N}_EXPORT.xlsx in repo root)",
    )
    parser.add_argument(
        "--no-faculty",
        action="store_true",
        help="Exclude faculty rows from export",
    )

    args = parser.parse_args()
    _load_env()

    block_number = args.block
    academic_year = args.academic_year
    output_path = (
        Path(args.output)
        if args.output
        else REPO_ROOT / f"Block{block_number}_EXPORT.xlsx"
    )

    session = SessionLocal()
    try:
        service = CanonicalScheduleExportService(session)
        service.export_block_xlsx(
            block_number=block_number,
            academic_year=academic_year,
            include_faculty=not args.no_faculty,
            output_path=output_path,
        )
        print(f"Exported block {block_number} AY{academic_year} to {output_path}")
    finally:
        session.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
