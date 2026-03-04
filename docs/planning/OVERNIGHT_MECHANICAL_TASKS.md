# Overnight Mechanical Tasks — No Scheduling Logic

> **Created:** 2026-03-04
> **Completed:** 2026-03-04 (all 6 tasks, 12 PRs: #1239-#1250)
> **Purpose:** Unattended overnight automation tasks that avoid scheduling/solver/constraint code
> **Runner:** Claude Code (Opus 4.6, 11 parallel worktree agents across 3 waves)
> **Rule:** One branch per task. Each task is a standalone PR.

---

## Execution Protocol

```bash
# 1. Clean tree
git fetch origin main
git checkout origin/main
git checkout -b overnight/TASK_NAME-$(date +%Y%m%d)

# 2. Do the work (see task sections below)

# 3. Verify (task-specific checks)

# 4. Commit + push
git add -A
git commit -m "chore(backend): TASK_NAME — overnight mechanical fix"
git push -u origin HEAD

# 5. Open PR
gh pr create --title "chore: TASK_NAME" --body "Overnight mechanical task. See docs/planning/OVERNIGHT_MECHANICAL_TASKS.md"
```

**Hard Rules:**
- NEVER touch files in `backend/app/scheduling/` (engine, solver, constraints, preload, activity_solver, acgme_validator)
- NEVER touch `backend/app/core/security.py` or `backend/app/core/config.py`
- NEVER change runtime behavior — only types, annotations, logging, docs
- NEVER combine multiple tasks into one PR
- Tests must pass before commit: `cd backend && pytest -x --tb=short -q`
- Linters must pass: `ruff check . --fix && ruff format .`

---

## Task 1: Backend `str(e)` Hardening ✅

**Status:** COMPLETE — PR #1239 (`overnight/str-e-hardening`)
**Codex P2 fix:** Generic error messages for ValueError handlers (pushed)

**What:** Replace `str(e)` in error handling with safe patterns to prevent information leakage.
**Files:** 148 files, 466 instances across `backend/app/`
**Risk:** Low — error message changes only, no logic changes
**Success:** `grep -r 'str(e)' backend/app/ | wc -l` drops; tests pass

**Exclude these directories entirely (scheduling logic):**
- `backend/app/scheduling/`
- `backend/app/core/security.py`
- `backend/app/core/config.py`

**Safe targets (non-scheduling, 100+ instances):**

| Directory | Instances | Notes |
|-----------|-----------|-------|
| `app/monitoring/health_checks.py` | 12 | Health checks — safe |
| `app/services/rag_service.py` | 12 | RAG — safe |
| `app/contracts/testing.py` | 9 | Test contracts — safe |
| `app/api/routes/rag.py` | 9 | RAG routes — safe |
| `app/api/routes/conflicts.py` | 8 | Conflict UI routes — safe |
| `app/api/routes/queue.py` | 8 | Queue routes — safe |
| `app/api/routes/search.py` | 8 | Search routes — safe |
| `app/api/routes/experiments.py` | 8 | Experiment routes — safe |
| `app/notifications/templates/engine.py` | 8 | Notification templates — safe |
| `app/saga/orchestrator.py` | 7 | Saga (orphan framework) — safe |
| `app/workflow/engine.py` | 7 | Workflow (orphan framework) — safe |
| `app/rollback/manager.py` | 7 | Rollback manager — safe |
| `app/services/job_monitor/job_stats.py` | 7 | Job stats — safe |
| `app/services/import_staging_service.py` | 7 | Import staging — safe |
| `app/api/routes/ml.py` | 7 | ML routes — safe |
| `app/grpc/services.py` | 7 | gRPC (orphan framework) — safe |

**Fix patterns:**

```python
# Pattern A: API routes — don't leak internals
# BAD
except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
# GOOD
except Exception as e:
    logger.error("Operation failed", exc_info=True)
    raise HTTPException(status_code=500, detail="Internal server error")

# Pattern B: Service layer — use exc_info for debugging
# BAD
except Exception as e:
    logger.error(f"Failed: {str(e)}")
    return None
# GOOD
except Exception as e:
    logger.error("Failed", exc_info=True)
    return None

# Pattern C: Re-raise with chain
# BAD
except Exception as e:
    raise RuntimeError(f"Wrapped: {str(e)}")
# GOOD
except Exception as e:
    raise RuntimeError("Wrapped error") from e
```

**Verification:**
```bash
cd backend
# Count remaining str(e) (should decrease)
grep -r 'str(e)\|str(error)\|str(exception)' app/ --include='*.py' | grep -v scheduling/ | grep -v 'core/security' | grep -v 'core/config' | wc -l
# Tests pass
pytest -x --tb=short -q
# Ruff clean
ruff check app/ --fix && ruff format app/
```

**Estimated time:** 2-3 hours
**Estimated impact:** ~300 instances fixed (excluding scheduling code)

---

## Task 2: Frontend ESLint Ratchet ✅

**Status:** COMPLETE — PRs #1240, #1246-#1249 (8 batches across 5 PRs)
**Result:** 1,745 → 473 warnings (72.9% reduction)
**Codex P1 fixes:** WebSocket snake_case (PR #1246), fetch() snake_case (PR #1249)
**Codex P2 fix:** Numeric suffix in test assertions (PR #1240)

**What:** Fix ESLint warnings batch-by-batch (1,745 warnings, 0 errors currently).
**Automation prompt:** `.claude/automation-prompts/lint-ratchet-frontend.md` (full details)
**Risk:** Low — naming convention + unused vars + a11y
**Success:** Warning count drops; `npm run build` passes; `npm test` passes

**Final state:** 473 warnings, 0 errors

**Pick ONE batch per overnight run:**

| Batch | Directory | ~Warnings | Rule |
|-------|-----------|-----------|------|
| 1 | `src/__tests__/integration/` | 488 | naming-convention |
| 2 | `src/hooks/` | 160 | naming-convention, no-explicit-any |
| 3 | `src/__tests__/hooks/` | 142 | naming-convention |
| 4 | `src/components/schedule/` | 102 | naming-convention |
| 5 | `src/components/` (remaining) | 70 | mixed |
| 6 | `src/lib/` | 62 | naming-convention, no-explicit-any |
| 7 | `src/components/admin/` | 58 | naming-convention |
| 8 | `src/features/voxel-schedule/` | 45 | naming-convention |

**Critical context (from CLAUDE.md):**
- Enum VALUES stay snake_case (`'one_to_one'`, not `'oneToOne'`) — Gorgon's Gaze
- URL query params stay snake_case (`block_id`, not `blockId`) — Couatl Killer
- Object KEYS become camelCase (axios interceptor converts)

**Verification:**
```bash
cd frontend
npx eslint src/BATCH_DIR/ --format json 2>/dev/null | python3 -c "
import json, sys; data = json.load(sys.stdin)
w = sum(1 for f in data for m in f.get('messages',[]) if m.get('severity')==1)
print(f'Batch warnings remaining: {w}')
"
npm run build
npm test -- --passWithNoTests
```

---

## Task 3: Backend Mypy Ratchet ✅

**Status:** COMPLETE — PRs #1243-#1245 (10 batches across 3 PRs)
**Result:** 4,194 → 1,138 errors (72.9% reduction, 271 files remaining)
**Codex P1 fixes:** UUID equality (PR #1243), nullable returns (PR #1244), AST dict-unpack error (PR #1245)

**What:** Fix mypy type errors batch-by-batch (~4,194 errors in 492 files).
**Automation prompt:** `.claude/automation-prompts/mypy-ratchet-backend.md` (full details)
**Risk:** Low — type annotations only, no runtime changes
**Success:** Error count drops; tests pass

**Pick ONE batch per overnight run (low-risk first):**

| Batch | Directory | ~Errors |
|-------|-----------|---------|
| 1 | `app/services/_archived/` | 74 |
| 2 | `app/frms/` | 43 |
| 3 | `app/tenancy/` | 42 |
| 4 | `app/search/` | 49 |
| 5 | `app/cli/` | 56 |
| 6 | `app/exports/` | 59 |
| 7 | `app/workflow/` | 59 |
| 8 | `app/analytics/` | 63 |
| 9 | `app/ml/` | 51 |
| 10 | `app/testing/` | 126 |

**SKIP (scheduling logic):** `app/scheduling/` (492 errors — do NOT touch)

---

## Task 4: Print Statement → Logger Conversion ✅

**Status:** COMPLETE — PR #1241 (`overnight/print-to-logger`)

**What:** Replace `print()` calls with proper `logger` calls in backend.
**Files:** 29 instances across 10 files
**Risk:** Very low — only non-scheduling files have print statements
**Success:** `grep -r 'print(' backend/app/ --include='*.py' | wc -l` drops to ~0

**Safe targets:**

| File | Count | Notes |
|------|-------|-------|
| `scheduling/quantum/call_assignment_qubo.py` | 15 | Quantum QUBO — not production scheduling |
| `scheduling/quantum/qubo_template_selector.py` | 4 | Quantum QUBO — not production scheduling |
| `scheduling/zeno_dashboard.py` | 2 | Zeno dashboard — safe |
| `middleware/logging/__init__.py` | 2 | Logging module — likely intentional, review |
| `frms/scenario_analyzer.py` | 1 | FRMS — safe |
| `core/cache/redis_cache.py` | 1 | Cache — safe |
| `eventbus/bus.py` | 1 | EventBus — safe |
| `eventbus/__init__.py` | 1 | EventBus — safe |
| `analytics/arima_forecast.py` | 1 | Analytics — safe |
| `tasks/block_quality_report_tasks.py` | 1 | Report tasks — safe |

**Fix pattern:**
```python
# Add at top of file if not present:
import logging
logger = logging.getLogger(__name__)

# Replace:
print(f"Processing {item}")
# With:
logger.info("Processing %s", item)
```

**Verification:**
```bash
cd backend
grep -rn 'print(' app/ --include='*.py' | grep -v '# print' | grep -v 'pprint' | wc -l
pytest -x --tb=short -q
ruff check app/ --fix && ruff format app/
```

**Estimated time:** 30 minutes

---

## Task 5: Documentation Staleness Report (Read-Only) ✅

**Status:** COMPLETE — Report at `docs/reports/doc-staleness-20260304.md`

**What:** Generate a report of stale/broken documentation. NO changes — report only.
**Risk:** Zero — read-only analysis
**Success:** Report generated at `docs/reports/doc-staleness-$(date +%Y%m%d).md`

**Script:**
```bash
cd /Users/aaronmontgomery/Autonomous-Assignment-Program-Manager

echo "# Documentation Staleness Report — $(date +%Y-%m-%d)" > docs/reports/doc-staleness-$(date +%Y%m%d).md
echo "" >> docs/reports/doc-staleness-$(date +%Y%m%d).md

# Files not modified in 60+ days
echo "## Files Not Modified in 60+ Days" >> docs/reports/doc-staleness-$(date +%Y%m%d).md
find docs/ -name '*.md' -mtime +60 -type f | sort >> docs/reports/doc-staleness-$(date +%Y%m%d).md

# Files with TODO/FIXME/PENDING
echo "" >> docs/reports/doc-staleness-$(date +%Y%m%d).md
echo "## Files with TODO/FIXME/PENDING" >> docs/reports/doc-staleness-$(date +%Y%m%d).md
grep -rl 'TODO\|FIXME\|PENDING' docs/ --include='*.md' | sort >> docs/reports/doc-staleness-$(date +%Y%m%d).md

# Broken internal links (files referenced but missing)
echo "" >> docs/reports/doc-staleness-$(date +%Y%m%d).md
echo "## Potentially Broken Links" >> docs/reports/doc-staleness-$(date +%Y%m%d).md
grep -roh '\[.*\]([^http][^)]*\.md)' docs/ --include='*.md' | sort -u >> docs/reports/doc-staleness-$(date +%Y%m%d).md
```

**Estimated time:** 5 minutes

---

## Task 6: Frontend `console.log` Sweep ✅

**Status:** COMPLETE — PR #1242 (`overnight/console-log-sweep`)

**What:** Remove or guard debug `console.log` statements in production frontend code.
**Risk:** Very low — removing debug output
**Success:** `grep -r 'console.log' src/ --include='*.ts' --include='*.tsx' | wc -l` drops

**Exclude:** Test files (`__tests__/`, `*.test.*`, `*.spec.*`)

**Fix pattern:**
```typescript
// Remove entirely if it's debug noise:
console.log('debug:', data);  // DELETE

// Keep if it's error logging but wrap:
console.error('Failed to fetch:', error);  // KEEP (errors are useful)
```

**Verification:**
```bash
cd frontend
npm run build
npm test -- --passWithNoTests
```

---

## Execution Results

All 6 tasks completed in a single overnight session using 11 parallel worktree agents across 3 waves.

| Wave | Agents | PRs | Duration |
|------|--------|-----|----------|
| 1 | 5 (str-e, print→logger, console.log, ESLint batch 1, mypy batch 1-2) | #1239-#1243 | ~45 min |
| 2 | 3 (mypy batch 3-6, mypy batch 7-10, ESLint batch 2-4) | #1244-#1247 | ~60 min |
| 3 | 2 (ESLint batch 5-6, ESLint batch 7-8) | #1248-#1249 | ~30 min |
| Wheat | 1 (codex chaff harvest) | #1250 | manual |

**Codex review:** 6 P1 + 4 P2 issues found across 7 PRs. All concurred and fixed. 4 PRs had no feedback.

---

## What NOT To Touch (Hard Boundaries)

| Path | Reason |
|------|--------|
| `backend/app/scheduling/engine.py` | Core scheduling logic |
| `backend/app/scheduling/activity_solver.py` | Activity assignment logic |
| `backend/app/scheduling/acgme_validator.py` | ACGME compliance |
| `backend/app/scheduling/constraints/` | Constraint definitions |
| `backend/app/services/sync_preload_service.py` | Preload sync logic |
| `backend/app/scheduling/annual/` | ARO solver |
| `backend/app/core/security.py` | Auth/hashing |
| `backend/app/core/config.py` | Configuration |
| `backend/app/db/base.py` | DB config |
| `backend/app/models/*.py` | Schema changes need migrations |
| `backend/alembic/versions/*.py` | Never edit existing migrations |
