# Block 10 CP-SAT Regen + Activity Solver Report (2026-01-27)

## Latest Run (Step 5: capacity_units backfill + regen)
**Block window:** **2026-03-12 → 2026-04-08** (Block 10, **AY2025**).

### Summary
- **CP-SAT generation succeeded** with **589** solver assignments + **20** call nights.
- **Activity solver succeeded** (OPTIMAL, ~2.56s, **457** activities).
- **Physical capacity constraints applied** (soft 6 / hard 8) across **40/40** slots.
- **PCAT/DO integrity check passed** (20 calls verified; **32** PCAT/DO slots synced).
- **AT coverage shortfall total:** 0 (CP-SAT run).
- **Activity min shortfall total:** 1 (soft penalty applied).
- **Note:** 144 solver assignments skipped due to immutable existing assignments.
- **Note:** Several templates had no activity requirements; solver fell back to all assignable activities.

### Command
```
DATABASE_URL=postgresql://scheduler:local_dev_password@localhost:5432/residency_scheduler \
  backend/venv/bin/python scripts/ops/block_regen.py --block 10 --academic-year 2025 --timeout 300 --clear
```

### Console Highlights
```
... CP-SAT solver generated 589 rotation assignments and 20 call assignments
... Synced 32 PCAT/DO slots to match new call assignments
... Found 457 outpatient slots to assign
... Added physical capacity constraints (soft 6, hard 8) for 40 of 40 time slots
... Activity solver status: OPTIMAL (2.56s)
... Activity min shortfall total: 1
STATUS: partial
SUMMARY COUNTS:
  call_assignments: 20
  half_day_assignments: 1296
  hda_activity_at: 36
  hda_activity_do: 15
  hda_activity_pcat: 15
  hda_source_preload: 839
  hda_source_solver: 457
  pcat_do_next_day: 2
```

### Notes
- Inpatient rotations now preload clinic **from weekly patterns only** (C/C‑I/C‑N).
- **CV is proactive** (not fallback): faculty/PGY‑3 FMC clinic slots can choose CV
  with a **30% weekly target** (group‑level, includes locked preloads).
- **CV still requires AT/PCAT coverage** (supervision demand decoupled from physical capacity).
- **Clinic floor relaxed for CV‑eligible PGY‑2/3** (PGY‑1 still requires in‑person C).
- CV usage in FMC clinic (faculty+PGY‑3): **17** assignments.
- Weekly CV ratios (faculty+PGY‑3, FMC clinic only): **35.71% / 30.77% / 25.00% / 35.71%**.
- Daily spread improved (soft), but some weekdays still under target due to
  preloaded C + limited flexible slots (e.g., Week 3 has a 0% day).
- Peak FMC physical capacity remains **8** at **2026‑04‑01 AM**.

### MCP Validation (Local-Only, re-run)
- **validate_schedule_tool:** 10 issues (2 critical 80‑hour violations; 8 consecutive‑days warnings).
- **detect_conflicts_tool:** 26 conflicts (2 work‑hour, 8 rest‑period, 16 supervision gaps).
- **generate_block_quality_report_tool:** **ok** (overall **PASS (1 GAP)**; post‑call PCAT/DO **GAP**).
- **No new 404/500s** on MCP tool calls.
- Full local outputs saved in:
  - `docs/analysis/block10_mcp_validation_human_20260127.md`
  - `docs/analysis/block10_mcp_validation_llm_20260127.md`

---

## Previous Run (Step 4b: post-call soft + CV target + daily spread penalty)
**Block window:** **2026-03-12 → 2026-04-08** (Block 10, **AY2025**).

### Summary
- **CP-SAT generation succeeded** with **589** solver assignments + **20** call nights.
- **Activity solver succeeded** (OPTIMAL, ~2.45s, 455 activities).
- **Physical capacity constraints applied** (soft 6 / hard 8) across **40/40** slots.
- **CV target enforced** per week across **faculty + PGY‑3** in FMC clinic.
- **CV daily spread penalty enabled** (soft, weight=6) to distribute CV across weekdays.
- **PCAT/DO integrity check passed** (20 calls verified; **34** PCAT/DO slots synced).
- **AT coverage shortfall total:** 0 (CP-SAT run).
- **Activity min shortfall total:** 1 (soft penalty applied).

### Command
```
DATABASE_URL=postgresql://scheduler:<local_db_password>@localhost:5432/residency_scheduler \
  python3.11 scripts/ops/block_regen.py --block 10 --academic-year 2025 --timeout 300 --clear
```

### Console Highlights
```
... CP-SAT solver generated 589 rotation assignments and 20 call assignments
... Synced 34 PCAT/DO slots to match new call assignments
... Found 455 outpatient slots to assign
... Added physical capacity constraints (soft 6, hard 8) for 40 of 40 time slots
... Activity solver status: OPTIMAL (2.45s)
... Activity min shortfall total: 1
STATUS: partial
SUMMARY COUNTS:
  call_assignments: 20
  half_day_assignments: 1296
  hda_activity_at: 29
  hda_activity_do: 16
  hda_activity_pcat: 16
  hda_source_preload: 841
  hda_source_solver: 455
  pcat_do_next_day: 2
```

### Notes
- Inpatient rotations now preload clinic **from weekly patterns only** (C/C‑I/C‑N).
- **CV is proactive** (not fallback): faculty/PGY‑3 FMC clinic slots can choose CV
  with a **30% weekly target** (group‑level, includes locked preloads).
- **CV still requires AT/PCAT coverage** (supervision demand decoupled from physical capacity).
- **Clinic floor relaxed for CV‑eligible PGY‑2/3** (PGY‑1 still requires in‑person C).
- CV usage in FMC clinic (faculty+PGY‑3): **17** assignments.
- Weekly CV ratios (faculty+PGY‑3, FMC clinic only): **35.71% / 30.77% / 25.00% / 35.71%**.
- Daily spread improved (soft), but some weekdays still under target due to
  preloaded C + limited flexible slots (e.g., Week 3 has a 0% day).
- Peak FMC physical capacity remains **8** at **2026‑04‑01 AM**.

### MCP Validation (Local-Only, re-run)
- **validate_schedule_tool:** 10 issues (2 critical 80‑hour violations; 8 consecutive‑days warnings).
- **detect_conflicts_tool:** 26 conflicts (2 work‑hour, 8 rest‑period, 16 supervision gaps).
- **generate_block_quality_report_tool:** **ok** (overall **PASS (1 GAP)**; post‑call PCAT/DO **GAP**).
- **No new 404/500s** on MCP tool calls.
- Full local outputs saved in:
  - `docs/analysis/block10_mcp_validation_human_20260127.md`
  - `docs/analysis/block10_mcp_validation_llm_20260127.md`

---

## Previous Run (Step 2b: intern continuity outpatient-only + CV excluded)
**Block window:** **2026-03-12 → 2026-04-08** (Block 10, **AY2025**).

### Summary
- **CP-SAT generation succeeded** with **584** solver assignments + **20** call nights.
- **Activity solver failed**: physical capacity infeasible (min clinic demand > hard 8).
- **Snapshot written:** `/tmp/activity_failure_capacity_block10_ay2025_20260127T150159Z.json`
- **PCAT/DO integrity check passed** (20 calls verified).
- **Null activity_id rows:** 0 in `weekly_patterns`, 0 in `half_day_assignments`.

### Console Highlights
```
... CP-SAT solver generated 584 rotation assignments and 20 call assignments
... Synced 36 PCAT/DO slots to match new call assignments
... Found 453 outpatient slots to assign
... Physical capacity infeasible: 1 of 40 slots have minimum clinic demand above hard 8. Examples: 2026-04-01 AM min=10
... Wrote activity failure snapshot to /tmp/activity_failure_capacity_block10_ay2025_20260127T150159Z.json
```

### Notes
- Strict preload activity resolution surfaced missing **FMC → fm_clinic** mapping in sync preloads; fixed by adding `_ROTATION_TO_ACTIVITY` mapping.
- Preload activity codes now fail fast on unknown codes (prevents silent NULL activity_id rows).

---

## Prior Run (pre-Step 1)
**Block window:** **2027-03-11 → 2027-04-07** (Block 10, AY2026).

### Summary
- **CP-SAT generation succeeded** for Block 10 (AY2026) with **617** solver assignments + **20** call nights.
- **Activity solver succeeded** with status **OPTIMAL** after **~0.24s**.
- **Outpatient slots to assign:** 872
- **Supervision sets:** required=15, providers=4 (no fallback)
- **Physical capacity constraints:** soft 6 / hard 8 applied to **40/40** time slots (template‑aware FMC only).
- **Export succeeded** via canonical pipeline to `/tmp/block10_export.xlsx`.

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
