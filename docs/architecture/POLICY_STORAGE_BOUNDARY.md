# Policy Storage Boundary

> Status: Draft working guidance
> Audience: Humans designing scheduler policy, admin UI, and solver configuration

## Purpose

This document defines the boundary between:

- policy and operational data that humans should edit in Postgres via UI/API
- solver and validation code that should remain in Python

The goal is to stop creating "GUI for Python" and to keep a single source of truth for scheduler behavior.

## Executive Summary

If a chief, coordinator, or admin should be able to change a value without a deploy, that value should not live only in Python.

Python should implement the solver, validation, and objective math.
Postgres should hold human-managed policy and operational facts.

## Decision Rule

Use this test before adding any new scheduler behavior:

| Question | Store In | Reason |
|----------|----------|--------|
| Should a human change this without a deploy? | Postgres | It is policy or operational data |
| Does this vary by academic year, site, service line, or person? | Postgres | It is scoped configuration |
| Is this a preloaded fact or locked schedule input? | Postgres | It is source data, not solver logic |
| Is this the CP-SAT model structure, penalty math, or variable construction? | Python | It is implementation logic |
| Is this a safety/compliance limit that already has a settings table? | Postgres, then read by Python | One source of truth |

## What Belongs In Postgres

These values should be editable by humans through UI/API, not by changing code:

- Constraint enable or disable state
- Soft-constraint weights
- Role caps and clinic targets
- Per-duty clinic min or max values
- Per-duty day-of-week availability
- Faculty call preferences
- Protected slots and preloaded schedule facts
- Effective-dated policy by academic year
- Call calendar rules, if operations may change them
- FMIT calendar policy, if operations may change it
- Global compliance settings already modeled as application settings

## What Belongs In Python

These values should remain code:

- Constraint class implementations
- CP-SAT variable definitions
- Objective construction
- Penalty application logic
- Validation algorithms
- Translation from DB policy rows into scheduling context

## Current Split Sources Of Truth

The repository still has several places where human policy is encoded in Python or JSON instead of being read from Postgres.

### 1. Primary Duty Policy Lives In Airtable Export JSON

Current location:

- `backend/app/scheduling/constraints/primary_duty.py`
- `docs/schedules/sanitized_primary_duties.json`

What is still code-side config:

- clinic min per week
- clinic max per week
- available weekdays
- allowed clinic templates

Why this is the wrong boundary:

- these are human-owned scheduling rules
- they vary by duty and person
- they should be auditable and editable without a deploy

### 2. Role Defaults Still Live In Python Properties

Current location:

- `backend/app/models/person.py`

Code-derived values:

- `weekly_clinic_limit`
- `block_clinic_limit`
- `sm_clinic_weekly_target`
- `avoid_tuesday_call`
- `prefer_wednesday_call`

Why this is the wrong boundary:

- these are operational role policies and preferences
- humans may want to override them
- the UI should edit data, not mutate Python behavior

### 3. Settings Exist In Postgres But Solver Rules Still Hardcode Values

Current DB-backed settings:

- `work_hours_per_week`
- `max_consecutive_days`
- `min_days_off_per_week`
- `pgy1_supervision_ratio`
- `pgy2_supervision_ratio`
- `pgy3_supervision_ratio`

Current Python constants still used by the solver:

- `backend/app/scheduling/constraints/acgme.py`

Why this is dangerous:

- the application appears configurable
- the solver may ignore the configured value
- humans cannot trust the admin setting unless tests prove it is wired through

### 4. Overnight Call And FMIT Calendar Policy Is Hardcoded

Current location:

- `backend/app/scheduling/constraints/call_coverage.py`
- `backend/app/scheduling/constraints/fmit.py`
- `backend/app/services/call_assignment_service.py`

Examples:

- Sun-Thu overnight call days
- Fri-Sat owned by FMIT
- FMIT week defined as Fri-Thu
- Sunday blocking after FMIT

These are valid code defaults, but if operations may change them they should move to one DB-backed policy source.

### 5. Curriculum Day Rules Are Still Fixed In Code

Current location:

- `backend/app/scheduling/constraints/temporal.py`
- `backend/app/scheduling/constraints/resident_weekly_clinic.py`

Examples:

- Wednesday AM intern-only clinic
- Wednesday AM protected academic time

If these are truly immutable institutional rules, code is acceptable.
If admins may shift them, they should come from patterns or requirements stored in Postgres.

## Data Already In The Right Place

Some important human-owned inputs are already DB-backed and should stay there:

- `RotationTemplate.max_residents`
- `RotationTemplate.includes_weekend_work`
- `RotationTemplate.requires_specialty`
- `WeeklyPattern.is_protected`
- per-person clinic min or max fields on `Person`
- preload tables

The design problem is not "move everything to DB."
The problem is "stop splitting one policy across DB and Python."

## Recommended Target Architecture

### Postgres Is The Source Of Truth For Policy

Human-editable policy should be stored in DB tables with:

- explicit schema validation
- audit trail
- effective dates or academic year scope
- optional per-person overrides
- admin UI and API support

### Python Is The Enforcement Layer

Python should:

- load policy from DB
- translate policy into solver context
- enforce policy in constraint classes
- validate schedules against the same loaded policy

### Tests Must Prove The Wiring

Every DB-backed policy should have at least one end-to-end test:

1. update policy in DB or API
2. generate or validate schedule
3. confirm solver behavior changed

Without that test, the system may still have a hidden split source of truth.

## Migration Order

Recommended order for cleanup:

1. Finish moving preload and locked-input data into Postgres
2. Move primary duty policy into DB tables
3. Remove Python-derived role defaults and replace them with DB policy or explicit person fields
4. Wire `ApplicationSettings` into ACGME and supervision constraints
5. Centralize call and FMIT calendar policy in one data source
6. Convert non-physical hard constraints into soft penalties, eligibility filters, or validators

## What Not To Do

Avoid these patterns:

- building a GUI that edits Python constants
- adding more role-policy fallbacks in model properties
- keeping the same setting in both DB and Python
- claiming a setting is configurable when the solver does not read it
- moving solver math into free-form admin text fields

## Review Checklist

Before merging scheduler policy work, ask:

- Can a human change this without a deploy?
- Is there exactly one source of truth?
- Does the solver read the DB value?
- Does validation read the same value?
- Is there audit history?
- Is there academic-year or effective-date scope if needed?
- Is there an end-to-end test proving the wiring?

If the answer to the first question is "yes" and the answer to the second is "no," the design is off track.
