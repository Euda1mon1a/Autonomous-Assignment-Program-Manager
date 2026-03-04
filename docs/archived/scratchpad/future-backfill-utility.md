# Future Consideration: Preload Activity ID Backfill Utility

> **Status:** Archived for future consideration
> **Date:** 2026-01-21
> **Decision:** Prefer fail-loud over silent backfill

## Context

During Session 126, a backfill script was created by Codex to fix missing `activity_id` values in `half_day_assignments`. However, the preferred approach is to fix the root cause so assignments are created correctly from the start.

## Root Cause Fixes Applied (Session 125-126)

Instead of backfilling, we fixed the creation logic:

1. **`_lookup_activity_by_abbreviation()`** - Falls back from `W-AM` → `W` for absence templates
2. **`time_off` source detection** - Activities with `activity_category == "time_off"` get `source=preload`
3. **NF/PedNF weekend patterns** - Return `("W", "W")` for weekends
4. **Compound rotation weekends** - `_load_compound_rotation_weekends()` handles NEURO-1ST-NF-2ND patterns

## Backfill Script (For Emergency Use Only)

If needed in the future, here's the utility pattern:

```python
#!/usr/bin/env python3
"""
Backfill missing activity_id values for preload half-day assignments.

This re-runs SyncPreloadService for a block/year and updates any existing
preload slots that are missing activity_id.

Usage:
    python backend/scripts/backfill_preload_activity_ids.py --block 10 --year 2025
    python backend/scripts/backfill_preload_activity_ids.py --block 10 --year 2025 --dry-run
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import SessionLocal
from app.services.sync_preload_service import SyncPreloadService


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Backfill missing activity_id for preload half-day assignments"
    )
    parser.add_argument("--block", type=int, required=True, help="Block number")
    parser.add_argument(
        "--year",
        type=int,
        required=True,
        help="Academic year (e.g., 2025 for AY 2025-2026)",
    )
    parser.add_argument(
        "--include-faculty-call",
        action="store_true",
        help="Also load faculty call PCAT/DO from existing CallAssignments",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without committing changes",
    )

    args = parser.parse_args()

    db = SessionLocal()
    try:
        service = SyncPreloadService(db)
        updated = service.load_all_preloads(
            args.block,
            args.year,
            skip_faculty_call=not args.include_faculty_call,
        )
        if args.dry_run:
            db.rollback()
            print(f"Dry run: would update/create {updated} preload slots")
        else:
            db.commit()
            print(f"Updated/created {updated} preload slots")
        return 0
    except Exception as exc:
        db.rollback()
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
```

## When to Use

Only use this if:
1. A bug in preload creation caused widespread missing `activity_id` values
2. Re-generating the schedule would be disruptive
3. You've already fixed the root cause bug

## Preferred Approach

Always prefer fixing the creation logic so data is correct from the start. Things should fail loudly if `activity_id` is missing rather than silently backfilling later.
