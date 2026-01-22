# Session 119: Activity Assignment Complete

> **Date:** 2026-01-20
> **Status:** COMPLETE
> **Purpose:** Ensure ALL half_day_assignments have activity_id populated

---

## Problem Solved

The activities table was missing 29 rotation-specific activities. The preload service couldn't find activities for FMIT, NF, PedW, etc., resulting in 472 preload slots with NULL activity_id.

**Before:**
- solver: 420 with activity_id
- preload: 230 with activity_id, **472 with NULL**

**After:**
- solver: 420 with activity_id
- preload: **722 with activity_id, 0 NULL**

---

## Changes Made

### 1. Migration: `20260120_add_rot_activities.py`

Added 29 new activities:

**Inpatient Rotations:** FMIT, NF, PedW, PedNF, KAP, IM, LDNF, TDY

**Schedule Codes:** W, HOL, DEP, C-N, CV, FLX, ADM

**Education/Protected:** SIM, PI, MM, CLC, HLC, HAFP, USAFP, BLS

**Electives:** NEURO, US, GYN, SURG, PR, VAS

### 2. SyncPreloadService Fixes

**File:** `backend/app/services/sync_preload_service.py`

1. Fixed enum/string handling for rotation_type:
   ```python
   activity_code = rotation_type.value if hasattr(rotation_type, 'value') else (rotation_type or "FMIT")
   ```

2. Added rotation-to-activity mapping:
   ```python
   rotation_to_activity = {
       "FMC": "fm_clinic",   # FM Clinic -> C
       "HILO": "TDY",        # Hilo rotation -> TDY
   }
   ```

3. Fixed `_get_rotation_codes()` to handle string rotation types

4. Fixed `ResidentCallPreload.date` → `ResidentCallPreload.call_date`

5. Removed unused fallback logic

### 3. Data Migration (Direct SQL)

Updated existing NULL preload records:

| Rotation | Activity | Records Updated |
|----------|----------|-----------------|
| FMIT | FMIT | 168 |
| IM | IM | 56 |
| PedW | PedW | 54 |
| HILO | TDY | 48 |
| NF | NF | 42 |
| KAP | KAP | 36 |
| PedNF | PedNF | 28 |
| LDNF | LDNF | 16 |
| LDNF weekend | W | 16 |
| FMC | fm_clinic | 8 |

---

## Final Activity Distribution (Block 10)

| Activity | Source | Count |
|----------|--------|-------|
| C | solver | 383 |
| FMIT | preload | 168 |
| OFF | preload | 102 |
| LV | preload | 56 |
| IM | preload | 56 |
| PedW | preload | 54 |
| TDY | preload | 48 |
| NF | preload | 42 |
| KAP | preload | 36 |
| LEC | solver | 30 |
| CALL | preload | 28 |
| PedNF | preload | 28 |
| PCAT/DO | preload | 38 |
| LDNF | preload | 16 |
| W | preload | 16 |
| ADV | solver | 7 |

**Total: 1142 assignments, 0 NULL activity_id**

---

## Architecture (Final)

```
BlockAssignment (manual/imported)
       ↓
Expansion Service (creates 56 slots/person, activity_id=NULL)
       ↓
SyncPreloadService (locks FMIT, NF, KAP, call, absences with activity_id)
       ↓
CPSATActivitySolver (assigns C, LEC, ADV to remaining slots)
       ↓
half_day_assignments (ALL slots have activity_id)
       ↓
Frontend (displays via /api/half-day-assignments)
```

---

## Key Learnings

1. **Enum vs String:** SQLAlchemy sometimes returns strings instead of enums from the database. Always check with `hasattr(x, 'value')` before calling `.value`.

2. **Activity naming:** Rotation types (FMIT, NF) don't always match activity codes (fm_clinic vs FMC). Maintain explicit mapping.

3. **Day-specific patterns:** KAP, LDNF, NF have different AM/PM codes depending on day of week. The `_get_rotation_codes()` function handles this.

4. **Preload service doesn't update:** `_create_preload` only creates new records, doesn't update existing NULL records. Direct SQL was needed for data migration.

---

## Files Modified

| File | Change |
|------|--------|
| `backend/alembic/versions/20260120_add_rot_activities.py` | NEW - adds 29 activities |
| `backend/app/services/sync_preload_service.py` | Fixed enum handling, rotation mapping, column name |

---

## Verification SQL

```sql
-- Verify no NULL activity_id remains
SELECT source, activity_id IS NULL as is_null, COUNT(*)
FROM half_day_assignments
WHERE date BETWEEN '2026-03-12' AND '2026-04-08'
GROUP BY source, activity_id IS NULL;

-- Expected: All rows have is_null = false
```

---

## GUI Verification (Chrome Extension)

### Test Results

| Criteria | Status | Notes |
|----------|--------|-------|
| Schedule page loads | ✅ PASS | Block 10 loaded correctly |
| FMIT residents | ✅ PASS | PGY-2/PGY-3 on FMIT show FMIT all day |
| NF resident | ✅ PASS | PGY-3 on NF shows off/NF pattern |
| KAP resident | ✅ PASS | PGY-1 on KAP shows correct day variations |
| IM resident | ✅ PASS | PGY-1 on IM shows IM all day |
| PedW/PedNF | ✅ PASS | PGY-1s show mid-block transitions |
| LDNF resident | ✅ PASS | PGY-2 on LDNF shows off/LDNF + Fri clinic |
| TDY (Hilo) | ✅ PASS | PGY-3 on Hilo shows TDY |
| Wednesday LEC | ✅ PASS | All residents show `lec` on Wed PM |
| Last Wed ADV | ✅ PASS | Shows `lec/advising` pattern |
| No blank cells | ✅ PASS | All cells populated |

### Bug Fixed: Display Abbreviation Now in API ✅

**Issue (Resolved):** GUI was showing `fm_clinic` instead of `C`, `lec` instead of `LEC`

**Fix Applied (Session 119 continued):**

1. Added `display_abbreviation` to `HalfDayAssignmentRead` schema
2. Updated API route to include `display_abbreviation` in response
3. Updated frontend TypeScript interface
4. Updated `ScheduleGrid.tsx` to prefer `displayAbbreviation` over `activityCode`

**Files Modified:**
- `backend/app/schemas/half_day_assignment.py` - Added field
- `backend/app/api/routes/half_day_assignments.py` - Include in response
- `frontend/src/hooks/useHalfDayAssignments.ts` - TypeScript interface
- `frontend/src/components/schedule/ScheduleGrid.tsx` - Display logic

**Verification:** GUI now shows `C`, `LEC`, `ADV` correctly instead of `fm_clinic`, `lec`, `advising`

---

## Architectural Discussion: UUIDs

### Current State

| Entity | ID Type | Notes |
|--------|---------|-------|
| People | UUID ✓ | |
| Activities | UUID ✓ | |
| HalfDayAssignments | UUID ✓ | |
| BlockAssignments | UUID ✓ | |
| RotationTemplates | UUID ✓ | |
| CallAssignments | UUID ✓ | |
| **Blocks** | Composite | `(block_number, academic_year)` - no table |
| **Academic Years** | Integer | Natural key (2025, 2026) |

### UUIDs and CP-SAT Compatibility

UUIDs work fine with CP-SAT - just need a mapping layer:

```python
# Map UUIDs to integers for CP-SAT
activity_idx = {a.id: i for i, a in enumerate(activities)}

# CP-SAT uses integer indices
a[slot_idx, activity_idx] = model.NewBoolVar(...)

# After solving, map back to UUIDs
slot.activity_id = activity.id  # UUID
```

**Cost:** O(n) to build dict, O(1) lookups - negligible for ~1000 assignments.

### Recommendation: Create Blocks Table

For consistency, create a `blocks` table with UUIDs while keeping human-readable attributes:

```python
class Block(Base):
    id: UUID                    # Primary key (UUID)
    block_number: int           # 0-13 (human readable)
    academic_year: int          # 2025 (human readable)
    start_date: date
    end_date: date
    # Unique constraint on (block_number, academic_year)
```

**Benefits:**
- Consistent UUID pattern everywhere
- Simpler FKs: `block_id UUID` instead of composite
- Human-readable attributes preserved for queries/display
- Future-proof for non-standard blocks

---

## Human TODOs (Deferred)

1. Fork greedy, pulp, hybrid solvers for activity assignment
2. Add rotation_activity_requirements constraints to activity solver
3. Add comprehensive tests for activity solver
4. ~~**Add `display_abbreviation` to HalfDayAssignmentRead schema**~~ ✅ DONE
5. **Consider creating `blocks` table with UUIDs**
