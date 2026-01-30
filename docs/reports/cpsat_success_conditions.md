# CP-SAT Success Conditions (Baseline)

Date: 2026-01-27
Scope: Local dev pipeline (CP-SAT activity solver + export)

This document captures the **known-good conditions** under which CP‑SAT successfully generated Block 10 schedules. Record this **before** any structural fixes so we can re‑establish a baseline after changes.

## Baseline Block Context
- Academic year: **2025–2026**
- Block 10 dates: **2026‑03‑12 → 2026‑04‑08**

## Data Integrity Preconditions
- **No NULL activity_id** in core schedule tables used by MCP/exports:
  - `half_day_assignments.activity_id` (for the target date range)
  - `weekly_patterns.activity_id` (rotation template grid)
  - `faculty_weekly_overrides.activity_id` uses explicit `OFF` instead of NULL
- Activities required for CP‑SAT and capacity logic exist in `activities` table:
  - Clinic/continuity: `C` (fm_clinic), `C‑I`
  - Capacity-counted: `V1`, `V2`, `V3`, `PROC`, `VAS`, `SM`
  - Non‑physical (capacity_units=0): admin/educ/time_off + explicit codes like
    `CV`, `AT`, `PCAT`, `DO`, `GME`, `DFM`, `LEC`, `ADV`
  - **CV still requires AT/PCAT supervision coverage**

## Capacity Semantics (Assignment-Level)
- **Physical capacity is assignment-based, not rotation-based.**
- `counts_toward_fmc_capacity` is the primary source of truth for room capacity;
  `activities.capacity_units` refines the count when capacity applies.
- FMC continuity **`C`** only counts **when the rotation template is FMC continuity** (template abbreviation `C/CONT`).
- `CV` never counts toward physical capacity.
- `CV` **does** count toward supervision demand (AT/PCAT ratios).
- `PROC`/`VAS` count toward physical capacity and **add +1 AT supervision demand**
  (soft via AT shortfall; hard AT capacity uses `AT` + `PCAT` only).
- **Clinic floor** (hard min 1) applies **only when CV is not allowed**
  (PGY‑1 or non‑FMC templates). CV‑eligible PGY‑2/3 can satisfy clinic weeks
  with CV if capacity binds.
- `SM` counts **once per slot**, regardless of number of learners.
- `activities.capacity_units` defaults to **1** for physical activities; non‑physical
  activities (e.g., CV/AT/PCAT/DO/LEC/OFF) are set to **0**. SM still counts once per slot.

## Solver Constraints (Current Baseline)
Hard constraints:
- One assignment per person per slot.
- Locked/preloaded slots are preserved.
- Physical capacity **hard cap = 8**.
- Clinic floor **hard min = 1**.

Soft constraints (penalized, not enforced):
- Physical capacity soft target = **6** (overages allowed with penalty).
- AT/SM requirements (shortfalls penalized, not infeasible).
- Activity min/max requirements (softened).

## Source Priority (Half-Day Assignments)
- `preload` > `manual` > `solver` > `template`
- Solver never overwrites `preload` or `manual` slots.
 - Placeholder solver slots use `OFF` (no NULL activity_id).

## Known-Good Run Indicators
- Activity solver returns **OPTIMAL** (or **FEASIBLE** when shortfalls are accepted).
- Exports (CSV/XLSX) complete without NULL activity_id warnings.
- MCP validation works against date range without tool errors.

## Latest Run Notes (2026-01-27)
- CP-SAT + activity solver complete for Block 10 (2026-03-12 → 2026-04-08).
- Physical capacity constraint **hard 8 / soft 6** enforced without infeasibility.
- Time-off activities **must not** count toward capacity:
  - Ensure `half_day_assignments.counts_toward_fmc_capacity = false` for
    `activities.activity_category = 'time_off'`.
  - SyncPreloadService now refreshes the capacity flag for preloads to prevent
    stale values.
- Intern continuity (PGY1 Wed AM) is applied **only for outpatient rotations**
  in both sync + async preload services; inpatient rotations (FMIT/NF/etc.)
  are handled exclusively via inpatient preloads.
- **CV is proactive** for faculty + PGY‑3 in FMC clinic with a **30% weekly target**
  (group‑level, **includes locked/preloaded C/CV**). It is **not** a fallback
  for failed C slots.
- **Post‑call PCAT/DO** is a **soft** constraint with LV/HOL/blocking‑absence exemptions.
- Post-call PCAT/DO is enforced via call assignments; call may proceed if the
  next-day slot is locked (yields PCAT/DO gaps in reports).

## Known Gaps After Latest Run
- **CV ratio below 30%** in some weeks due to preloaded C slots; solver hits
  30% on solver slots but cannot move locked C without policy change.
- Post-call PCAT/DO gap reported (locked-slot exceptions).
- **Resolved (2026-01-30):** 1-in-7/rest warnings cleared after time-off templates
  are preloaded into solver context (validated clean for 2026-03-12 → 2026-04-08).

## Notes
- Any schema/code changes affecting `weekly_patterns.activity_id` or activity resolution must preserve the above invariants before re‑running CP‑SAT.
