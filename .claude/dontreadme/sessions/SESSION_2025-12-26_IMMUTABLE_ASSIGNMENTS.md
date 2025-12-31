# Session: Immutable Assignment Preservation

**Date:** 2025-12-25/26
**Branch:** `claude/block0-engine-fix-commands`
**Type:** Bug Fix + Feature Enhancement

---

## Problem Statement

When running the scheduling solver on Block 10 after pre-seeding inpatient rotations, the solver failed with:

```
duplicate key value violates unique constraint "unique_person_per_block"
```

The solver was attempting to create outpatient assignments for residents who already had inpatient rotations (Night Float, FMIT, ICU, L&D), causing unique constraint violations in the database.

---

## Root Cause Analysis

The scheduling engine (`backend/app/scheduling/engine.py`) did not:
1. Pass existing assignments to the solver as constraints
2. Filter solver output against immutable assignments
3. Distinguish between solver-managed rotations and pre-seeded immutable ones

Additionally, `PostFMITRecoveryConstraint` existed in `backend/app/scheduling/constraints/fmit.py` but was **never registered** in the default constraint manager.

---

## Solution: Preserved Assignment Architecture

### Activity Type Classification

Rotations are now classified into **7 activity types**:

| Activity Type | Solver Manages? | Examples |
|---------------|-----------------|----------|
| `outpatient` | **Yes** | Clinic AM/PM, Sports Med, Colposcopy |
| `procedures` | **Yes** | Botox, Vasectomy |
| `inpatient` | No - Preserved | FMIT AM/PM, Night Float, ICU, L&D, NICU |
| `off` | No - Preserved | Hilo, Kapiolani, Okinawa |
| `education` | No - Preserved | FMO (Orientation), GME, Lectures |
| `absence` | No - Preserved | Leave AM/PM, Weekend AM/PM |
| `recovery` | No - Preserved | Post-Call Recovery |

### Engine Modifications

**6 new loader methods** in `engine.py`:
- `_load_fmit_assignments()` - Faculty FMIT teaching weeks
- `_load_resident_inpatient_assignments()` - All resident inpatient rotations
- `_load_absence_assignments()` - Leave, Weekend, TDY
- `_load_offsite_assignments()` - Hilo, Kapiolani, Okinawa
- `_load_recovery_assignments()` - Post-Call Recovery
- `_load_education_assignments()` - FMO, GME, Lectures

**Conflict filtering** in `_create_assignments_from_result()`:
```python
occupied_slots: set[tuple[UUID, UUID]] = set()
if existing_assignments:
    for a in existing_assignments:
        occupied_slots.add((a.person_id, a.block_id))

# Skip solver assignments that conflict with preserved slots
if (person_id, block_id) in occupied_slots:
    skipped += 1
    continue
```

**Faculty supervision fix** in `_assign_faculty()`:
```python
# Check both preserved assignments AND session assignments
faculty_occupied_slots: set[tuple[UUID, UUID]] = set()
if preserved_assignments:
    for a in preserved_assignments:
        if a.person_id in faculty_ids:
            faculty_occupied_slots.add((a.person_id, a.block_id))
for a in self.assignments:
    if a.person_id in faculty_ids:
        faculty_occupied_slots.add((a.person_id, a.block_id))
```

**Deferred deletion** for data safety:
- Old: Delete existing assignments before solving
- New: Delete only after successful solve, preserving data on solver failure

---

## Bug Fix: PostFMITRecoveryConstraint

### Discovery

The constraint class existed in `backend/app/scheduling/constraints/fmit.py` (line 468) but was never added to the default constraint manager. This meant faculty were not getting their Friday recovery day blocked after FMIT weeks.

### Fix

Added to `backend/app/scheduling/constraints/manager.py`:
```python
# Block 10 hard constraints - inpatient headcount and post-FMIT blocking
manager.add(ResidentInpatientHeadcountConstraint())
manager.add(PostFMITRecoveryConstraint())  # Faculty Friday PC after FMIT
manager.add(PostFMITSundayBlockingConstraint())
```

### Why It Only Affects Faculty

The constraint identifies FMIT weeks by matching template names containing "FMIT":
```python
is_fmit = (
    hasattr(template, "activity_type")
    and template.activity_type == "inpatient"
    and hasattr(template, "name")
    and "FMIT" in template.name.upper()
)
```

Template naming:
- Faculty: "FMIT AM", "FMIT PM" → matches "FMIT" ✓
- Residents: "Family Medicine Inpatient Team Intern" → does NOT match ✗

Residents work 6 days/week on FMIT with no PC day. Faculty get Friday PC to compensate for mandatory weekend call duties during FMIT week.

---

## Domain Knowledge Captured

From user during session:

1. **"FMIT faculty cannot supervise clinic"** - Faculty on FMIT weeks must be excluded from clinic supervision assignments

2. **"absences in general"** - Leave, Weekend, and TDY should all be preserved as immutable

3. **"residents work 6 days a week"** - Residents on FMIT don't get a PC day, unlike faculty

4. **"faculty get PC day to make up for weekend lost, plus the crazy call at the start"** - Faculty FMIT includes mandatory Fri/Sat night call

---

## Files Modified

### Core Engine
- `backend/app/scheduling/engine.py` (+211 lines)
  - 6 loader methods for preserved assignments
  - Conflict filtering in `_create_assignments_from_result()`
  - Faculty occupied slot checking in `_assign_faculty()`
  - Deferred deletion safety

### Constraint Manager
- `backend/app/scheduling/constraints/manager.py` (+3 lines)
  - Import PostFMITRecoveryConstraint
  - Add to `create_default()` and `create_resilience_aware()`

---

## Verification

After fix:
- Solver returned status 207 (partial success)
- 59 outpatient assignments created
- 336 inpatient assignments preserved
- All 5 inpatient residents verified to have ONLY inpatient assignments
- No duplicate key violations

---

## Session Methodology

This session demonstrated effective human-AI collaboration:

1. **Claude Code Web** for data inspection - Verified JSON data and solver results in web interface
2. **Iterative debugging** - Each error revealed the next issue (residents → faculty → off-site → recovery → education)
3. **Domain expert input** - User provided critical context about FMIT week structure and PC rules
4. **Systematic constraint review** - Traced template → constraint → manager chain to find missing registration
