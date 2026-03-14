# Policy And GUI Migration Backlog

> Status: Working backlog
> Date: 2026-03-14
> Audience: Backend, frontend, and scheduler architecture work

## Purpose

This document answers one narrow question:

- What scheduler policy is still trapped in Python but should be human-tunable in Postgres and the admin UI?

It separates the remaining work into four buckets:

1. New table needed
2. Already in DB, wire solver
3. Already in DB, wire frontend
4. Leave in Python

This is not a replacement for `HARDCODED_TO_POSTGRES_ROADMAP.md`.
It is the concrete follow-up list after PRs `#1297` through `#1312`.

## Current Baseline

Already in good shape:

- Constraint enable/disable and soft weights:
  `constraint_configurations`
- Global ACGME settings:
  `application_settings`
- Primary duty policy:
  `primary_duty_configs`
- Rotation template preload classification:
  `rotation_templates.is_offsite`, `is_lec_exempt`, `is_continuity_exempt`,
  `is_saturday_off`, `preload_activity_code`

The remaining gaps are mostly:

- role-derived faculty policy still encoded as Python properties
- calendar policy still encoded as Python constants
- DB-backed fields not yet surfaced in the GUI
- a few DB-backed inputs still have Python fallback behavior outside the main path

## 1. New Table Needed

These items do not have a clean DB-backed source of truth yet.

### A. Faculty call preferences

Current state:

- `avoid_tuesday_call` and `prefer_wednesday_call` are Python properties derived
  from `faculty_role` in `backend/app/models/person.py`
- solver reads those properties in
  `backend/app/scheduling/constraints/call_equity.py`

Why this should move:

- These are human scheduling preferences and local policy.
- They should not require code edits or role hacks.

Recommended storage:

- Preferred: dedicated per-person scheduling preference fields or table
- Acceptable: add explicit columns to `people` if the scope is simple

Recommended fields:

- `avoid_tuesday_call: bool`
- `prefer_wednesday_call: bool`
- optional future fields:
  `avoid_sunday_call`, `max_calls_per_block`, `preferred_call_days`

### B. Call and FMIT calendar policy

Current state:

- Overnight call nights are hardcoded in
  `backend/app/scheduling/constraints/call_coverage.py`
- FMIT week boundaries and Sun-Thu logic are hardcoded in
  `backend/app/scheduling/constraints/fmit.py`
- similar logic is duplicated in
  `backend/app/services/call_assignment_service.py`

Why this should move:

- This is operational policy, not solver internals.
- If the service ever changes which nights are solver-covered, the current setup
  requires Python edits in multiple places.

Recommended storage:

- small scheduling-policy table or JSONB-backed settings row

Recommended fields:

- `overnight_call_weekdays`
- `fmit_week_start_weekday`
- `fmit_call_weekdays`
- optional effective-dating by academic year

### C. Editable curriculum slot definition, if local policy may change

Current state:

- `WednesdayAMInternOnly` is still tied to a hardcoded weekday/time rule in
  `backend/app/scheduling/constraints/temporal.py`
- `ResidentAcademicTime` still hardcodes Wednesday AM in
  `backend/app/scheduling/constraints/resident_weekly_clinic.py`

Why this may need schema:

- `resident_weekly_requirements` already stores `academics_required`
- `weekly_patterns` already stores protected slots
- but there is no generic DB field that says "this curriculum rule occurs on
  weekday X / half-day Y"

Recommended action:

- If Wednesday AM is truly fixed forever, leave it in Python
- If the program may change the protected slot, add DB-backed slot fields or
  express the rule entirely through `weekly_patterns`

## 2. Already In DB, Wire Solver

These items already have DB storage, but some solver or related runtime paths
 still fall back to Python assumptions.

### A. Year-scoped faculty clinic caps

Current state:

- `person_academic_years.clinic_min` and `clinic_max` already exist in
  `backend/app/models/person_academic_year.py`
- `people.clinic_min`, `clinic_max`, `at_min`, `at_max`, `gme_min`, `gme_max`
  also already exist in `backend/app/models/person.py`
- the main faculty role constraint still falls back to Python role defaults via
  `weekly_clinic_limit` and `block_clinic_limit`

Why this matters:

- The database already has richer per-person/per-year capacity fields.
- The solver should prefer explicit DB values over role-derived Python defaults.

Recommended action:

- Make solver precedence explicit:
  academic-year override > person override > role default
- stop treating role-derived properties as the primary source of truth

### B. Rotation template preload classification fallback removal

Current state:

- `rotation_templates` now stores preload classification flags
- `backend/app/services/preload/rotation_codes.py` uses them when a template is
  present
- but still falls back to Python constants from
  `backend/app/services/preload/constants.py`

Why this matters:

- The DB now has the intended truth source.
- Python set membership should be a migration fallback, not ongoing policy truth.

Recommended action:

- Keep aliases and normalization helpers in Python
- remove policy fallback for classification once templates are fully populated
- use DB template flags consistently in preload, export, and validation flows

### C. Curriculum/protected-slot truth should converge on DB-backed patterns

Current state:

- `weekly_patterns` and `resident_weekly_requirements` already exist
- solver/preload/export code still contains hardcoded Wednesday defaults in a
  few places

Examples:

- `backend/app/services/block_assignment_expansion_service.py`
- `backend/app/services/schedule_xml_exporter.py`

Recommended action:

- choose one prescriptive source of truth:
  `weekly_patterns` plus `resident_weekly_requirements`
- refactor preload/export/helper code to read those models rather than restating
  Wednesday rules in Python

## 3. Already In DB, Wire Frontend

These items already have storage and backend API support but are still not
fully editable in the admin UI.

### A. Primary duty configs

Backend status:

- model exists:
  `backend/app/models/primary_duty_config.py`
- CRUD API exists:
  `backend/app/api/routes/primary_duty_configs.py`

Remaining work:

- add admin page and forms in frontend
- list, create, edit, delete
- validate `available_days`, `clinic_min_per_week`, `clinic_max_per_week`

### B. Rotation template preload classification fields

Backend status:

- model fields exist in `backend/app/models/rotation_template.py`
- schema fields exist in `backend/app/schemas/rotation_template.py`
- rotation template API already exists

Remaining work:

- expose the following on the admin rotations UI:
  - `is_offsite`
  - `is_lec_exempt`
  - `is_continuity_exempt`
  - `is_saturday_off`
  - `preload_activity_code`

### C. Person clinic cap fields

Backend status:

- person-level clinic cap fields exist in `backend/app/models/person.py`
- person schemas expose `min_clinic_halfdays_per_week` and
  `max_clinic_halfdays_per_week` in `backend/app/schemas/person.py`

Remaining work:

- expose these in the admin people UI
- decide whether AY-scoped clinic caps also need an admin surface

### D. Existing rotation requirement/pattern editors

Backend status:

- `weekly_patterns` and `resident_weekly_requirements` already have models and APIs

Remaining work:

- confirm the frontend surfaces are sufficient for human control
- if not, add explicit editor flows instead of leaving admins dependent on
  fallback Python behavior

## 4. Leave In Python

These should stay code, not DB policy rows.

### A. Constraint implementations

- `add_to_cpsat()`
- `add_to_pulp()`
- validation logic
- penalty variable construction
- objective math

### B. Hard vs soft semantics

- whether a constraint is implemented as hard feasibility or soft penalty
- the exact mathematical encoding

DB can store:

- enabled state
- weight
- metadata

DB should not become the source of truth for:

- solver semantics
- CP-SAT structure
- feasibility logic

### C. Complex pattern algorithms

Examples:

- `get_kap_codes`
- `get_hilo_codes`
- `get_ldnf_codes`
- `get_nf_codes`
- NF-combined transition logic

These are procedural rules.
Do not move them into ad hoc DB rows unless the product intentionally builds a
pattern/rules engine.

### D. Normalization helpers and translation glue

Examples:

- rotation alias normalization in
  `backend/app/services/preload/constants.py`

This is code-level translation logic.
It is not a good admin-UI target unless there is a real operational need for
non-engineers to edit aliases.

## Current DB Data That Should Not Move Back To Python

Nothing major currently in DB should be migrated back to Python.

Keep these DB-backed:

- `constraint_configurations`
- `application_settings`
- `primary_duty_configs`
- rotation template preload flags
- person and academic-year capacity fields
- weekly patterns and resident weekly requirements

The correction is not "move DB policy back to code."
The correction is:

- keep policy and operational inputs in DB
- keep solver semantics in Python

## Recommended Execution Order

1. Frontend for `primary_duty_configs`
2. Frontend for rotation-template preload flags
3. Frontend for person clinic caps
4. Schema for explicit call preferences
5. Schema for call/FMIT calendar policy
6. Solver precedence cleanup for person/person-academic-year cap fields
7. Remove long-term preload/export fallback reliance on Python classification sets

## Definition Of Done

This backlog is done when:

- humans can edit all intended scheduling policy without touching Python
- solver reads DB-backed policy directly in the main runtime path
- export/preload/helper code uses the same DB-backed truth source
- no operator-facing policy depends on role-derived Python properties
- Python remains the only source of truth for solver semantics and math
