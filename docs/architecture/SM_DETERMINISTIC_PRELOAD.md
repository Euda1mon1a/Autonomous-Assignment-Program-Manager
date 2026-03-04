# Sports Medicine (SM) Deterministic Preload Design

> **Created:** 2026-02-28
> **Status:** Proposed
> **Priority:** HIGH — blocks solver accuracy for SM faculty
> **Depends on:** Activity Classification Phase 1 (PR #1213), Template-Authoritative Write-Back (PR #1212)
> **Cross-refs:** [`FACULTY_FIX_ROADMAP.md`](FACULTY_FIX_ROADMAP.md) Phase 2.5, [`MASTER_PRIORITY_LIST.md`](../planning/MASTER_PRIORITY_LIST.md) Item 6

---

## Problem Statement

SM_CLINIC is the **only activity** in the system that is simultaneously:
- **Supervision** (`provides_supervision = true`) — counts toward ACGME supervision ratios
- **Physical capacity** (`counts_toward_physical_capacity = true`) — counts toward max-6/slot clinic limit

This dual classification makes SM fundamentally incompatible with the solver's binary C/AT model. The solver can assign SM faculty to `fac_clinic` (correct for capacity) or `fac_supervise` (correct for supervision), but **never both at once**. The template-authoritative write-back (PR #1212) then resolves the solver's coarse code to the template-specific `sm_clinic`, but the solver has already made a category decision that may be wrong.

**Practical consequence:** SM faculty frequently get assigned Monday SM clinic sessions, and then take Sunday call, resulting in **SM clinic the morning after overnight call** — a quality-of-life and patient-safety concern.

---

## Current State

### SM Faculty Template (SM Faculty Member)

| Day | AM | PM |
|-----|----|----|
| Mon | sm_clinic | sm_clinic |
| Tue | sm_clinic | sm_clinic |
| Wed | aSM | lec |
| Thu | sm_clinic | gme |
| Fri | sm_clinic | FMIT |
| Sat | W | W |
| Sun | W | W |

**Key observations:**
- **Monday is the problem.** Sunday call → Monday PCAT is a hard constraint. But even without PCAT, Monday SM clinic after Sunday overnight is poor scheduling.
- **Friday PM = FMIT.** During FMIT rotation weeks (~6/year), the entire week is inpatient service, making all SM slots unavailable.
- **Wednesday = split.** AM is aSM (Advanced SM — educational), PM is LEC (protected). Neither is standard SM clinic.

### How SM Is Currently Handled

| File | Classification | Notes |
|------|---------------|-------|
| `engine.py` write-back | **Clinic** (C) | Template resolves solver C → sm_clinic |
| `activity_solver.py` | **Admin** (AT) | `ADMIN_ACTIVITY_CODES = {"SM": "sm_clinic"}` |
| `fmc_capacity.py` | **Separate track** | `SM_CAPACITY_CODES = {"SM", "SM_CLINIC", "ASM"}` |
| `activity_solver.py:2026-2107` | **Soft constraint** | SM alignment penalty=30 |

The **disagreement** between engine.py (clinic) and activity_solver.py (admin) means SM may be double-counted or miscounted depending on which code path runs.

### Solver SM Alignment (Current)

`activity_solver.py:2026-2107` has a soft constraint (`SM_ALIGNMENT`, penalty=30) that tries to align resident SM assignments with faculty SM availability. But this operates at the activity solver level — **after** the CP-SAT solver has already decided faculty C/AT assignments. The alignment is best-effort, not guaranteed.

---

## Proposed Solution: Deterministic SM Preload

**Remove SM from solver optimization entirely.** Instead, preload SM slots from faculty weekly templates with exclusion logic, then mark them as `is_protected = true` so the solver treats them as fixed.

### Why Preload?

1. **SM is template-driven.** The SM faculty member's weekly pattern is fixed — same days every week. There's nothing to "optimize."
2. **Avoids post-call conflicts.** Exclusion logic can check call assignments and skip SM on post-call days.
3. **Avoids FMIT collisions.** Exclusion logic can check inpatient preloads and skip entire FMIT weeks.
4. **Simplifies solver.** One fewer faculty member in the C/AT optimization space. Solver handles remaining 9 faculty.
5. **Preserves equity.** SM faculty remains in the call pool. Only the SM *clinic assignment* is deterministic — call distribution stays solver-optimized.

### Exclusion Rules

For each SM template slot (day + AM/PM):

```
1. FMIT week?     → Skip entire week (Fri→Thu rotation makes all slots unavailable)
2. Post-call day? → Skip (PCAT AM is hard constraint; PM should also be protected)
3. Monday?        → Skip (Sunday call risk — even without actual call, Monday SM
                    creates scheduling fragility)
```

### What Replaces Excluded Slots?

| Exclusion | Replacement | Rationale |
|-----------|-------------|-----------|
| FMIT week | FMIT preload handles it | Already covered by `_load_fmit_call` |
| Post-call day | PCAT (AM) + DO (PM) | Already covered by call chain |
| Monday | **Solver decides** (C or AT) | Falls back to normal solver optimization |

**Monday fallback:** When Monday SM is excluded, the slot reverts to solver control. The solver will assign C or AT based on capacity/supervision needs. The write-back will then resolve to the template's non-SM activity for that slot (if one exists) or use the generic solver type.

**Coordinator decision needed:** Should Monday slots have an explicit alternative template activity (e.g., `at`, `gme`), or should we let the solver decide? Current template shows `sm_clinic` on Monday — a new Monday-specific template entry may be needed.

### Data Sources for Exclusion Checks

| Check | Data Source | Query |
|-------|-------------|-------|
| FMIT week | `inpatient_preloads` | `WHERE person_id = :sm_faculty AND rotation = 'FMIT' AND date_range overlaps block` |
| Post-call | `call_assignments` | `WHERE person_id = :sm_faculty AND date = :day_before` |
| Monday | `slot_date.weekday() == 0` | Pure Python check |

**Note on post-call:** At preload time, call assignments for the current block may not exist yet (solver hasn't run). Two options:
1. **Two-pass approach:** Preload SM first (skip Mondays + FMIT weeks), then after solver assigns calls, remove SM from post-call days in a cleanup pass.
2. **Historical pattern:** Use prior block's call pattern as a heuristic (unreliable).
3. **Accept the risk:** Monday exclusion already eliminates the worst case (Sunday call → Monday SM). Tue-Thu post-call SM is less common and less problematic.

**Recommended:** Option 1 (two-pass) for correctness, with Monday exclusion as the primary safety net.

---

## Implementation Plan

### Step 1: SM Preload Function

**File:** `backend/app/services/preload/sm_preload.py` (NEW)

```python
def preload_sm_faculty_slots(
    db: Session,
    block_start: date,
    block_end: date,
    sm_faculty_id: UUID,
) -> list[HalfDayAssignment]:
    """Preload SM clinic slots from weekly template with exclusion logic.

    Exclusions:
    1. FMIT weeks (entire week skipped)
    2. Mondays (Sunday call risk)
    3. Post-call days (cleanup pass after solver)
    """
    # Load SM faculty weekly template entries where activity = sm_clinic
    # Load FMIT weeks from inpatient_preloads
    # For each day in block:
    #   if day is in FMIT week → skip
    #   if day.weekday() == 0 → skip (Monday)
    #   if template has sm_clinic for this day/slot → create HDA
    # Mark all created HDAs as source='preload', is_protected=True
```

### Step 2: Wire Into Preload Pipeline

**File:** `backend/app/services/preload/sync_preload_service.py`

Add SM preload after FMIT preload, before solver runs. SM preload needs FMIT preload results to check exclusions.

### Step 3: Post-Solver Cleanup Pass

**File:** `backend/app/scheduling/engine.py`

After solver assigns calls, check if any SM preloaded slots conflict with post-call. If so, convert SM → solver-decided (remove `is_protected`, re-run activity assignment for that slot).

### Step 4: Remove SM from Solver

**File:** `backend/app/scheduling/solvers.py`

Exclude SM faculty from `fac_clinic`/`fac_supervise` variable creation. SM slots are already preloaded; solver should not create variables for them.

**Caution:** SM faculty still needs call variables (`fac_call`, PCAT, DO). Only skip C/AT variables for SM-preloaded slots.

### Step 5: Clean Up Activity Solver SM Alignment

**File:** `backend/app/scheduling/activity_solver.py`

Remove or disable the SM alignment soft constraint (lines 2026-2107) — it's no longer needed since SM is preloaded deterministically.

### Step 6: Resident SM Alignment

Residents assigned to SM rotation still need their clinic slots aligned with the SM faculty member's preloaded SM slots. The activity solver's resident assignment should query preloaded SM faculty slots and place resident SM clinic sessions on matching days.

---

## SM_CLINIC Classification Resolution

With SM preloaded deterministically, the classification disagreement becomes less critical but should still be resolved for consistency:

| Property | Current | Correct | Rationale |
|----------|---------|---------|-----------|
| `counts_toward_physical_capacity` | `true` | `true` | SM generates patient load — screeners, room, MA |
| `provides_supervision` | `true` | `true` | SM faculty supervises residents during SM clinic |
| `is_solver_clinic` | `true` | N/A (preloaded) | Not in solver's variable space anymore |
| `is_solver_admin` | `false` | N/A (preloaded) | Not in solver's variable space anymore |

**Key insight:** By preloading SM, we sidestep the dual-classification problem entirely. SM doesn't need to fit the binary C/AT model because it never enters the solver.

---

## FMIT Week Collision Detail

SM faculty template shows Friday PM = FMIT. During FMIT rotation weeks (~6 per year, Fri→Thu cycle):

```
Week of FMIT:
  Fri: FMIT (all day) — SM template says SM AM / FMIT PM → FMIT wins
  Sat: FMIT call (overnight)
  Sun: FMIT call recovery
  Mon: FMIT inpatient
  Tue: FMIT inpatient
  Wed: FMIT inpatient
  Thu: FMIT inpatient (last day)
```

The FMIT preload already handles the inpatient week. SM preload must check against it to avoid creating SM HDAs that conflict with FMIT rotation assignments.

**Query pattern:**
```sql
SELECT DISTINCT date
FROM inpatient_preloads
WHERE person_id = :sm_faculty_id
  AND date >= :block_start
  AND date <= :block_end;
```

Any date in this result set → skip SM preload for that date.

---

## Call Equity Preservation

SM faculty remains fully in the call assignment pool:
- **Sunday call:** SM faculty eligible (Monday SM already excluded)
- **Weekday call (Mon-Thu):** SM faculty eligible (post-call cleanup handles next-day SM)
- **FMIT call (Fri-Sat):** Already handled by FMIT preload
- **Holiday call:** SM faculty eligible

**Equity mechanism:** `call_equity.py` MAD formulation (PR #1199) treats SM faculty identically to other faculty for call distribution. No change needed.

---

## Testing Plan

| Test | Scope | Type |
|------|-------|------|
| SM preload creates HDAs for Tue-Thu template slots | Unit | `test_sm_preload.py` |
| SM preload skips Mondays | Unit | `test_sm_preload.py` |
| SM preload skips FMIT weeks | Unit | `test_sm_preload.py` |
| Post-solver cleanup removes SM on post-call days | Unit | `test_sm_preload.py` |
| Solver does not create C/AT variables for SM-preloaded slots | Unit | `test_solvers.py` |
| SM alignment constraint removed/disabled | Unit | `test_activity_solver.py` |
| Resident SM sessions align with faculty SM preload | Integration | `test_sm_preload.py` |
| Block 12 full pipeline with SM preload | E2E | `schedule_grid` validation |

---

## Files

| File | Action | Phase |
|------|--------|-------|
| `backend/app/services/preload/sm_preload.py` | NEW | Step 1 |
| `backend/app/services/preload/sync_preload_service.py` | MODIFY | Step 2 |
| `backend/app/scheduling/engine.py` | MODIFY | Steps 3-4 |
| `backend/app/scheduling/solvers.py` | MODIFY | Step 4 |
| `backend/app/scheduling/activity_solver.py` | MODIFY | Steps 5-6 |
| `backend/tests/services/test_sm_preload.py` | NEW | All steps |

---

## Open Questions

1. **Monday alternative activity:** What should SM faculty do on Mondays? Options: AT (supervision), GME (admin), or solver-decided. Needs coordinator input.
2. **Wednesday aSM:** Is Advanced SM also deterministic, or does it stay solver-controlled? Current template shows aSM on Wed AM only.
3. **Multiple SM faculty:** If a second SM faculty member is added in the future, does this approach scale? Yes — each SM faculty member gets independent preload with the same exclusion logic.
4. **SM resident supervision:** Do residents need an SM faculty member present for every SM clinic session, or can they work independently for some? Affects whether preload must guarantee faculty-resident alignment.
