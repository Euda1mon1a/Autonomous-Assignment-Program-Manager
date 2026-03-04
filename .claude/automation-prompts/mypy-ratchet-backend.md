# Backend Mypy Ratchet — Overnight Automation

> For: Mac Mini overnight runs
> Goal: Reduce mypy errors from ~4,160 to 0 in directory-scoped batches
> Rule: ONE batch per run. Do NOT combine batches.

## Preflight

```bash
git fetch origin && git checkout origin/main && git checkout -b mini/claude/mypy-ratchet-$(date +%Y%m%d)-BATCH_NAME
cd backend
```

## Batch Order (largest → smallest, grouped by risk)

### Low-Risk Batches (start here)

| Batch | Directory | ~Errors | Top Error Types |
|-------|-----------|---------|-----------------|
| ~~1~~ | ~~`app/services/_archived/`~~ | ~~74~~ | **DELETED** — dead code removed Mar 2026 |
| 2 | `app/testing/` | 126 | arg-type, assignment |
| 3 | `app/analytics/` | 63 | arg-type, str |
| 4 | `app/exports/` | 59 | arg-type, assignment |
| 5 | `app/cli/` | 56 | arg-type, assignment |
| 6 | `app/search/` | 49 | arg-type, str |
| 7 | `app/frms/` | 43 | arg-type, assignment |
| 8 | `app/tenancy/` | 42 | arg-type, union-attr |
| 9 | `app/workflow/` | 59 | arg-type, assignment |
| 10 | `app/ml/` | 51 | arg-type, assignment |

### Medium-Risk Batches

| Batch | Directory | ~Errors | Top Error Types |
|-------|-----------|---------|-----------------|
| 11 | `app/validators/` | 89 | arg-type, assignment |
| 12 | `app/schemas/` | 84 | arg-type, assignment |
| 13 | `app/repositories/` | 48 | arg-type, return-value |
| 14 | `app/models/` | 98 | assignment, attr-defined |
| 15 | `app/migrations/` | 54 | misc, assignment |
| 16 | `app/resilience/` | 227 | arg-type, assignment |

### High-Risk Batches (do last, most critical code)

| Batch | Directory | ~Errors | Top Error Types |
|-------|-----------|---------|-----------------|
| 17 | `app/scheduling/bio_inspired/` | 98 | arg-type, assignment |
| 18 | `app/scheduling/` (core) | 492 | arg-type, assignment, return-value |
| 19 | `app/api/routes/` | 637 | arg-type, assignment |
| 20 | `app/services/` (non-archived) | 1137 | arg-type, assignment, str |

## Rules

### Common Fix Patterns

**arg-type (1,385 errors):** Function called with wrong type.
```python
# Before (error: arg-type)
def get_person(person_id: int) -> Person: ...
get_person(some_uuid)  # UUID != int

# Fix: correct the call site OR widen the parameter type
get_person(int(some_uuid))  # if conversion is safe
# OR
def get_person(person_id: int | UUID) -> Person: ...  # if both types valid
```

**assignment (1,041 errors):** Variable assigned incompatible type.
```python
# Before
result: str = some_func()  # some_func returns str | None

# Fix: widen the annotation
result: str | None = some_func()
# OR narrow with assertion
result: str = some_func()  # type: ignore[assignment]  -- LAST RESORT
```

**attr-defined (393 errors):** Accessing attribute that type doesn't have.
```python
# Usually SQLAlchemy relationship access — add type stubs or TYPE_CHECKING imports
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.block import Block
```

### NEVER Do

1. **NEVER add blanket `# type: ignore`** without an error code — always use `# type: ignore[specific-code]`
2. **NEVER change runtime behavior** to fix a type error — if the code works, fix the annotation
3. **NEVER modify ACGME compliance code** (`app/scheduling/acgme_validator.py`) — skip and note
4. **NEVER modify security code** (`app/core/security.py`, `app/core/config.py`) — skip and note
5. **NEVER remove existing `# type: ignore` comments** — they may guard against real issues

### Acceptable Patterns

- `from __future__ import annotations` for forward refs
- `TYPE_CHECKING` imports for circular dependencies
- `cast()` when you can prove type safety but mypy can't infer it
- `# type: ignore[error-code]` with comment explaining why, as LAST RESORT

## Verification (MUST pass before commit)

```bash
# Count errors in your batch directory
.venv/bin/python3 -m mypy app/YOUR_BATCH_DIR --ignore-missing-imports --no-error-summary 2>&1 | wc -l

# Full mypy must not INCREASE error count
TOTAL=$(.venv/bin/python3 -m mypy app --ignore-missing-imports --no-error-summary 2>&1 | wc -l)
echo "Total mypy errors: $TOTAL"
# Must be <= 4160

# Tests must still pass for the directory
DEBUG=true .venv/bin/python3 -m pytest tests/ -x --tb=short -q

# Ruff must pass
.venv/bin/ruff check app/YOUR_BATCH_DIR --fix
.venv/bin/ruff format app/YOUR_BATCH_DIR
```

## Commit Format

```
fix(backend): reduce mypy errors in BATCH_DIR

Batch N of mypy ratchet: fix arg-type/assignment/etc
in app/BATCH_DIR/. Errors: BEFORE → AFTER.
```
