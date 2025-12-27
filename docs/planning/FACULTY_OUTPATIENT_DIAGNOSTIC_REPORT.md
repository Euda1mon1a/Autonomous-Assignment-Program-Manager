# Diagnostic Report: Faculty Outpatient Generation Issues

**Purpose:** Comprehensive diagnosis for handoff to Claude Code Web for parallel implementation

**Status:** ✅ COMPLETED (2025-12-27)

---

## Implementation Summary

All issues identified in this diagnostic report have been resolved:

| Issue | Status | Commit |
|-------|--------|--------|
| Supervision Calculation Bug | ✅ Fixed | `bec6efe` |
| Adjunct Faculty Role | ✅ Added | `bec6efe` |
| PCAT Generation | ⏳ Deferred (depends on call schedule) | N/A |
| Documentation | ✅ Updated | `bec6efe` |

---

## Key Documentation References

Read these files for full context:

| Document | Path | Relevant Sections |
|----------|------|-------------------|
| **Faculty Scheduling Spec** | `docs/architecture/FACULTY_SCHEDULING_SPECIFICATION.md` | Supervision Ratios (line 259-272), Faculty Roles (line 38) |
| **Solver Algorithm** | `docs/architecture/SOLVER_ALGORITHM.md` | Post-processing faculty supervision (line 95) |
| **CLAUDE.md** | `CLAUDE.md` | ACGME compliance rules, supervision ratios |

**Documentation Status:** ✅ The supervision calculation example has been fixed to use fractional loads.

---

## Executive Summary

Three issues were identified with faculty outpatient generation:

1. ✅ **Supervision overcounting** (CRITICAL) - Fixed by switching to fractional load approach
2. ✅ **Missing adjunct faculty category** - Added ADJUNCT role with full frontend/backend support
3. ⏳ **PCAT not generating** (LOW PRIORITY) - Deferred; will auto-generate when call schedule is loaded

---

## Issue 1: Supervision Calculation Overcounting (CRITICAL) - ✅ FIXED

**Problem:** The implementation treated PGY-1 (1:2) and PGY-2/3 (1:4) supervision ratios as separate calculations with separate ceiling operations.

**Solution Implemented:** Switched to fractional supervision load approach:
- PGY-1: 0.5 supervision load each (1:2 ratio)
- PGY-2/3: 0.25 supervision load each (1:4 ratio)
- Sum all loads THEN ceiling to get required faculty

**Files Changed:**
| File | Change |
|------|--------|
| `backend/app/services/faculty_outpatient_service.py` | Lines 530-536: Fractional load calculation |
| `backend/app/scheduling/engine.py` | Lines 1271-1276: Integer math equivalent |
| `backend/app/scheduling/constraints/acgme.py` | Lines 546-567: Updated `calculate_required_faculty()` |
| `backend/tests/test_constraints.py` | Added `test_calculate_required_faculty_fractional_load()` |
| `docs/architecture/FACULTY_SCHEDULING_SPECIFICATION.md` | Fixed example at lines 261-272 |

**New Formula:**
```python
# Fractional load approach:
supervision_load = (pgy1_count * 0.5) + (other_count * 0.25)
required = ceil(supervision_load) if supervision_load > 0 else 0

# Integer math equivalent (used in some locations):
supervision_units = (pgy1_count * 2) + other_count  # intern=2, resident=1
required = (supervision_units + 3) // 4 if supervision_units > 0 else 0
```

**Test Coverage:**
| Interns | Residents | Expected | Verified |
|---------|-----------|----------|----------|
| 1 | 1 | 1 | ✅ |
| 1 | 2 | 1 | ✅ |
| 2 | 0 | 1 | ✅ |
| 2 | 2 | 2 | ✅ |
| 1 | 3 | 2 | ✅ |
| 4 | 0 | 2 | ✅ |
| 0 | 4 | 1 | ✅ |
| 3 | 4 | 3 | ✅ |

---

## Issue 2: Adjunct Faculty Category - ✅ IMPLEMENTED

**Problem:** Adjunct faculty who occasionally help with AT or FMIT needed a separate role for proper GUI management and scheduling treatment.

**Solution Implemented:**

### Backend Changes
| File | Change |
|------|--------|
| `backend/app/models/person.py` | Added `ADJUNCT = "adjunct"` to `FacultyRole` enum |
| `backend/app/models/person.py` | Added `FacultyRole.ADJUNCT: 0` to `weekly_clinic_limit` |
| `backend/app/schemas/person.py` | Added `ADJUNCT = "adjunct"` to `FacultyRoleSchema` |
| `backend/app/services/faculty_outpatient_service.py` | Excluded adjunct from `_get_available_faculty()` |

### Frontend Changes
| File | Change |
|------|--------|
| `frontend/src/types/api.ts` | Added `FacultyRole` enum with all 7 roles |
| `frontend/src/types/api.ts` | Added `faculty_role` to `Person`, `PersonCreate`, `PersonUpdate` |
| `frontend/src/components/AddPersonModal.tsx` | Added faculty role dropdown for faculty type |
| `frontend/src/components/EditPersonModal.tsx` | Added faculty role dropdown with pre-population |

### Adjunct Role Behavior
- **Weekly clinic limit:** 0 (not auto-scheduled)
- **Auto-scheduling:** Excluded from `FacultyOutpatientAssignmentService`
- **FMIT eligible:** Yes (can be pre-loaded via block schedule)
- **GUI:** Full support in Add/Edit Person modals

---

## Issue 3: PCAT Not Being Generated - ⏳ DEFERRED

**Problem:** PCAT (Post-Call Attending) is a special AT rotation auto-assigned after being on call. It's not being generated because call assignments haven't been loaded yet.

**Root cause:** Call schedule not loaded → no overnight call assignments → no post-call PCAT generation

**Action:** No code changes needed. PCAT will auto-generate once call schedule is loaded and PostCallConstraint runs.

---

## File Manifest (Final)

| File Path | Issue | Status |
|-----------|-------|--------|
| `backend/app/services/faculty_outpatient_service.py` | 1, 2 | ✅ Fixed |
| `backend/app/scheduling/engine.py` | 1 | ✅ Fixed |
| `backend/app/scheduling/constraints/acgme.py` | 1 | ✅ Fixed |
| `backend/app/models/person.py` | 2 | ✅ Updated |
| `backend/app/schemas/person.py` | 2 | ✅ Updated |
| `backend/tests/test_constraints.py` | 1 | ✅ Tests added |
| `frontend/src/types/api.ts` | 2 | ✅ Updated |
| `frontend/src/components/AddPersonModal.tsx` | 2 | ✅ Updated |
| `frontend/src/components/EditPersonModal.tsx` | 2 | ✅ Updated |
| `docs/architecture/FACULTY_SCHEDULING_SPECIFICATION.md` | 1 | ✅ Fixed |

---

## Related PRs

- **PR #466**: Added `FacultyOutpatientAssignmentService` with this diagnostic report
- **Commit `bec6efe`**: Implemented all fixes identified in this report
