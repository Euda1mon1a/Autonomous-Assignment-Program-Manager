# Block 10 Schedule Generation: Edge Cases

**Date:** 2026-01-23
**Purpose:** Document all edge cases and failure scenarios for Block 10 generation
**Total Edge Cases:** 14 (8 primary + 6 edge-of-edge)

---

## Primary Edge Cases (8)

### EC-1: Activity Code Lookup Failure

**Scenario:** Activity code not found in database during expansion

**File:** `backend/app/services/block_assignment_expansion_service.py:315-347`

**Code Pattern:**
```python
activity = self._activity_cache.get(code)
if activity is None:
    logger.warning(f"Activity {code} not found")
    return None  # ← Silent failure
```

**Cascade:**
```
Activity not in database
  └─→ _get_activity() returns None
       └─→ HalfDayAssignment created with activity_id=NULL
            └─→ Export tries assignment.activity.code
                 └─→ AttributeError: 'NoneType' has no attribute 'code'
```

**Detection:**
```sql
SELECT COUNT(*) FROM half_day_assignments
WHERE activity_id IS NULL AND date >= '2026-03-12';
```

**Mitigation:** Pre-audit all 83 activity codes before generation.

---

### EC-2: Mid-Block Transition (Day 11)

**Scenario:** Resident changes rotation mid-block

**File:** `backend/app/services/block_assignment_expansion_service.py`

**Constant:** `MID_BLOCK_DAY = 11` (start of week 3; day index 11 of block)

**Sub-Cases:**

| Condition | Result |
|-----------|--------|
| `secondary_rotation_template_id` is NULL | First template used for all 28 days |
| `secondary_rotation_template` not loaded | AttributeError on access |
| 1-in-7 counter at transition | Counter does NOT reset at transition |

**Code Path:**
```python
# Simplified from expansion service
if current_day >= MID_BLOCK_DAY:
    template = block_assignment.secondary_rotation_template  # ← Can be None
    if template is None:
        template = block_assignment.rotation_template  # Fallback
```

**Risk:** 1-in-7 counter carries across rotation boundary, potential ACGME violation.

---

### EC-3: 1-in-7 Day-Off with Absences

**Scenario:** Absence HOLDS counter instead of resetting it

**File:** `backend/app/services/block_assignment_expansion_service.py:705-800`

**The "PAUSE" Interpretation:**
```
Day 1-6: Work (counter increments to 6)
Day 7: Absence (counter HOLDS at 6, NOT reset)
Day 8: Work (counter becomes 7) → VIOLATES 1-in-7!
```

**Code Evidence:**
```python
# From expansion service (paraphrased)
if is_absence:
    # Counter PAUSES, does not reset
    # This is intentional per code comments
    pass
elif is_day_off:
    counter = 0  # Reset only on actual day-off
else:
    counter += 1
```

**Why This Happens:** Code interprets absence as "not a work day" but also "not a rest day" - the counter freezes.

**Risk Level:** MEDIUM - Could cause ACGME 1-in-7 violation.

---

### EC-4: NULL Activity in WeeklyPattern

**Scenario:** WeeklyPattern has `activity_id = NULL`

**File:** `backend/app/models/weekly_pattern.py:104-110`

**Schema:**
```python
activity_id = Column(
    ForeignKey("activities.id", ondelete="RESTRICT"),
    nullable=True,  # ← Migration incomplete
    ...
)
```

**Cascade:**
```
WeeklyPattern.activity_id = NULL
  └─→ Expander reads NULL activity
       └─→ HalfDayAssignment.activity_id = NULL
            └─→ Export crashes on attribute access
```

**Detection:**
```sql
SELECT rotation_template_id, COUNT(*)
FROM weekly_patterns
WHERE activity_id IS NULL
GROUP BY rotation_template_id;
```

---

### EC-5: Intern Continuity (PGY-1 Wed AM)

**Scenario:** PGY-1 intern should have Clinic on Wednesday AM

**File:** `backend/app/services/block_assignment_expansion_service.py:395-428`

**Rules:**
- PGY-1 gets `C` (Clinic) on Wednesday AM
- Exempt rotations: NF, PNF, LDNF, TDY, HILO, KAPI-LD
- FMIT was **removed** from exempt list (recent change)

**Edge Cases:**

| Condition | Expected | Actual Risk |
|-----------|----------|-------------|
| `C` activity missing | Wed AM = C | Wed AM = NULL |
| Intern on NF | Wed AM = OFF | Correct (exempt) |
| Intern on FMIT | Wed AM = C | Was exempt, now should be C |

**Test Query:**
```sql
SELECT p.name, hda.date, a.code
FROM half_day_assignments hda
JOIN people p ON hda.person_id = p.id
LEFT JOIN activities a ON hda.activity_id = a.id
WHERE p.pgy_level = 1
  AND EXTRACT(DOW FROM hda.date) = 3  -- Wednesday
  AND hda.time_of_day = 'AM'
  AND hda.date >= '2026-03-12';
```

---

### EC-6: Last Wednesday of Block

**Scenario:** Last Wednesday has special rules

**File:** `backend/app/services/block_assignment_expansion_service.py`

**Rules:**
- AM = LEC (all residents, no exemptions)
- PM = ADV (all residents)

**Edge Cases:**

| Condition | Result |
|-----------|--------|
| `LEC` activity missing | AM slot NULL or wrong code |
| `ADV` activity missing | PM slot NULL or wrong code |
| Block ends on Wednesday | Off-by-one in date calculation |
| Resident exempt from Wed LEC | Last Wed rule overrides exemption |

**Block 10 Dates:**
- Start: 2026-03-12 (Thursday)
- End: 2026-04-08 (Wednesday) ← Last Wednesday IS end date
- Last Wednesday: 2026-04-08

---

### EC-7: Compound Rotations

**Scenario:** Rotation name indicates mid-block split

**File:** `backend/app/services/block_assignment_expansion_service.py:531-541`

**Known Patterns:**
- `NEURO-1ST-NF-2ND` (Neurology first half, Night Float second)
- `NF-1ST-ENDO-2ND` (Night Float first, Endocrinology second)
- `NEURO-NF` (special handling)

**Edge Case:** Rotation not in compound list → Pattern applies to all 28 days

**Detection:**
```sql
SELECT abbreviation FROM rotation_templates
WHERE abbreviation LIKE '%-%-%'
  AND abbreviation NOT IN ('NEURO-1ST-NF-2ND', 'NF-1ST-ENDO-2ND', 'NEURO-NF');
```

---

### EC-8: IntegrityError on Duplicate Preloads

**Scenario:** Duplicate preload creation triggers IntegrityError

**File:** `backend/app/services/sync_preload_service.py:655-660`

**Code:**
```python
try:
    self.session.flush()
except IntegrityError:  # ← Catches ALL integrity errors
    self.session.rollback()
    return False  # ← Silent failure
```

**Risk:** FK violation (not just duplicate) also silently fails.

**Sub-Cases:**
- Duplicate (person_id, date, time_of_day) → Silent skip (intended)
- Invalid activity_id FK → Silent skip (BUG)
- Invalid person_id FK → Silent skip (BUG)

---

## Edge Cases of Edge Cases (6)

### EC-9: Absence + 1-in-7 at Block Boundary

**Scenario:** Absence on Block 9's final Sunday affects Block 10's 1-in-7

**Timeline:**
```
Block 9 ends Wednesday 2026-03-11
Block 10 starts Thursday 2026-03-12

Block 9 Week 4:
  Thu-Fri-Sat: Work (counter = 3)
  Sun: ABSENCE (counter HOLDS at 3)
  Mon-Tue-Wed: Work (counter = 6)

Block 10 Week 1:
  Thu: Work (counter = 7) ← VIOLATION!
```

**Why:** 1-in-7 counter carries across block boundaries. Absence on Sunday didn't reset it.

**Risk Level:** HIGH for residents with absences near block boundaries.

---

### EC-10: FMIT + Call + Absence Triple Overlap

**Scenario:** Three preloads compete for same slot

**Timeline:**
```
Friday 2026-03-20 PM:
  - FMIT preload wants: FMIT
  - Call preload wants: CALL
  - Absence preload wants: LV-PM
```

**Resolution Order:** First preload created wins (race condition)

**Code:** `_create_preload()` checks if slot exists, updates if source priority allows.

**Actual Priority:**
```python
if existing.source in (TEMPLATE, SOLVER):
    # Overwrite allowed
elif existing.source in (PRELOAD, MANUAL):
    # Cannot overwrite - first preload wins
```

**Risk:** Order of `_load_absences()`, `_load_fmit_call()` matters.

---

### EC-11: Mid-Block Transition + Last Wednesday

**Scenario:** Transition day coincides with special Wednesday rule

**Timeline:**
```
Resident: NEURO first half, NF second half
Mid-block: Day 11 = Monday 2026-03-23

Last Wednesday: 2026-04-08
  - Resident is on NF (second half)
  - NF pattern: "no Wednesday LEC" (works nights)
  - Last Wednesday rule: "ALL residents get LEC"
```

**Resolution:** Last Wednesday rule wins (higher priority in code)

**Code Evidence:** Last Wednesday check happens AFTER rotation pattern applied.

---

### EC-12: NULL Template + NULL Activity Chain

**Scenario:** Cascading NULLs produce empty schedule

**Cascade:**
```
BlockAssignment.rotation_template_id = NULL (template was deleted)
  └─→ Cannot load weekly_patterns
       └─→ Cannot determine activity codes
            └─→ All 56 slots created with activity_id = NULL
                 └─→ Resident has 0 scheduled clinical hours
                      └─→ ACGME validator sees 0 hours (PASSES trivially!)
```

**Risk:** Empty schedule passes validation because 0 < 80 hours.

**Detection:**
```sql
SELECT p.name, COUNT(hda.id) as assignments,
       SUM(CASE WHEN hda.activity_id IS NULL THEN 1 ELSE 0 END) as null_activities
FROM people p
LEFT JOIN half_day_assignments hda ON p.id = hda.person_id
WHERE p.type = 'resident'
  AND hda.date >= '2026-03-12'
GROUP BY p.id, p.name
HAVING SUM(CASE WHEN hda.activity_id IS NULL THEN 1 ELSE 0 END) > 0;
```

---

### EC-13: Solver Timeout + Greedy Fallback + PCAT Sync

**Scenario:** CP-SAT timeout triggers fallback chain

**Timeline:**
```
1. CP-SAT solver runs for 60s
2. Timeout reached, no optimal solution
3. Falls back to greedy algorithm
4. Greedy produces different call assignments
5. PCAT/DO sync uses greedy call result
6. Validation runs on suboptimal schedule
```

**Risk:** Schedule is valid but not optimized for call equity.

**Code Path:**
```python
# In engine.py (paraphrased)
result = solver.solve(timeout=60)
if not result.success and solver != 'greedy':
    result = greedy_solver.solve()  # Fallback
```

**Mitigation:** Use `timeout_seconds=120` to give CP-SAT more time.

---

### EC-14: Export After Partial Generation Failure

**Scenario:** Generation fails mid-process, partial data committed

**Timeline:**
```
Step 1-4: Preloads + expansion complete (~800 assignments written)
Step 5: Solver fails (timeout, infeasible)
Step 6: Exception raised
Step 7: Transaction SHOULD rollback, but...
Step 8: Some assignments already flushed
Step 9: User exports schedule
Step 10: Export shows incomplete schedule
```

**Risk:** No visible atomic transaction wrapper around full generation.

**Detection:** Check for orphaned half_day_assignments with stale run_id.

---

## Test Scenarios

### Test 1: Activity Code Coverage
```python
def test_all_critical_activities_exist():
    critical = ['LEC-PM', 'LEC', 'ADV', 'C', 'C-I',
                'CALL', 'PCAT', 'DO', 'FMIT', 'NF', 'IM', 'PedW', 'aSM',
                'W', 'LV', 'OFF', 'HOL']
    codes = {row[0] for row in db.query(Activity.code).all()}
    abbrevs = {row[0] for row in db.query(Activity.display_abbreviation).all()}
    existing = codes | abbrevs
    for code in critical:
        assert code in existing, f"Missing critical activity: {code}"
```

### Test 2: 1-in-7 with Absence
```python
def test_1in7_absence_pauses_counter():
    # Create 6 work days, 1 absence, 1 work day
    # Expect pause semantics (no forced OFF on day 8)
    # If policy changes, update this test and docs
```

### Test 3: Last Wednesday Override
```python
def test_last_wednesday_overrides_exemptions():
    # NF resident on last Wednesday
    # Should have LEC (AM), ADV (PM) despite NF exemption
```

### Test 4: NULL Activity Detection
```python
def test_no_null_activities_after_generation():
    null_count = db.query(HalfDayAssignment).filter(
        HalfDayAssignment.activity_id == None,
        HalfDayAssignment.date >= '2026-03-12'
    ).count()
    assert null_count == 0, f"Found {null_count} NULL activity assignments"
```

---

## Resolution Priority

| Edge Case | Likelihood | Impact | Priority |
|-----------|------------|--------|----------|
| EC-1 (Activity lookup) | HIGH | CRITICAL | P0 |
| EC-4 (NULL WeeklyPattern) | MEDIUM | HIGH | P1 |
| EC-3 (1-in-7 absence) | MEDIUM | HIGH | P1 |
| EC-12 (NULL chain) | LOW | CRITICAL | P1 |
| EC-8 (IntegrityError) | MEDIUM | MEDIUM | P2 |
| EC-5 (Intern continuity) | MEDIUM | MEDIUM | P2 |
| EC-6 (Last Wednesday) | LOW | MEDIUM | P2 |
| EC-2 (Mid-block) | LOW | MEDIUM | P3 |
| EC-7 (Compound) | LOW | LOW | P3 |
| EC-9 (Block boundary) | LOW | HIGH | P3 |
| EC-10 (Triple overlap) | LOW | LOW | P4 |
| EC-11 (Mid+LastWed) | LOW | LOW | P4 |
| EC-13 (Solver timeout) | LOW | LOW | P4 |
| EC-14 (Partial commit) | LOW | MEDIUM | P4 |

---

## Related Documents

- [BLOCK10_GENERATION_GAPS.md](BLOCK10_GENERATION_GAPS.md) - Gap analysis
- [BLOCK10_999_SUCCESS_PLAN.md](BLOCK10_999_SUCCESS_PLAN.md) - 99.9% success plan
- [session-133-schedule-generation-status.md](../scratchpad/session-133-schedule-generation-status.md) - Session notes
- [HALF_DAY_ASSIGNMENT_MODEL.md](../architecture/HALF_DAY_ASSIGNMENT_MODEL.md) - Data model
