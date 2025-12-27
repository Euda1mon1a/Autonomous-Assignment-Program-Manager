# Diagnostic Report: Faculty Outpatient Generation Issues

**Purpose:** Comprehensive diagnosis for handoff to Claude Code Web for parallel implementation

---

## Key Documentation References

Read these files for full context:

| Document | Path | Relevant Sections |
|----------|------|-------------------|
| **Faculty Scheduling Spec** | `docs/architecture/FACULTY_SCHEDULING_SPECIFICATION.md` | Supervision Ratios (line 243), Faculty Roles (line 38) |
| **Solver Algorithm** | `docs/architecture/SOLVER_ALGORITHM.md` | Post-processing faculty supervision (line 95) |
| **CLAUDE.md** | `CLAUDE.md` | ACGME compliance rules, supervision ratios |

**WARNING:** The documentation at line 261-268 has the WRONG example:
```
# CURRENT DOCS (WRONG):
3 PGY-1 → ceil(3/2) = 2
2 PGY-2 → ceil(2/4) = 1
2 PGY-3 → ceil(2/4) = 1
Total: 2+1+1 = 4 faculty  ← WRONG

# CORRECT:
3 PGY-1 × 0.5 = 1.5 supervision load
2 PGY-2 × 0.25 = 0.5
2 PGY-3 × 0.25 = 0.5
Total: ceil(1.5+0.5+0.5) = ceil(2.5) = 3 faculty  ← CORRECT
```

**Action:** Also update `docs/architecture/FACULTY_SCHEDULING_SPECIFICATION.md` lines 261-268

---

## Executive Summary

Three issues identified with faculty outpatient generation:
1. **Supervision overcounting** (CRITICAL) - Wrong formula causes 2x faculty assignments in mixed PGY scenarios
2. **Missing adjunct faculty category** - Adjunct faculty need separate role for GUI management
3. **PCAT not generating** (LOW PRIORITY) - Depends on call schedule not yet loaded

---

## Issues Identified

### Issue 1: Supervision Calculation Overcounting (CRITICAL)

**Problem:** The current implementation treats PGY-1 (1:2) and PGY-2/3 (1:4) supervision ratios as separate calculations with separate ceiling operations:

```python
# CURRENT (WRONG)
required = ceil(pgy1_count / 2) + ceil(other_count / 4)
```

**Correct approach:** Each resident contributes a fractional supervision load:
- Intern (PGY-1) = 0.5 supervision load (1:2 ratio)
- Resident (PGY-2/3) = 0.25 supervision load (1:4 ratio)
- Sum all loads, THEN ceiling to get required faculty

**Example where current overcounts:**
| Scenario | Correct | Current |
|----------|---------|---------|
| 1 PGY-1 + 1 PGY-2 | ceil(0.5 + 0.25) = 1 | ceil(0.5) + ceil(0.25) = 2 |
| 1 PGY-1 + 2 PGY-2 | ceil(0.5 + 0.5) = 1 | ceil(0.5) + ceil(0.5) = 2 |
| 1 PGY-1 + 3 PGY-2 | ceil(0.5 + 0.75) = 2 | ceil(0.5) + ceil(0.75) = 2 |

**Affected Code Locations:**

**Location 1:** `backend/app/services/faculty_outpatient_service.py` lines 530-531
```python
# Current code (WRONG):
pgy1_count = sum(1 for a in block_assignments
    if resident_lookup.get(a.person_id)
    and resident_lookup[a.person_id].pgy_level == 1)
other_count = len(block_assignments) - pgy1_count
required = ceil(pgy1_count / 2) + ceil(other_count / 4)  # <-- BUG HERE
```

**Location 2:** `backend/app/scheduling/engine.py` line 1272
```python
# Current code (WRONG):
pgy1_count = sum(1 for r in residents_in_block if r.pgy_level == 1)
other_count = len(residents_in_block) - pgy1_count
required = (pgy1_count + 1) // 2 + (other_count + 3) // 4  # <-- BUG HERE
```

**Location 3:** `backend/app/scheduling/constraints/acgme.py` lines 555-560
```python
# SupervisionRatioConstraint.calculate_required_faculty()
def calculate_required_faculty(self, pgy1_count: int, other_count: int) -> int:
    from_pgy1 = (pgy1_count + self.PGY1_RATIO - 1) // self.PGY1_RATIO
    from_other = (other_count + self.OTHER_RATIO - 1) // self.OTHER_RATIO
    return max(1, from_pgy1 + from_other) if (pgy1_count + other_count) > 0 else 0
    # ^-- BUG: Separate ceiling operations
```

**Correct Formula:**
```python
# Fractional load approach:
supervision_load = (pgy1_count * 0.5) + (other_count * 0.25)
required = ceil(supervision_load) if supervision_load > 0 else 0

# OR integer math equivalent:
supervision_units = (pgy1_count * 2) + other_count  # intern=2, resident=1
required = (supervision_units + 3) // 4 if supervision_units > 0 else 0  # 4 units per faculty
```

---

### Issue 2: Adjunct Faculty Category

**Problem:** Two faculty members are adjunct faculty who occasionally help with AT or FMIT but don't belong to the program. They need:
1. A separate category to distinguish them from core program faculty
2. GUI support to add/manage them
3. Different scheduling treatment (pre-loaded to FMIT, excluded from auto-scheduling)

**Use case:** When adjunct faculty are pre-loaded to FMIT weeks, this frees up program faculty for clinic/supervision assignments.

**Specific adjunct faculty to reclassify:**
- FAC-ADJ-01 (see local database for identity)
- FAC-ADJ-02 (see local database for identity)

**From docs/architecture/FACULTY_SCHEDULING_SPECIFICATION.md line 529:**
> "Adjunct faculty are manually placed and not subject to automated scheduling constraints."

**Current state:**
- FacultyRole enum has 6 roles: pd, apd, oic, dept_chief, sports_med, core
- No adjunct/external category exists
- Frontend doesn't expose faculty_role field in Add/Edit modals

**Solution:** Add `ADJUNCT` role to FacultyRole enum with special handling:
- Weekly clinic limit: 0 (not auto-scheduled to clinic/supervision)
- FMIT eligible: Yes (can be pre-loaded via block schedule)
- Auto-scheduling: Excluded from FacultyOutpatientAssignmentService
- GUI: Add faculty_role dropdown to Add/Edit Person modals

**Affected Code Locations:**

**Location 1:** `backend/app/models/person.py` lines 14-28 (FacultyRole enum)
```python
class FacultyRole(str, Enum):
    PD = "pd"
    APD = "apd"
    OIC = "oic"
    DEPT_CHIEF = "dept_chief"
    SPORTS_MED = "sports_med"
    CORE = "core"
    # ADD: ADJUNCT = "adjunct"
```

**Location 2:** `backend/app/models/person.py` lines 178-189 (weekly_clinic_limit property)
```python
@property
def weekly_clinic_limit(self) -> int:
    limits = {
        FacultyRole.PD: 0,
        FacultyRole.DEPT_CHIEF: 1,
        FacultyRole.APD: 2,
        FacultyRole.OIC: 2,
        FacultyRole.SPORTS_MED: 0,
        FacultyRole.CORE: 4,
        # ADD: FacultyRole.ADJUNCT: 0,
    }
```

**Location 3:** `backend/app/schemas/person.py` lines 12-18 (FacultyRoleSchema)
```python
class FacultyRoleSchema(str, Enum):
    PD = "pd"
    APD = "apd"
    # ... etc
    # ADD: ADJUNCT = "adjunct"
```

**Location 4:** `backend/app/services/faculty_outpatient_service.py` (exclude from auto-scheduling)
```python
def _get_available_faculty(self, block_start, block_end):
    # ... existing logic ...
    # ADD: Exclude adjunct faculty
    available = [f for f in available if f.role_enum != FacultyRole.ADJUNCT]
```

**Location 5:** `frontend/src/components/AddPersonModal.tsx` (add dropdown)
- Add faculty_role select when type === 'faculty'
- Options: Program Director, Assoc PD, OIC, Dept Chief, Sports Med, Core, Adjunct

**Location 6:** `frontend/src/components/EditPersonModal.tsx` (add dropdown)
- Same as AddPersonModal

---

### Issue 3: PCAT Not Being Generated (Lower Priority)

**Problem:** PCAT (Post-Call Attending) is a special AT rotation auto-assigned after being on call. It's not being generated because call assignments haven't been loaded yet.

**Root cause:** Call schedule not loaded → no overnight call assignments → no post-call PCAT generation

**Action:** File for later investigation. Not blocking current work. PCAT will be generated automatically once call schedule is loaded and PostCallConstraint runs.

---

## Handoff Summary for Claude Code Web

### Task 1: Fix Supervision Calculation (Backend Only)

**Files to modify:**
1. `backend/app/services/faculty_outpatient_service.py` - lines 530-531
2. `backend/app/scheduling/engine.py` - line 1272
3. `backend/app/scheduling/constraints/acgme.py` - lines 555-560

**Change:** Replace separate ceiling operations with fractional load calculation:
```python
# FROM: required = ceil(pgy1_count / 2) + ceil(other_count / 4)
# TO:   supervision_load = (pgy1_count * 0.5) + (other_count * 0.25)
#       required = ceil(supervision_load) if supervision_load > 0 else 0
```

**Test cases:**
| Interns | Residents | Expected Faculty |
|---------|-----------|------------------|
| 1 | 1 | 1 |
| 1 | 2 | 1 |
| 2 | 0 | 1 |
| 2 | 2 | 2 |
| 1 | 3 | 2 |
| 4 | 0 | 2 |
| 0 | 4 | 1 |

---

### Task 2: Add Adjunct Faculty Role (Backend + Frontend)

**Backend files:**
1. `backend/app/models/person.py` - Add ADJUNCT to FacultyRole enum
2. `backend/app/schemas/person.py` - Add ADJUNCT to FacultyRoleSchema
3. `backend/app/services/faculty_outpatient_service.py` - Exclude adjunct from auto-scheduling

**Frontend files:**
4. `frontend/src/components/AddPersonModal.tsx` - Add faculty_role dropdown
5. `frontend/src/components/EditPersonModal.tsx` - Add faculty_role dropdown

**Behavior:**
- Adjunct weekly_clinic_limit = 0
- Adjunct excluded from `_get_available_faculty()`
- Can still be manually assigned to FMIT/AT via pre-loading

---

### Task 3: PCAT Investigation (Deferred)

**Root cause:** Call schedule not loaded yet → no post-call assignments → no PCAT generation

**Action:** No code changes needed. PCAT will auto-generate once call is loaded.

---

## File Manifest

| File Path | Issue | Change Type |
|-----------|-------|-------------|
| `backend/app/services/faculty_outpatient_service.py` | 1, 2 | Edit |
| `backend/app/scheduling/engine.py` | 1 | Edit |
| `backend/app/scheduling/constraints/acgme.py` | 1 | Edit |
| `backend/app/models/person.py` | 2 | Edit |
| `backend/app/schemas/person.py` | 2 | Edit |
| `frontend/src/components/AddPersonModal.tsx` | 2 | Edit |
| `frontend/src/components/EditPersonModal.tsx` | 2 | Edit |
| `docs/architecture/FACULTY_SCHEDULING_SPECIFICATION.md` | 1 | Edit (fix example) |
