# Block 10 CP-SAT Regen + Activity Solver Report (2026-01-27)

## Summary
- **CP-SAT generation succeeded** for Block 10 (AY2026) with **617** solver assignments + **20** call nights.
- **Activity solver failed** with status **INFEASIBLE** after **0.78s**.
- **Outpatient slots to assign:** 872
- **Supervision sets:** required=15, providers=4 (no fallback)
- **Physical capacity constraints:** soft 6 / hard 8 applied to **40/40** time slots.
- **Many FM Clinic requirements were clamped** (min=3 down to available 1–2) — activity_id `24998...` = `fm_clinic`.

Block window: **2027-03-11 → 2027-04-07** (Block 10, AY2026).

## Changes Applied Before Run
- Normalized `rotation_type` for rotation templates to **inpatient/outpatient** (procedures → outpatient).
- Added **FMC capacity boolean** (`counts_toward_fmc_capacity`) on half-day assignments.
- FMC capacity now **assignment-level**, not rotation-level.
- **SM** counts as **1** per slot regardless of number of learners.
- Activity solver **uses FMC activity codes** for capacity and supervision demand.

## Command
```
python3.11 scripts/ops/block_regen.py --block 10 --academic-year 2026 --clear
```

## Console Highlights
```
... CP-SAT solver generated 617 rotation assignments and 20 call assignments
... Synced 40 PCAT/DO slots to match new call assignments
... Found 872 outpatient slots to assign
... Supervision activity sets: required=15, providers=4 (fallback_required=False, fallback_providers=False)
... Added 607 activity requirement constraints
... Added physical capacity constraints (soft 6, hard 8) for 40 of 40 time slots
... Activity solver status: INFEASIBLE (0.78s)
STATUS: partial
SUMMARY COUNTS:
  call_assignments: 20
  half_day_assignments: 1112
  hda_activity_do: 19
  hda_activity_pcat: 19
  hda_source_preload: 240
  hda_source_solver: 872
  pcat_do_next_day: 2
```

## Findings
- **Rotation-type normalization succeeded** (procedures now outpatient; 37 outpatient / 31 inpatient).
- **Activity solver infeasible** despite full FMC capacity constraints and supervision sets.
- **Clamped min requirements** are primarily for **FM Clinic** (min=3, available 1–2) — indicates weekly requirement config may exceed available outpatient slots for certain residents/templates.
- New outpatient procedure templates created activities on the fly (Botox/Procedure/Vasectomy/POCUS) with specialty requirements.

## Plan (Next Actions)
1. **Add activity-solver infeasibility diagnostics** (constraint attribution by slot/template/person).
2. **Audit FM Clinic requirements vs available slots** for Block 10 (where clamping occurs).
3. **Verify supervision coverage math** for FMC activities (AT demand vs 4 providers).
4. Re-run block regen after diagnostics to confirm root cause (capacity vs supervision vs requirements).

## Priority List (Block 10 Stabilization)
- **P0:** Activity solver infeasible — needs constraint-level diagnostics.
- **P1:** FM Clinic weekly mins frequently exceed availability (clamping); verify requirement data.
- **P2:** Supervision coverage capacity (required=15 vs providers=4) may still be binding.
