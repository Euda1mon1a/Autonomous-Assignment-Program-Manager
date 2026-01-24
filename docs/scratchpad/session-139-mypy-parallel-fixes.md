# Session 139: Parallel mypy Fix Deployment

**Date:** 2026-01-24
**Branch:** `feature/rotation-faculty-templates`
**Commit:** `5bd187c8`
**Status:** PARTIAL - 235/6678 errors fixed (3.5%)

---

## Approach

Deployed 10 parallel coordinators (flat structure) across domain partitions:

| COORD | Domain | Files | Errors Fixed |
|-------|--------|-------|--------------|
| 1 | services/ | 98 | ~10 |
| 2 | api/ | 76 | 16 |
| 3 | resilience/ | 74 | 30-40 |
| 4 | scheduling/ | 71 | 10 |
| 5 | models/ | 52 | 0 (reversion issue) |
| 6 | notifications+db | 63 | 29 |
| 7 | middleware+analytics | 48 | ? |
| 8 | core+schemas+validators | 48 | 20-25 |
| 9 | auth+tasks+cli+repos | 42 | 15-20 |
| 10 | remaining | ~76 | 39 |

**Total:** 50 files modified, 235 errors fixed

---

## Why It Was Slow

### Problem: Incremental Fix Loop
Each agent was doing:
```
1. Run mypy (slow - checks all 1243 files)
2. Read error output
3. Fix ONE error
4. Re-run mypy to verify
5. Repeat
```

This pattern is O(n²) - each verification runs full mypy.

### Better Approach (Next Session)
Batch fix by error pattern:
```
1. Run mypy ONCE, capture all errors
2. Group by error type
3. Fix ALL instances of each pattern
4. Run mypy ONCE to verify
```

---

## Error Pattern Analysis

### Top Error Types (from agent reports)

| Pattern | Count Est. | Fix |
|---------|------------|-----|
| `no-untyped-def` | ~2000 | Add `-> None` or `-> Type` |
| `var-annotated` | ~1500 | Add `: Type` to variables |
| `assignment` (Column) | ~1000 | `cast(Type, model.attr)` |
| `arg-type` | ~500 | Type narrowing with cast |
| `union-attr` | ~300 | None checks before `.method()` |
| `attr-defined` | ~200 | Import fixes, model corrections |

### SQLAlchemy Column Pattern (Critical)
Most errors stem from SQLAlchemy ORM:
```python
# mypy sees: Column[str]
# code expects: str

# Fix pattern:
from typing import cast
email = cast(str, person.email)
```

This affects ~40% of all errors.

---

## Agent-Specific Findings

### COORD-5 (models/) - File Reversion
Reported that edits were being reverted by:
- Pre-commit hooks (ruff format)
- File watchers
- Docker volume sync

**Mitigation:** Run `SKIP=ruff-format` or disable watchers during bulk edits.

### COORD-6 (notifications+db) - Success Story
Fixed ALL 29 errors in assigned files. Used patterns:
- `-> Generator[Type, None, None]` for context managers
- `Token[Type] | None` for context vars
- `getattr(obj, "attr", default)` for dynamic access

### COORD-10 (remaining) - mypy Internal Errors
Encountered mypy AssertionError in some directories:
- `app/controllers/` - Cannot process
- Likely circular imports or cache corruption

**Fix:** `rm -rf .mypy_cache` and retry

---

## Recommendations for Next Session

### Option A: Bulk Pattern Fix (Recommended)
```bash
# 1. Get all -> None candidates
grep -r "def.*:$" backend/app/ --include="*.py" | grep -v "-> "

# 2. Sed/awk to add -> None
find backend/app -name "*.py" -exec sed -i '' \
  's/def \(__init__\|__repr__\|__str__\)(self):/def \1(self) -> None:/g' {} \;

# 3. Verify with single mypy run
```

### Option B: Error-Type Specialists
Spawn specialists by error type, not directory:
- SPEC-1: All `no-untyped-def` errors
- SPEC-2: All `var-annotated` errors
- SPEC-3: All SQLAlchemy `cast()` fixes

### Option C: Hybrid
1. Bulk sed for trivial patterns (`-> None`, `-> str`)
2. Specialists for complex patterns (Column casts, generics)

---

## Files Modified (50 total)

```
backend/app/analytics/metrics.py
backend/app/api/dependencies/role_filter.py
backend/app/api/deps.py
backend/app/auth/access_matrix.py
backend/app/auth/permissions/decorators.py
backend/app/auth/sso/config.py
backend/app/db/explain_analyzer.py
backend/app/db/health_check.py
backend/app/db/materialized_views.py
backend/app/db/query_optimizer.py
backend/app/db/transaction.py
backend/app/multi_objective/core.py
backend/app/multi_objective/decision_support.py
backend/app/multi_objective/diversity.py
backend/app/multi_objective/indicators.py
backend/app/multi_objective/moead.py
backend/app/multi_objective/preferences.py
backend/app/resilience/blast_radius.py
backend/app/resilience/burnout_fire_index.py
backend/app/resilience/circadian_model.py
backend/app/resilience/defense_in_depth.py
backend/app/resilience/le_chatelier.py
backend/app/services/faculty_assignment_expansion_service.py
backend/app/tasks/periodic_tasks.py
backend/app/validators/sanitizers.py
backend/app/validators/swap_validators.py
... (24 more)
```

---

## Progress Tracking

| Session | Start | End | Fixed | % |
|---------|-------|-----|-------|---|
| 137 R1 | 7426 | 6880 | 546 | 7.3% |
| 137 R2 | 6880 | 6440 | 440 | 6.4% |
| 139 | 6678 | 6443 | 235 | 3.5% |
| **Total** | 7426 | 6443 | **983** | **13.2%** |

**Remaining:** 6,443 errors across 742 files

---

*Session 139 complete. Bulk pattern approach recommended for next session.*
