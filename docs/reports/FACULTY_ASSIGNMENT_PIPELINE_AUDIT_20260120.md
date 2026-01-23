# Faculty Assignment Pipeline Audit (Block 10)

> Date: 2026-01-20
> Scope: Block 10 (AY 2025-2026) faculty scheduling pipeline and weekly assignment parameters
> Method: Read-only database inspection + code path review

---

## Executive Summary

Block 10 faculty scheduling is split across multiple tables and pipelines with no single source of truth. The half-day pipeline only contains preloads, while the legacy assignments table has partial faculty coverage. Weekly limits and template parameters exist but are not enforced in the solver. This creates inconsistent faculty coverage in UI and exports.

---

## Current Data Snapshot (Block 10)

### People and Coverage
- Faculty in `people`: 14 total
- Faculty in legacy `assignments` (Block 10 date range): 12 faculty, 264 rows (22 per faculty)
- Faculty missing from legacy `assignments`: Anne Lamoureux, Kyle Samblanet

### Half-Day Assignments
- `half_day_assignments` (Block 10 date range): only `source=preload`
- Counts: faculty=162, resident=540
- No `solver` or `template` sources present

### Preloads
- `inpatient_preloads` within Block 10 window: 19 rows
  - FMIT faculty: 5 rows
  - Other resident preloads: NF, PedW, PedNF, HILO, IM, KAP, LDNF, FMC

---

## Where Weekly Parameters Live

### Per-Faculty Weekly Limits (Not Enforced)
`people.min_clinic_halfdays_per_week` and `people.max_clinic_halfdays_per_week` exist but are not referenced in the scheduling code. Actual enforcement is role-based via `weekly_clinic_limit`.

Examples of inconsistent data:
- Anne Lamoureux (adjunct): min=2, max=2 but role limit is 0
- Brian Dahl (oic): min=0, max=0 but role limit is 2
- Bridget Colgan (core): min=0, max=0 but role limit is 4
- Kyle Samblanet (adjunct): max=4 but role limit is 0

### Faculty Weekly Templates
`faculty_weekly_templates` defines a 7x2 default pattern per faculty.
- 10 faculty have 10 slots (weekday-only patterns)
- 4 faculty have 0 slots (no template data)
- All templates use week_number NULL (no week-specific patterns)
- Activity distribution: at=52, gme=27, fm_clinic=16, sm_clinic=5

### Faculty Weekly Overrides
`faculty_weekly_overrides` is effectively empty (only one faculty has overrides).

### Permissions and Preferences
- `faculty_activity_permissions` is role-based (not person-based), 32 rows
- `faculty_preferences` is empty

---

## Pipeline Breakdown (Where It Fails)

### 1. Source of Truth
- Residents use `block_assignments` (1 per resident per block)
- Faculty have no equivalent block-level source

### 2. Expansion to Daily Slots
- `expand_block_assignments=True` populates `half_day_assignments` for residents
  - Only preload rows exist for Block 10
- Faculty expansion exists (`FacultyAssignmentExpansionService`) but is not wired
  - It fills legacy `assignments`, not `half_day_assignments`

### 3. Activity Solver (CP-SAT)
- Solver only assigns activities to `half_day_assignments` when base slots exist
- No faculty half-day slots exist beyond preloads, so faculty activity assignment never runs

### 4. UI and Export
- UI uses `assignments` with half-day fallback
- Export uses `block_assignments` (residents) + `assignments` (faculty)
- Result: inconsistent schedules between UI, export, and half-day pipeline

---

## Root Causes

1. Faculty expansion is not connected to the half-day pipeline.
2. Weekly min/max clinic limits are stored but never applied.
3. Faculty templates are incomplete (4 faculty missing) and not expanded into daily slots.
4. Dual-source schedule tables (`assignments` vs `half_day_assignments`) are both in use.

---

## Fixes Required (Ordered)

### P0
1. Decide the canonical schedule table for faculty (prefer `half_day_assignments`).
2. Wire faculty expansion into the half-day pipeline (new service or extend existing).
3. Ensure faculty slots are generated for all 56 half-days per block before CP-SAT.

### P1
1. Enforce `min_clinic_halfdays_per_week` and `max_clinic_halfdays_per_week` in constraints.
2. Normalize faculty min/max values to match role-based limits (or remove if unused).
3. Populate weekly templates for all faculty or define default template rules.

### P2
1. Decide how `faculty_preferences` should be populated and applied.
2. Align export to the canonical schedule table (avoid mixed sources).

---

## Verification Queries (Read-Only)

```sql
-- Faculty coverage in legacy assignments
SELECT p.name, COUNT(*) AS assignments
FROM assignments a
JOIN blocks b ON b.id = a.block_id
JOIN people p ON p.id = a.person_id
WHERE b.date BETWEEN '2026-03-12' AND '2026-04-08'
  AND p.type = 'faculty'
GROUP BY p.name
ORDER BY assignments, p.name;

-- Half-day assignments by source
SELECT p.type, hda.source, COUNT(*) AS count
FROM half_day_assignments hda
JOIN people p ON p.id = hda.person_id
WHERE hda.date BETWEEN '2026-03-12' AND '2026-04-08'
GROUP BY p.type, hda.source
ORDER BY p.type, hda.source;

-- Faculty weekly templates presence
SELECT p.name, COUNT(fwt.id) AS template_slots
FROM people p
LEFT JOIN faculty_weekly_templates fwt ON fwt.person_id = p.id
WHERE p.type = 'faculty'
GROUP BY p.name
ORDER BY template_slots, p.name;
```

---

## Related Code

- `backend/app/models/person.py` (weekly limits fields)
- `backend/app/scheduling/constraints/faculty_role.py` (role-based limits)
- `backend/app/models/faculty_weekly_template.py` (default weekly patterns)
- `backend/app/services/faculty_assignment_expansion_service.py` (legacy assignments filler)
- `backend/app/scheduling/engine.py` (half-day mode skips faculty assignment)
