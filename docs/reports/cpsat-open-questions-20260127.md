# CP-SAT Semantics Alignment: Open Questions + Recommendations

**Date:** 2026-01-27
**Updated:** 2026-01-27 (reordered priorities, step-wise approach for Codex)
**Purpose:** Capture open questions, recommended decisions (with risk/benefit), and a step-wise implementation plan.

---

## Critical Framing: Human vs CP-SAT "Hard Constraints"

Before proceeding, understand this distinction:

| Concept | Human Understanding | CP-SAT Understanding |
|---------|--------------------|-----------------------|
| "Hard constraint" | "Really important, should never happen" | "If violated by 0.001, model is INFEASIBLE—no schedule produced" |
| "Optimal schedule" | "Complete, correct, all fields populated" | "Best assignment of variables I was told about" |
| "Backfill needed" | "Solver missed something" | "Creation code didn't set fields I don't know about" |

**Decision rule:** Ask "If violated by 1 unit, is the schedule usable?"
- **No** → Hard constraint (physics, accreditation)
- **Yes, but worse** → Soft constraint with penalty

**CP-SAT only optimizes what you encode.** If `activity_id` isn't in the model, CP-SAT doesn't set it.

---

## Ground Rules (Current Intent)

- **Assignments, not rotations, drive physical capacity.**
- **Faculty AT hard capacity counts only for:** `AT`, `PCAT`.
- **PROC/VAS:** do **not** count toward hard AT capacity, but **do** add a soft penalty
  to reflect supervision load.
- **C** is the display abbreviation for clinic assignments.
- **CV** does **not** count toward FMC physical capacity, but **does** require
  AT/PCAT supervision coverage.
- **Clinic floor** is enforced **only when CV is not allowed** (PGY‑1 or non‑FMC
  templates). CV‑eligible PGY‑2/3 can satisfy clinic weeks with CV if capacity
  binds.
- **Dev environment:** No production data. "Backfill" = fix creation code + delete+regen.

---

## Reordered Decision Queue (Confirmed)

Priority order based on dependencies:

| Priority | Question | Why This Order |
|----------|----------|----------------|
| **P0** | Q2: activity_id canonical | Foundation for all capacity logic |
| **P1** | Q5: CV capacity (zero/zero) | Clarifies capacity model before constraints |
| **P2** | Q3: Preload vs solve | Depends on activity_id being reliable |
| **P3** | Q1: Post-call PCAT/DO | Depends on activity definitions being clean |
| **P4** | Q4: SM capacity_units | Enhancement, not blocker |
| **P5** | Q6: "Backfill" scope | Last—rules must be stable first |

---

## Step-Wise Implementation Plan for Codex

### Step 0: Understand the Data Flow

```
CP-SAT Model → Activity Solver → Service Layer → Database
     ↓              ↓                 ↓              ↓
  Variables    Activity IDs      Validation      Storage
  (minimal)    (must derive)    (must enforce)   (rejects bad)
```

**Key insight:** CP-SAT outputs minimal data. The activity solver and service layer are responsible for deriving `activity_id`, `counts_toward_fmc_capacity`, etc.

---

### Step 1: Make activity_id Canonical (P0)

**Goal:** Eliminate NULL activity_id rows permanently.

**Substeps:**

1. **Audit creation code paths** that produce WeeklyPattern/Assignment:
   ```bash
   grep -r "WeeklyPattern(" backend/app/ --include="*.py" | grep -v test
   grep -r "Assignment(" backend/app/ --include="*.py" | grep -v test
   ```

2. **Fix each code path** to always set activity_id (reject unknown activity_type):
   ```python
   # BEFORE (broken)
   WeeklyPattern(
       person_id=person_id,
       activity_type=activity_type,
       # activity_id not set → NULL
   )

   # AFTER (correct)
   activity = activity_repo.get_by_type(activity_type)
   if not activity:
       logger.error(f"Unknown activity_type: {activity_type}")
       raise ValueError(
           f"Unknown activity_type: {activity_type}. Valid types: {activity_repo.list_codes()}"
       )
   WeeklyPattern(
       person_id=person_id,
       activity_type=activity_type,
       activity_id=activity.id,  # Always set
       counts_toward_fmc_capacity=activity.counts_toward_fmc_capacity,
   )
   ```

3. **Add service layer validation:**
   ```python
   def create_weekly_pattern(self, data: WeeklyPatternCreate) -> WeeklyPattern:
       if not data.activity_id:
           if data.activity_type:
               data.activity_id = self._resolve_activity_id(data.activity_type)
           else:
               raise ValueError("activity_id or activity_type required")
       return self.repo.create(data)
   ```

4. **Make DB column NOT NULL** (after fixing code):
   ```python
   # Migration
   activity_id = Column(UUID, ForeignKey("activities.id"), nullable=False)
   ```

5. **Clear dev data and regenerate (dev only):**
   ```bash
   # Dev only - nuclear option
   DELETE FROM weekly_patterns WHERE activity_id IS NULL;
   # Or full regenerate after code fix
   ```

**Acceptance criteria:**
- [ ] All WeeklyPattern/Assignment creation sets activity_id
- [ ] Service layer rejects missing activity_id
- [ ] DB column is NOT NULL
- [ ] Zero NULL rows after regeneration

---

### Step 2: Clarify CV Capacity + Target (P1)

**Decision:** CV = zero physical capacity **but requires AT/PCAT supervision**.
Additionally, CV is a **proactive target** (not a fallback) for **faculty + PGY‑3**
in FMC clinic.

**Substeps:**

1. **Update activity definition** (if not already):
   ```python
   # activities table or seed data
   CV: counts_toward_fmc_capacity=False, requires_supervision=True
   ```

2. **Document in code:**
   ```python
   # In capacity constraint
   # CV is virtual - no physical presence
   # BUT it still requires AT/PCAT supervision coverage
   ```

3. **Add CV target constraint (faculty + PGY‑3, FMC clinic only):**
   ```python
   # Per-week group target (soft):
   # 10 * CV >= 3 * (C + CV)  with penalty for shortfall
   # Include locked/preloaded C/CV in the denominator (group-level)
   ```

4. **Role policy:**
   - Faculty: preferred CV (no penalty)
   - PGY‑3: allowed, low penalty
   - PGY‑2: overflow only, medium penalty
   - PGY‑1: excluded from CV

**Acceptance criteria:**
- [ ] CV activity definition has both capacity flags = False
- [ ] CV assignments still require AT/PCAT coverage
- [ ] Weekly CV target enforced for faculty + PGY‑3 (FMC clinic only)
- [ ] Target includes locked/preloaded C/CV counts in the denominator

**Open question (new):** Preloaded C slots reduce the overall 30% ratio.
Options:
- Allow conversion of some preloaded C → CV (policy change).
- Add CV requirements to rotation templates for faculty/PGY‑3.
- Increase shortfall penalty (accept solver tradeoffs).

---

### Step 3: Preload vs Solve for Clinic (P2)

**Decision:**
- Inpatient rotations → Preload C from **weekly patterns**
- Outpatient rotations → Solve via activity solver (CV **proactive**, not fallback)

**Substeps:**

1. **Preload logic** respects `rotation_type`:
   ```python
   if rotation_template.rotation_type == "inpatient":
       preload_clinic_from_weekly_patterns(person, rotation)
   # Outpatient rotations leave clinic to activity solver
   ```

2. **Activity solver** only allocates clinic for outpatient:
   ```python
   # Skip clinic allocation if already preloaded (inpatient)
   if person_has_preloaded_clinic(person, week):
       continue
   ```

3. **CV proactive target for outpatient FMC clinic**:
   ```python
   # CV is a planned assignment (targeted), not an overflow fallback
   ```

**Acceptance criteria:**
- [ ] Inpatient rotations have clinic preloaded
- [ ] Outpatient rotations get clinic from activity solver only
- [ ] No double-allocation of clinic slots
- [ ] CV is assigned to meet the 30% weekly target (faculty + PGY‑3)
- [ ] No hard capacity infeasibility (hard 8 respected)

---

### Step 4: Post-Call PCAT/DO as Soft Constraint (P3)

**Decision:** Soft constraint with LV/HOL/blocking-absence exemption, not hard.
Locked blocks and blocking absences exempt the penalty.

**Rationale:** A schedule with 1 post-call gap is better than no schedule. Post-call is training priority, not physics.

**Substeps:**

1. **Change PostCallAutoAssignmentConstraint** from HardConstraint to SoftConstraint:
   ```python
   class PostCallAutoAssignmentConstraint(SoftConstraint):  # Was HardConstraint
       DEFAULT_PENALTY = 35  # Between AT coverage (50) and activity min (10)
   ```

2. **Add LV/HOL/FMIT + blocking-absence exemption logic:**
   ```python
   def _is_exempt(self, next_day_slot, context) -> bool:
       """Check if next day is exempt from post-call requirement."""
       next_day_activity = self._get_locked_activity(next_day_slot)
       if next_day_activity in ("LV", "HOL", "FMIT"):
           return True
       # Also exempt if person has blocking absence
       if self._has_blocking_absence(next_day_slot, context):
           return True
       return False
   ```

3. **Log gaps instead of failing:**
   ```python
   if not self._is_exempt(next_day, context) and not has_pcat_do:
       # Add penalty, don't fail
       model.Add(penalty_var == self.DEFAULT_PENALTY)
       logger.warning(f"Post-call gap: {person_id} on {next_day}")
   ```

**Acceptance criteria:**
- [ ] PostCallAutoAssignment is SoftConstraint
- [ ] LV/HOL/blocking absence exempts from requirement
- [ ] Gaps are logged with penalty, not INFEASIBLE

---

### Step 5: SM Capacity Units (P4)

**Decision:** Add `capacity_units` column, default 1, SM uses 1 regardless of learners.

**Substeps:**

1. **Add column to activities table:**
   ```python
   # Migration
   capacity_units = Column(Integer, default=1, nullable=False)
   ```

2. **Set SM to capacity_units=1** in seed/definition

3. **Update capacity constraint:**
   ```python
   physical_usage = sum(
       a.activity.capacity_units  # Use units, not count
       for a in slot_assignments
       if a.counts_toward_fmc_capacity
   )
   ```

**Acceptance criteria:**
- [ ] capacity_units column exists
- [ ] SM activity has capacity_units=1
- [ ] Capacity constraint uses units not row count

---

### Step 6: "Backfill" Scope (P5)

**Decision:** In dev, "backfill" = fix creation code + delete+regen. No historical migration needed.

**The insight:** There is no backfill. The problem was creation code not setting fields. Once code is fixed:

```bash
# Option A: Delete bad rows, regenerate
DELETE FROM weekly_patterns WHERE activity_id IS NULL;
python scripts/ops/block_regen.py --block 10 --academic-year 2026

# Option B: Full reset (dev only)
alembic downgrade base && alembic upgrade head
# Then regenerate all test data
```

**For future production:** If this were production, you'd need:
1. Migration script to map activity_type → activity_id
2. Explicit mapping table for edge cases
3. Audit log of changes

But that's not needed now.

**Acceptance criteria:**
- [ ] All creation code paths fixed (Step 1)
- [ ] Dev data regenerated with fixed code
- [ ] Zero NULL activity_id rows

---

## Recommendations Summary

| Constraint | Human Priority | CP-SAT Type | Penalty | Status |
|------------|---------------|-------------|---------|--------|
| activity_id presence | CRITICAL | Hard (DB level) | N/A | Step 1 |
| CV zero capacity | MEDIUM | Hard (definition) | N/A | Step 2 |
| Clinic preload (inpatient) | MEDIUM | Hard (locked) | N/A | Step 3 |
| Clinic solve (outpatient) | MEDIUM | Soft (mins) | 10-25 | Step 3 |
| Post-call PCAT/DO | HIGH | **Soft** | 35 | Step 4 |
| SM capacity units | LOW | Hard (physics) | N/A | Step 5 |

---

## AT Capacity Policy (Faculty)

**Hard AT capacity counts only these faculty assignments:**
- `AT`
- `PCAT`

**Soft AT penalty only (does NOT count toward hard capacity):**
- `PROC` (soft penalty)
- `VAS` (soft penalty)

**Do NOT count toward AT capacity (hard or soft):**
CV, SM, GME, DFM, LV, HOL, and all other activities.

---

## Validation Checklist (After All Steps)

```bash
# 1. No NULL activity_id
SELECT COUNT(*) FROM weekly_patterns WHERE activity_id IS NULL;  # Should be 0

# 2. CV has correct flags
SELECT counts_toward_fmc_capacity, counts_toward_at_capacity
FROM activities WHERE activity_type = 'CV';  # Both false

# 3. Post-call constraint is soft
grep -r "class PostCallAutoAssignmentConstraint" backend/app/  # Should extend SoftConstraint

# 4. SM capacity_units = 1
SELECT capacity_units FROM activities WHERE activity_type = 'SM';  # Should be 1

# 5. Block regeneration succeeds
python scripts/ops/block_regen.py --block 10 --academic-year 2026 --timeout 300
```

---

*Document updated with step-wise approach. Work sequentially unless Steps are explicitly coupled.*
