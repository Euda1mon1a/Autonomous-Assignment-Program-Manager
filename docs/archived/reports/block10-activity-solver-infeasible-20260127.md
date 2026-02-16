# Block 10 Activity Solver Infeasible (2026-01-27)

## Run summary
- Command: `python3.11 scripts/ops/block_regen.py --block 10 --academic-year 2026 --clear --timeout 300`
- Result: CP-SAT succeeded; activity solver INFEASIBLE
- Block range: 2027-03-11 to 2027-04-07
- Snapshot written: `/tmp/activity_failure_solve_block10_ay2026_20260127T024043Z.json`
- Follow-up (capacity disabled): `DISABLE_PHYSICAL_CAPACITY=1 ...` → OPTIMAL (2026-01-26 17:44)
- Follow-up (capacity on + fix): default run → OPTIMAL (2026-01-26 17:54)

## Snapshot highlights
- Slots: 872 total (510 resident, 362 faculty)
- Templates: 37 outpatient
- Activity requirements: 249
- Activities: 165 total, 119 assignable
- Clamped min requirements: 275 total (max shortage 2)
- Missing outpatient templates: 0

## Why it failed (first-order diagnosis)
The activity solver enforces per-week minimums for each activity requirement.
For most outpatient rotations in Block 10, the number of available weekly
slots per resident is far smaller than the sum of per-week minimums.

Empirical check after the run:
- Outpatient person-template-week combos: 402
- Cases where sum(min_halfdays) > available slots: 387
- Worst cases: 1 slot/week with min_sum=8 (overage 7)

This is a structural infeasibility, not a search failure. The solver originally
clamped each activity’s minimum individually when it exceeded available slots, but
did not relax the *sum* of minima across multiple activities. That has now been
changed to **soft mins with penalties** plus a **hard clinic floor of 1**. Even
with that change, the model remained infeasible, which pointed to another hard
constraint. That blocker was confirmed as **physical capacity**.

## Root cause (confirmed)
- Physical capacity counted **every `fm_clinic`/`C` assignment** by activity code,
  but `fm_clinic` is used as a generic outpatient activity even when the rotation
  is **not** in the Family Medicine Clinic (FMC).
- That made per‑slot capacity exceed 8 in many slots, making the model infeasible.

## Fix applied
- Capacity now counts clinic activities **only when the rotation template is FMC
  continuity** (template display/abbrev in `C`, `C-AM`, `C-PM`, `CONT`, `CONTINUITY`).
- `PROC`/`VAS`/`V1-3`/`SM` always count toward capacity (SM still counts once/slot).
- Activity solver now writes `counts_toward_fmc_capacity` per assignment using this
  template‑aware rule.
- Debug toggles added:
  - `DISABLE_PHYSICAL_CAPACITY=1`
  - `DISABLE_CLINIC_FLOOR=1`

## Results after fix
- `DISABLE_PHYSICAL_CAPACITY=1` run: **OPTIMAL** (2026‑01‑26 17:44).
- Capacity enabled with the fix: **OPTIMAL** (2026‑01‑26 17:54).
- No failure snapshot generated on these runs.

## Failure snapshot location
Activity solver failures now write a PII-free snapshot to `/tmp` (or
`$SCHEDULE_FAILURE_SNAPSHOT_DIR`) for every failure stage:
- requirements missing
- no activities / no assignable activities
- solve infeasible

These snapshots are intended for fast root-cause analysis of infeasibility.
