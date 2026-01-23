# Session 125: PCAT/DO Validation Hook

> **Date:** 2026-01-21
> **Branch:** `feature/activity-assignment-session-119`
> **Status:** Complete

---

## Summary

Added automatic PCAT/DO integrity validation that runs on every schedule generation. This catches silent sync failures without requiring CI.

---

## Problem

Codex identified that pipeline order tests were "documentation-only" and didn't exercise the actual engine. Additionally, there was no automated way to verify PCAT/DO was created correctly after call assignments.

---

## Solution

### 1. Enhanced Pipeline Tests (Commits `7fd9bc1e`, `4776cdfd`)

Added three test categories:
- **Unit tests**: `skip_faculty_call` parameter
- **Enforcement tests (TRIPWIRE)**: Mock/patch tests that track call order - catches code reordering
- **Integration tests (DATABASE)**: Verify actual PCAT/DO creation with live DB

Key features:
- `REQUIRED_STEPS` list with hard-fail assertions
- Tracks `_run_solver` for call generation ordering
- No exception swallowing

### 2. PCAT/DO Validation Hook (Commits `f9556dfa`, `8c172409`, `41373b81`)

New `_validate_pcat_do_integrity()` method in `engine.py`:

```python
# Step 6.6.1 - runs after PCAT/DO sync, before activity solver
if validate_pcat_do:
    pcat_do_issues = self._validate_pcat_do_integrity(call_assignments)
    if pcat_do_issues:
        # ROLLBACK all changes, update run status to failed
        ...
```

Features:
- Runs automatically on every `generate()` call
- Checks each call → PCAT (next day AM) + DO (next day PM)
- Respects: FMIT skip, end-of-block skip, preload precedence (AM and PM)
- **Rollback on failure** - no partial state
- Disable with `validate_pcat_do=False` once stable

### 3. Codex Findings Addressed

| Finding | Severity | Fix |
|---------|----------|-----|
| Tests don't exercise engine | Medium | Added enforcement + integration tests |
| Exception swallowing | Medium | Removed try/except, hard-fail assertions |
| `_run_solver` not tracked | Medium | Added to call_order tracking |
| Unused imports | Low | Removed PropertyMock, uuid4 |
| Partial commit on failure | High | Changed to rollback() |
| AM preload precedence | Medium | Added same check as PM |
| Wrong ScheduleRun fields | High | Use `_update_run_status()` |
| PK conflict on re-insert | High | Re-fetch existing run via `db.get()` |

---

## Commits

| Commit | Description |
|--------|-------------|
| `7fd9bc1e` | Initial enforcement + integration tests |
| `4776cdfd` | Hard-fail assertions, track `_run_solver`, remove unused imports |
| `f9556dfa` | Add `_validate_pcat_do_integrity` hook |
| `8c172409` | Rollback on failure + AM preload precedence |
| `41373b81` | Fix ScheduleRun fields and PK conflict |

---

## Verification

Block 10 generation with validation enabled:
```
Created 20 overnight call assignments
PCAT/DO integrity check passed (20 calls verified)
Status: success
```

---

## Usage

```python
# Validation ON (default)
engine.generate(block_number=10, academic_year=2025)

# Validation OFF (once pipeline is stable)
engine.generate(block_number=10, academic_year=2025, validate_pcat_do=False)
```

---

## Files Modified

- `backend/app/scheduling/engine.py` - Added validation method and hook
- `backend/tests/scheduling/test_pipeline_order.py` - Enhanced tests
- `docs/scratchpad/block10-pre-regeneration-snapshot.md` - Pre-generation state

---

## Next Steps

1. Monitor validation in production for a few blocks
2. Once confident, can disable with `validate_pcat_do=False`
3. Consider adding to CI if Postgres service is configured
