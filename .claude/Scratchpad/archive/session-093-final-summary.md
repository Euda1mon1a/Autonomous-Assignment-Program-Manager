# Session 093: Solver Visualization Fix - Final Summary

**Date:** 2026-01-13
**Branch:** `feat/exotic-explorations`
**Status:** Multiple fixes applied, ready for testing

## Problem Summary

Solver 3D visualization not rendering due to 500 errors on `/schedule/generate` and `/schedule/queue`.

## Root Cause Investigation

### Myth Busted
- **Original theory:** Next.js rewrites strip Authorization headers
- **Reality:** Next.js DOES forward Authorization headers correctly (verified via curl)
- **Red herring:** `user=anonymous` in PHI middleware is benign (runs before auth sets user)

### Actual Root Causes Found & Fixed

1. **Call Assignment Constraint Violation**
2. **Migration Bugs**
3. **Pydantic Schema Validation Error**

## Fixes Applied

### Fix 1: Call Assignment (`backend/app/scheduling/engine.py`)

**Problem:** `UniqueViolation: duplicate key violates unique constraint "unique_call_per_day"`
- No cleanup of existing CallAssignments before regeneration
- Solver uses `call_type='overnight'` but DB constraint only allows `('sunday', 'weekday', 'holiday', 'backup')`

**Solution:**
```python
# In _create_call_assignments_from_result():
# 1. Delete existing call assignments for date range
deleted_count = (
    self.db.query(CallAssignment)
    .filter(CallAssignment.date >= self.start_date, CallAssignment.date <= self.end_date)
    .delete(synchronize_session=False)
)

# 2. Map 'overnight' to correct type
is_sunday = block.date.weekday() == 6
if call_type == "overnight":
    mapped_call_type = "sunday" if is_sunday else "weekday"
```

### Fix 2: Migration - Abbreviation Length (`backend/alembic/versions/20260111_hybrid_model.py`)

**Problem:** `StringDataRightTruncation: value too long for type character varying(10)`
- Migration tried to set 12-char abbreviations in VARCHAR(10) column

**Solution:** Use short `abbreviation` + longer `display_abbreviation`:
```sql
UPDATE rotation_templates SET abbreviation = 'NF-FMIT', display_abbreviation = 'NF-FMIT-PGY1'
WHERE abbreviation = 'NFI';
```

### Fix 3: Migration - Enum Creation (`backend/alembic/versions/20260111_day_type_cols.py`)

**Problem:** `UndefinedObject: type "daytype" does not exist`
- Enum types not created before use in add_column

**Solution:** Explicitly create enums first:
```python
day_type_enum = sa.Enum("NORMAL", "FEDERAL_HOLIDAY", ..., name="daytype")
day_type_enum.create(op.get_bind(), checkfirst=True)  # ADD THIS
```

### Fix 4: Schema Validation (`backend/app/schemas/schedule.py`)

**Problem:** `2 validation errors for NFPCAuditViolation: nf_date - Input should be a valid date`

**Solution:** Make fields optional:
```python
class NFPCAuditViolation(BaseModel):
    nf_date: date | None = None  # Was: date (required)
    pc_required_date: date | None = None  # Was: date (required)
    missing_am_pc: bool = False  # Was: bool (required)
    missing_pm_pc: bool = False  # Was: bool (required)
```

## Files Modified

| File | Change |
|------|--------|
| `backend/app/scheduling/engine.py` | Call assignment cleanup + type mapping |
| `backend/alembic/versions/20260111_hybrid_model.py` | Use short abbr + display_abbreviation |
| `backend/alembic/versions/20260111_day_type_cols.py` | Create enum before use |
| `backend/app/schemas/schedule.py` | NFPCAuditViolation fields optional |

## Auth Flow (Working)

After login:
- `[Auth] storeTokens called: {hasRefresh: true, hasAccess: true}`
- `[API] Request interceptor: {hasToken: true}`
- `[API] Added Authorization header`

Session persistence via sessionStorage also working.

## Testing Status

- ✅ Backend starts successfully
- ✅ Migrations complete
- ✅ Auth headers sent correctly
- ✅ Solver runs (~66 seconds before schema fix)
- 🔄 Awaiting user test after schema fix

## Remaining Known Issues

1. **Redis auth warning** - Caching disabled, non-blocking
2. **WebSocket closes quickly** - May be React StrictMode double-mount
3. **`__rsub__` solver error** - Data-dependent, may occur in specific scenarios

## Container Rebuild Command

```bash
docker-compose up -d --build backend
```

## Documentation Locations (User Question)

For AI agents:
- `.claude/dontreadme/INDEX.md` - Master index
- `.claude/skills/` - Skill definitions
- RAG: `mcp__residency-scheduler__rag_search("topic")`

For humans + AI:
- `docs/development/BEST_PRACTICES_AND_GOTCHAS.md`
- `CLAUDE.md` - Project guidelines
