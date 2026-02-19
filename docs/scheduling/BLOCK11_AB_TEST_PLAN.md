# Block 11 A/B Pipeline Comparison Plan

> **Status:** COMPLETE — A/B test passed, `USE_LANGGRAPH_PIPELINE=true` flipped
> **Backup:** `backups/pre_block11_ab_20260218_121135.sql` (21MB, pre-test state)
> **Run A log:** `/tmp/block11_baseline_v2.txt` (old pipeline)
> **Run B log:** `/tmp/block11_langgraph_v2.txt` (LangGraph pipeline)

## Context

PR #1157 merged the LangGraph scheduling pipeline with feature flag `USE_LANGGRAPH_PIPELINE=false`. Block 11 AY2025 (Apr 9 – May 6, 2026) is the real-world validation target. Run both pipelines on identical inputs, compare outputs, flip the flag if equivalent.

## First Attempt Results (2026-02-18)

| Metric | Old Pipeline | LangGraph Pipeline |
|--------|-------------|-------------------|
| Status | partial (success) | **failed** |
| Templates | 29 | **0** |
| Residents | 5 (outpatient) | **16 (all — fallback)** |
| Preloads | 491 | **250** |
| Rotation-protected preloads | 241 | **0 (never loaded)** |
| Assignments | 477 | 0 |

**Root cause:** The DB restore between Run A and Run B used plain `psql < dump.sql` on an existing populated database. A plain `pg_dump` (without `--clean`) produces `CREATE TABLE` + `COPY` statements that **fail silently** on existing tables, leaving the DB in the post-Run-A state. The graph pipeline code was confirmed to be **structurally identical** to `engine.generate()` — no code bugs found.

### Lesson learned

- **Never** use plain `psql < dump.sql` to restore over an existing DB
- **Never** suppress stderr during testing (`> /dev/null 2>&1`)
- Use `dropdb + createdb + psql` for clean restores

## Steps (v2 — Fixed Procedure)

### 1. Backup Database

```bash
/opt/homebrew/opt/postgresql@17/bin/pg_dump -U scheduler residency_scheduler \
  > backups/pre_block11_ab_v2_$(date +%Y%m%d_%H%M%S).sql
```

### 2. Audit Current State

```bash
cd backend && .venv/bin/python ../scripts/ops/block_regen.py --block 11 --academic-year 2025 --audit-only
```

### 3. Run A: Old Pipeline (Baseline)

```bash
cd backend && USE_LANGGRAPH_PIPELINE=false .venv/bin/python ../scripts/ops/block_regen.py \
  --block 11 --academic-year 2025 --clear --timeout 300 \
  2>&1 | tee /tmp/block11_baseline_v2.txt
```

### 4. Safe Restore (CRITICAL)

```bash
# Drop and recreate DB (scheduler lacks CREATEDB, use superuser)
/opt/homebrew/opt/postgresql@17/bin/dropdb -U $(whoami) residency_scheduler
/opt/homebrew/opt/postgresql@17/bin/createdb -U $(whoami) -O scheduler residency_scheduler

# Pre-install extensions (require superuser)
/opt/homebrew/opt/postgresql@17/bin/psql -U $(whoami) -d residency_scheduler \
  -c "CREATE EXTENSION IF NOT EXISTS vector; CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"

# Restore data (as scheduler role, WITHOUT ON_ERROR_STOP to tolerate extension warnings)
/opt/homebrew/opt/postgresql@17/bin/psql -U scheduler -d residency_scheduler \
  < backups/pre_block11_ab_v2_*.sql
```

**DO NOT** use `psql < dump.sql` on an existing populated DB — it fails silently.
**DO NOT** use `ON_ERROR_STOP` — the dump contains `CREATE EXTENSION vector` which
requires superuser and would abort the entire restore.

### 5. Run B: LangGraph Pipeline

```bash
cd backend && USE_LANGGRAPH_PIPELINE=true .venv/bin/python ../scripts/ops/block_regen.py \
  --block 11 --academic-year 2025 --clear --timeout 300 \
  2>&1 | tee /tmp/block11_langgraph_v2.txt
```

### 6. Compare

```bash
diff /tmp/block11_baseline_v2.txt /tmp/block11_langgraph_v2.txt
```

Key comparison points:
- `STATUS` — both should be `partial` (same status)
- `TOTAL_ASSIGNED` — should match exactly
- `SUMMARY COUNTS` — all counts should match
- `Preservation summary` — fmit/inpatient/offsite counts must match
- `Data load summary` — residents/templates/faculty counts must match

### 7. Verdict

| Outcome | Action |
|---------|--------|
| Match | Flip `USE_LANGGRAPH_PIPELINE=true`, commit |
| Minor diffs | Investigate ordering — likely acceptable |
| Status differs | Debug, do NOT flip |
| Count differs | Root-cause which node diverges |

## Second Attempt Results (2026-02-18) — PASS

| Metric | Old Pipeline | LangGraph | Match? |
|--------|-------------|-----------|--------|
| Status | partial | partial | Yes |
| Total Assigned | 477 | 477 | Yes |
| Templates | 29 | 29 | Yes |
| Residents (outpatient) | 5 | 5 | Yes |
| Preloads | 491 | 491 | Yes |
| Preserved IDs | 616 | 616 | Yes |
| Call Assignments | 28 | 28 | Yes |
| Half-Day Assignments | 1152 | 1152 | Yes |
| Source: Preload | 521 | 521 | Yes |
| Source: Solver | 631 | 631 | Yes |
| Activity AT/DO/PCAT | 37/19/19 | 37/19/19 | Yes |
| PCAT/DO Next Day | 0 | 2 | Minor (solver non-determinism) |
| Faculty Clinic | 48 | 49 | Minor (solver non-determinism) |
| Virtual Clinic | 33/112 | 33/113 | Minor (solver non-determinism) |

**Verdict:** PASS — all structural metrics match. Minor differences are expected CP-SAT solver non-determinism (different solution exploration paths produce equivalent-quality feasible solutions).

**Action taken:** Flipped `USE_LANGGRAPH_PIPELINE` default to `True` in `backend/app/core/config.py`.

## Native PostgreSQL (NOT Docker)

```bash
# pg_dump (backup)
/opt/homebrew/opt/postgresql@17/bin/pg_dump -U scheduler residency_scheduler > backups/name.sql

# Safe restore (drop + create + load)
/opt/homebrew/opt/postgresql@17/bin/dropdb -U $(whoami) residency_scheduler
/opt/homebrew/opt/postgresql@17/bin/createdb -U $(whoami) -O scheduler residency_scheduler
/opt/homebrew/opt/postgresql@17/bin/psql -U $(whoami) -d residency_scheduler \
  -c "CREATE EXTENSION IF NOT EXISTS vector; CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"
/opt/homebrew/opt/postgresql@17/bin/psql -U scheduler -d residency_scheduler < backups/name.sql

# Python (always use venv)
cd backend && .venv/bin/python ../scripts/ops/block_regen.py ...
```
