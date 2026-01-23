# Session 094: Schedule Generation Validation & Beholder Bane

**Date:** 2026-01-13
**Branch:** `feat/exotic-explorations`
**Status:** Complete - all fixes applied and tested

## Summary

Fixed schedule generation bugs and created the Beholder Bane lint tool to prevent SQLAlchemy filter anti-magic patterns.

## Bugs Fixed

### 1. Assignment Delete/Insert Ordering (`engine.py:1913-1915`)
**Problem:** SQLAlchemy could execute INSERTs before DELETEs in same transaction, causing `unique_person_per_block` constraint violations.
**Fix:** Added `self.db.flush()` after `_delete_existing_assignments()`.

### 2. Faculty Assignment Missing Preserved Assignments (`engine.py:1602-1641`)
**Problem:** `_assign_faculty()` only considered `self.assignments` (new), not preserved seed data in DB. Result: 0 faculty supervision for 476 preserved resident assignments.
**Fix:** Include `preserved_assignments` when building `assignments_by_block`, `all_resident_ids`, and `all_template_ids`.

### 3. Validation Flush Timing (`engine.py:396-398`)
**Problem:** `ACGMEValidator.validate_all()` queries DB, but new assignments weren't flushed yet. Validator saw stale data.
**Fix:** Added `self.db.flush()` before calling `validate_all()`.

### 4. Coverage Rate SQLAlchemy Filter (`validator.py:152`)
**Problem:** `not Block.is_weekend` is invalid SQLAlchemy - Python evaluates `not <Column>` as `False`, so filter returns 0 blocks.
**Fix:** Changed to `Block.is_weekend == False  # noqa: E712`.

### 5. Notification Service Filter (`notifications/service.py:504`)
**Problem:** Same pattern - `not Notification.is_read` in filter.
**Fix:** Changed to `Notification.is_read == False  # noqa: E712`.

## Final Validation Results

```
Block 10 (March 12 - April 8, 2026):
- Coverage Rate: 100%
- ACGME Violations: 0
- Total Assignments: 903 (508 primary + 395 supervising)
- Only Issue: NF_PC_COVERAGE (Post-Call template not configured - data setup)
```

## Beholder Bane - New Lint Tool

**Location:** `scripts/beholder-bane.sh`
**Pre-commit:** Phase 24 in `.pre-commit-config.yaml`

Named after D&D Beholder's anti-magic cone. Detects `not Column` in SQLAlchemy `.filter()` calls which silently break queries.

**Usage:**
```bash
./scripts/beholder-bane.sh              # Scan backend/
./scripts/beholder-bane.sh backend/app/ # Specific path
pre-commit run beholder-bane --all-files
```

**Pattern Detected:**
```python
# CURSED (returns nothing):
.filter(not Block.is_weekend)
.filter(not Notification.is_read)

# BLESSED:
.filter(Block.is_weekend == False)
.filter(~Block.is_weekend)
```

## Files Modified

| File | Changes |
|------|---------|
| `backend/app/scheduling/engine.py` | 3 fixes: flush after delete, include preserved in faculty assignment, flush before validation |
| `backend/app/scheduling/validator.py` | Coverage rate filter fix |
| `backend/app/notifications/service.py` | Filter bug fix |
| `scripts/beholder-bane.sh` | NEW - SQLAlchemy anti-magic detector |
| `.pre-commit-config.yaml` | Added Phase 24: Beholder Bane |

## Key Code Changes

### engine.py - Flush after delete (line 1913-1915)
```python
# CRITICAL: Flush deletes before any inserts to avoid constraint violations
# SQLAlchemy may execute INSERTs before DELETEs without explicit flush
self.db.flush()
```

### engine.py - Include preserved in faculty assignment (lines 1602-1641)
```python
# Group assignments by block - include BOTH new (self.assignments) AND preserved
# Preserved assignments in DB need faculty supervision too
assignments_by_block = {}

# First add new assignments from this run
for assignment in self.assignments:
    ...

# Then add preserved assignments (already in DB, not deleted)
if preserved_assignments:
    for assignment in preserved_assignments:
        ...
```

### engine.py - Flush before validation (lines 396-398)
```python
# Step 8.5: Flush to make assignments visible to validator
# Validator queries DB, so flush is needed before validation
self.db.flush()
```

### validator.py - Coverage rate filter (line 152)
```python
Block.is_weekend == False,  # noqa: E712 - SQLAlchemy requires == for filter
```

## Remaining Known Issues

1. **NF_PC_COVERAGE** - Post-Call rotation template not configured (data setup issue)
2. **`__rsub__` solver error** - Data-dependent, may occur in specific constraint scenarios
3. **Visualization 500 errors** - Deferred from Session 093

## Container Rebuild Command

```bash
docker-compose up -d --build backend
```

## Test Commands

```bash
# Test schedule generation
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123" | jq -r '.access_token')

curl -s -X POST "http://localhost:8000/api/v1/schedule/generate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"start_date":"2026-03-12","end_date":"2026-04-08","algorithm":"cp_sat","timeout_seconds":120}'

# Test Beholder Bane
./scripts/beholder-bane.sh
pre-commit run beholder-bane --all-files
```
