# Block Regeneration Runbook (CP-SAT)

This runbook regenerates a single academic block using the canonical CP-SAT pipeline.
It assumes you have a valid local DB and have already taken a backup.

## Prerequisites

- Python 3.11+ environment for the backend.
- `DATABASE_URL` set in your shell or in `.env`.
- Local backup created (required before destructive clears).

## Script

Use:

```
python scripts/ops/block_regen.py --block 10 --academic-year 2026 --clear
```

Common flags:

- `--clear` clears `half_day_assignments` and `call_assignments` for the block,
  and removes next-day `pcat`/`do` slots.
- `--timeout 300` sets CP-SAT timeout (seconds).
- `--draft` creates a draft instead of writing live data.
- `--audit-only` prints counts without generating.
- `--skip-pcat-do-validate` skips the post-call integrity check.

## Notes

- The script prints a PII-free summary of counts by source and activity.
- The canonical pipeline uses CP-SAT for call + outpatient activity filling;
  inpatient coverage should be preloaded upstream.
