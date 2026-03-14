# AI Policy Storage Boundary

This document is for coding agents and developers working on scheduler policy.

Its purpose is to prevent one recurring mistake:

- putting human-editable policy in Python
- then trying to manage that policy through a GUI

## Rule Zero

Do not build a GUI for Python constants.

If a human should edit it without a deploy, store it in Postgres and have Python read it.

## Mandatory Boundary

### Store In Postgres

Store these in DB tables plus UI/API:

- constraint enable flags
- soft weights
- role caps
- clinic min or max targets
- day-of-week availability
- call preferences
- preload and protected-slot facts
- academic-year scoped policy
- effective-dated operational rules

### Keep In Python

Keep these in code:

- constraint implementations
- CP-SAT variable creation
- objective math
- penalty math
- validation algorithms
- translation from DB records into scheduling context

## Repo-Specific Hot Spots

These areas are known split-source problems and should not gain more code-side policy.

### Primary Duty Policy

Current source:

- `backend/app/scheduling/constraints/primary_duty.py`

Problem:

- clinic min or max and weekday availability are loaded from Airtable-export JSON

Rule:

- do not add more policy fields here unless they are moving toward DB-backed storage

### Role Defaults And Preferences

Current source:

- `backend/app/models/person.py`

Problem:

- clinic limits and call preferences are computed from `faculty_role` in Python properties

Rule:

- do not add new role-policy behavior to model properties if humans may override it

### Application Settings Drift

Current source:

- `backend/app/models/settings.py`
- `backend/app/scheduling/constraints/acgme.py`

Problem:

- settings exist in DB, but the solver still hardcodes the same values

Rule:

- if a setting already exists in DB, wire the solver to it instead of duplicating a Python constant

### Call And FMIT Calendar Policy

Current source:

- `backend/app/scheduling/constraints/call_coverage.py`
- `backend/app/scheduling/constraints/fmit.py`
- `backend/app/services/call_assignment_service.py`

Problem:

- Sun-Thu call days and Fri-Thu FMIT week logic are repeated in code

Rule:

- do not spread more calendar policy constants across files

### Fixed Wednesday Rules

Current source:

- `backend/app/scheduling/constraints/temporal.py`
- `backend/app/scheduling/constraints/resident_weekly_clinic.py`

Problem:

- curriculum slot rules are hardcoded by weekday checks

Rule:

- if admins may change the slot, move it to DB-backed patterns or requirements

## When Adding A New Policy Field

Use this workflow:

1. Decide whether a human should edit it without a deploy.
2. If yes, add DB storage first.
3. Add API and UI with validation.
4. Load the value into scheduling context.
5. Use the loaded value in solver or validator code.
6. Add an end-to-end test proving the DB value changes behavior.

## When NOT To Add A New DB Field

Do not create DB config for:

- CP-SAT variable names
- solver-internal helper thresholds that are not policy
- implementation details of objective construction
- free-form algorithm behavior that must remain code-reviewed

## Anti-Patterns

Do not do these:

- hardcode a human policy default in a model property
- add a GUI toggle that does not change solver behavior
- keep the same policy in both DB and Python
- mark a field as configurable but never read it in the engine
- solve "admin wants to edit this" by introducing more branchy Python fallbacks

## Required Tests

For any human-editable scheduler policy:

- one API or DB update test
- one engine or validator integration test
- one regression test proving old hardcoded behavior is gone

## Short Decision Test

Ask:

- Should an admin change this in the next academic year without a deploy?

If yes:

- it belongs in Postgres

If no:

- it may stay in Python

When in doubt, prefer DB-backed policy plus Python enforcement.
