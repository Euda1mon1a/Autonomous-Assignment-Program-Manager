# Block 10 CP-SAT Regen + Activity Solver Report (2026-01-27)

## Summary
- **CP-SAT generation succeeded** for Block 10 (AY2026) with **617** solver assignments + **20** call nights.
- **Activity solver succeeded** with status **OPTIMAL** after **~0.24s**.
- **Outpatient slots to assign:** 872
- **Supervision sets:** required=15, providers=4 (no fallback)
- **Physical capacity constraints:** soft 6 / hard 8 applied to **40/40** time slots (template‑aware FMC only).
- **Export succeeded** via canonical pipeline to `/tmp/block10_export.xlsx`.

Block window: **2027-03-11 → 2027-04-07** (Block 10, AY2026).

## Changes Applied Before Run
- Normalized `rotation_type` for rotation templates to **inpatient/outpatient** (procedures → outpatient).
- Added **FMC capacity boolean** (`counts_toward_fmc_capacity`) on half-day assignments.
- FMC capacity now **assignment-level** (counts only FMC continuity templates).
- **SM** counts as **1** per slot regardless of number of learners.
- Capacity counting now **template‑aware**:
  - `C`/`fm_clinic` count **only** for FMC continuity templates (`C/CONT`).
  - `PROC`/`VAS`/`V1-3`/`SM` always count.
  - `CV` does **not** count.
- Draft publishes now set `counts_toward_fmc_capacity` for manual edits.

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
... Activity solver status: OPTIMAL (0.24s)
... Activity solver updated 872 slots
... Activity min shortfall total: 0
... AT coverage shortfall total: 0
STATUS: partial
SUMMARY COUNTS:
  call_assignments: 20
  half_day_assignments: 1112
  hda_activity_at: 76
  hda_activity_do: 19
  hda_activity_pcat: 19
  hda_source_preload: 240
  hda_source_solver: 872
  pcat_do_next_day: 2
```

## Findings
- **Rotation-type normalization succeeded** (procedures now outpatient; 37 outpatient / 31 inpatient).
- **Activity solver now feasible** once FMC capacity uses assignment‑level flags.
- **Capacity check with assignment flags:** max FMC slot count **4** (no slots > 8).
- New outpatient procedure templates created activities on the fly (Botox/Procedure/Vasectomy/POCUS) with specialty requirements.

## Plan (Next Actions)
1. **Backfill capacity flags** for existing assignments (optional, dev only).
2. **Audit activity codes** for PROC/VAS variants to reduce reliance on display abbreviations.

## Priority List (Block 10 Stabilization)
- **P0:** Backfill/update existing assignments’ capacity flags (dev safety).
- **P1:** Normalize PROC/VAS activity codes (reduce display‑based matching).
