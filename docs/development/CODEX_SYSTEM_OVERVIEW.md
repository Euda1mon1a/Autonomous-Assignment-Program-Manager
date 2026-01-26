# Codex System Overview

This document summarizes the current state of the residency scheduling system for Codex.

> **Auto-accept policy**: Accept edits for low-risk changes (docs, tests, formatting, non-breaking additions). Flag for review: schema changes, auth/security, constraint logic modifications.

## 1) System overview

- Stack: FastAPI backend + PostgreSQL database + React/Next.js frontend.
- Domain: residency scheduling with half-day blocks, rotations, absences, and ACGME supervision rules.
- Core flow: generate blocks -> build availability matrix -> run solver -> create assignments -> validate and report.

## 2) What was implemented today

- FMIT preservation: scheduling can preserve existing FMIT faculty assignments during generation.
- Block-half support: blocks expose a `block_half` property for split-rotation logic (first/second half of 4-week block).
- NF Post-Call constraint: night-float post-call protection added to constraints (see pending review for validation).
- Git history reconciliation: Merged `docs/session-14-summary` into `main` with `--allow-unrelated-histories` due to PII removal rewriting history. **FMIT code restored after merge overwrote it.**

## 3) Pending review items

- Preserved FMIT assignments should block supervision assignment to avoid double-booking.
- `block_half` should scope to the academic year; current lookup can cross years.
- Airtable absence import should normalize names to handle titles (e.g., "Dr.") and casing.

## 4) Domain concepts glossary

- Block: a half-day scheduling unit (AM or PM) with a date and block number.
- NF: Night Float rotation (often split within a block).
- PC: Post-Call (recovery time following night call).
- FMIT: Faculty Managing Inpatient Teaching (inpatient faculty coverage).
- ACGME: Accreditation body setting supervision ratios and workload limits.

## 5) Architecture notes

- Some rotation rules are hardcoded in services/constraints; others are data-driven via rotation templates.
- Activity type and leave eligibility are properties on rotation templates; they drive conflict logic.
- Scheduling solver logic is centralized; constraints are modular but not fully externalized.

## 6) Key files to focus on

- backend/app/scheduling/engine.py
- backend/app/scheduling/solvers.py
- backend/app/models/block.py
- backend/app/models/rotation_template.py
- backend/app/schemas/schedule.py
- backend/app/api/routes/schedule.py
- scripts/airtable_sync.py

## 7) Specific tasks for Codex

- Patch FMIT preservation so supervising assignments do not reuse preserved faculty in the same block.
- Fix `block_half` to scope to the current academic year and use `BLOCK_LENGTH_DAYS`.
- Normalize names in Airtable absence import to prevent missed matches.

## 8) Codex Context Prompt - Session 14/15 Handoff

### Instructions for Codex

- Context: FastAPI + PostgreSQL backend with a Next.js frontend.
- Scope: schedules trainees and supervisors for rotations, clinic, and call; enforces
  compliance rules.

### What Was Implemented Yesterday (Dec 21, 2025)

- Faculty Solver Integration Docs
  - Call-to-assignment mapping documentation
  - FMIT attending auto-call vs other faculty rotation clarification
  - Faculty-specific constraints (weekend call Fri AM - Sun noon)
  - Faculty require full solver integration (730 half-days)
  - Post-processing approach recommendation
- Wednesday Constraints
  - WednesdayAMInternOnlyConstraint - Only interns in clinic Wed AM
  - WednesdayPMSingleFacultyConstraint - Single faculty Wed PM
  - Registered in ConstraintManager
- Rotation Half-Day Requirements Model
  - RotationHalfDayRequirement model for rule-based half-day allocation
  - e.g., fm_clinic_halfdays=3, specialty_halfdays=6, academics_halfdays=1

### What Was Implemented Today (Dec 22, 2025)

1. FMIT Preservation
   - Status: IMPLEMENTED but may need verification after merge
   - Faculty Managing Inpatient Teaching assignments are preserved during
     schedule regeneration
   - Files: backend/app/scheduling/engine.py,
     backend/app/schemas/schedule.py
   - Key: preserve_fmit_assignments flag in ScheduleRequest

2. Block-Half Support
   - Status: IMPLEMENTED
   - 4-week blocks split into 2-week halves (block_half = 1 or 2)
   - Used for Night Float rotations where residents swap mid-block
   - Files: backend/app/models/block.py (block_half property),
     backend/app/models/rotation_template.py (is_block_half_rotation field)

3. Night Float Post-Call Constraint
   - Status: IMPLEMENTED
   - After Night Float ends -> mandatory full PC (Post-Call) day
   - PC = both AM and PM blocked for recovery
   - Files: backend/app/scheduling/constraints/night_float_post_call.py,
     migration 20251222_add_pc_rotation_template.py

4. Git History Reconciliation
   - Status: IN PROGRESS
   - PII was removed from history, causing branch divergence
   - Merged docs/session-14-summary into main with
     --allow-unrelated-histories
   - Accepted session-14-summary as base (has PII cleanup)
   - NEED TO VERIFY: FMIT code may have been overwritten during merge

### Pending Review Items

1. Verify FMIT preservation code exists after merge conflict resolution
2. Check NightFloatPostCallConstraint is properly registered in
   ConstraintManager
3. Review CLAUDE_REVIEW_PATCHES_4.md for suggested fixes:
   - block_half academic year scoping
   - Preserved FMIT blocking supervision assignment
   - Seed script credential configurability
   - Airtable name normalization

### Key Domain Concepts

| Term       | Meaning                                              |
|------------|------------------------------------------------------|
| Block      | 4-week rotation period (28 days)                     |
| Block-half | 2-week sub-period within a block                     |
| NF         | Night Float - overnight shift rotation               |
| PC         | Post-Call - mandatory recovery day after NF          |
| FMIT       | Faculty Managing Inpatient Teaching                  |
| ACGME      | Accreditation Council for Graduate Medical Education |

### Architecture Notes

- Hardcoded rotations: NF, NICU, PC, FMIT - fixed patterns
- Rule-based rotations: Use RotationHalfDayRequirement model (e.g., 3/10
  clinic half-days)
- Constraints: Hard constraints in backend/app/scheduling/constraints/
- Solver: Supports both OR-Tools CP-SAT and PuLP

### Files to Focus On

- backend/app/scheduling/engine.py          # Main scheduling logic
- backend/app/scheduling/constraints/       # All constraint implementations
- backend/app/models/block.py               # Block model with block_half
- backend/app/models/rotation_template.py   # Rotation templates
- backend/app/schemas/schedule.py           # API schemas
- docs/development/CLAUDE_REVIEW_PATCHES_4.md  # Suggested fixes

### What Codex Should Do

1. Verify FMIT code - Check if preserve_fmit_assignments and
   _load_fmit_assignments() exist in engine.py
2. Run tests - cd backend && pytest -x to catch any regressions
3. Apply patches from CLAUDE_REVIEW_PATCHES_4.md if they haven't been
   applied
4. Check constraint registration - Ensure NightFloatPostCallConstraint
   is in ConstraintManager.create_default()

### Plan: Night Float (NF) Post-Call Implementation

Completed (Session 14)

- FMIT Preservation
  - preserve_fmit_assignments in ScheduleRequest schema
  - _load_fmit_assignments() method in engine
  - Conditional deletion in _delete_existing_assignments()

- Block Half Support
  - block_half computed property on Block model (returns 1 or 2)
  - is_block_half_rotation field on RotationTemplate
  - NF-AM and NF-PM templates flagged as block-half rotations

### Architecture Decision: No 56-Slot Templates

Deprecated approach: Importing 56-slot templates from Airtable as
RotationSlot records.

New approach: Granularity at block-half level with:
1. Hardcoded rotations (NF, NICU, PC) - fixed patterns, absolute
2. Rule-based rotations (NEURO, Cardio, etc.) - use
   RotationHalfDayRequirement
3. PC override - trumps whatever follows NF/NICU

### Implementation Plan: NF Post-Call Constraint

Requirement

When Night Float ends -> next day is PC (Post-Call) full day (AM + PM
blocked).

PC trumps whatever the next rotation would have scheduled. This applies:
- When NF is in block-half 1 -> Day 15 = PC (start of block-half 2)
- When NF is in block-half 2 -> Day 1 of next block = PC

Existing Infrastructure

| Component                        | Location                                         | Purpose                           |
|----------------------------------|--------------------------------------------------|-----------------------------------|
| RotationHalfDayRequirement       | backend/app/models/rotation_halfday_requirement.py | Rule-based half-day allocation |
| PostCallAutoAssignmentConstraint | backend/app/scheduling/constraints/post_call.py  | Faculty post-call (PCAT/DO)       |
| is_block_half_rotation           | backend/app/models/rotation_template.py          | Flag for NF-type rotations        |
| block_half property              | backend/app/models/block.py                      | Returns 1 or 2 for block position |

New Components to Create

1. PC (Post-Call) Rotation Template

INSERT INTO rotation_templates (name, abbreviation, rotation_type,
leave_eligible, is_block_half_rotation)
VALUES ('Post-Call Recovery', 'PC', 'recovery', false, false);
- leave_eligible = false (cannot take leave on PC day)
- Not a block-half rotation itself (it's a single day)

2. Night Float Post-Call Constraint

File: backend/app/scheduling/constraints/night_float_post_call.py

class NightFloatPostCallConstraint(HardConstraint):
    """
    Enforces PC (Post-Call) full day after Night Float ends.

    Rules:
    - NF in block-half 1 -> Day 15 AM+PM = PC
    - NF in block-half 2 -> Day 1 of next block AM+PM = PC
    - PC trumps any other rotation assignment
    """

Logic:
1. Find all NF assignments for a resident
2. Determine which block-half NF occupies
3. Calculate PC day (first day after NF ends)
4. Force PC template for both AM and PM blocks
5. Remove/block any conflicting assignments

3. Integration with RotationHalfDayRequirement

For combined rotations like "NF+NEURO":
- Block-half 1: NF (hardcoded pattern)
- Day 15: PC (full day, hardcoded)
- Block-half 2 remainder (Days 16-28): NEURO follows
  RotationHalfDayRequirement
  - e.g., fm_clinic_halfdays=3, specialty_halfdays=6, academics_halfdays=1

Adjustment: RotationHalfDayRequirement.total_halfdays for post-NF
block-halves should be 24 (not 28) to account for PC day consuming 2
half-days.

Implementation Steps

Step 1: Create PC Template (migration + seeder)

- Add migration for PC rotation template
- Set rotation_type = 'recovery'
- Set leave_eligible = false

Step 2: Create NightFloatPostCallConstraint

- New file: backend/app/scheduling/constraints/night_float_post_call.py
- Implement add_to_cpsat() - force PC assignment after NF
- Implement add_to_pulp() - same for PuLP solver
- Implement validate() - check existing schedules

Step 3: Register Constraint

- Add to backend/app/scheduling/constraints/__init__.py
- Add to constraint registry in engine

Step 4: Modify RotationHalfDayRequirement Logic

- When calculating half-day allocation for post-NF block-half:
  - Subtract 2 half-days for PC
  - Distribute remaining (fm_clinic + specialty + academics) across 24
    half-days

Step 5: NF Coverage Constraint

- Ensure exactly 1 resident on NF per block-half
- Pair "+NF" (NF in half 2) with "NF+" (NF in half 1) for continuous
  coverage

Files to Modify/Create

| Action | File                                                        |
|--------|-------------------------------------------------------------|
| CREATE | backend/app/scheduling/constraints/night_float_post_call.py |
| CREATE | backend/alembic/versions/XXXXXX_add_pc_template.py          |
| MODIFY | backend/app/scheduling/constraints/__init__.py              |
| MODIFY | backend/app/scheduling/engine.py (register constraint)      |
| MODIFY | scripts/seed_rotation_templates.py (add PC template)        |

Validation Rules

1. PC must follow NF: Any resident with NF assignment must have PC on
   transition day
2. PC is full day: Both AM and PM must be PC (not split)
3. PC trumps all: No other rotation can override PC day
4. NF coverage: Each block-half has exactly 1 resident on NF

### Activity Abbreviations Reference

| Abbrev | Meaning                             | Hardcoded?      |
|--------|-------------------------------------|-----------------|
| NF     | Night Float                         | Yes             |
| PC     | Post-Call (recovery day)            | Yes             |
| NICU   | NICU Inpatient                      | Yes             |
| FMIT   | Faculty Managing Inpatient Teaching | Yes             |
| C      | Clinic                              | No (rule-based) |
| C30    | Clinic (30-min appointments)        | No (rule-based) |
| W      | Weekend                             | N/A             |
| OFF    | Off (covered by call)               | N/A             |
| LEC    | Lecture                             | No              |
| FMC    | FMC Meeting                         | No              |
| GME    | Graduate Medical Education Time     | No              |
| Sim    | Simulation                          | No              |

### Key Relationships

Combined Rotation: NF+NEURO (Block 10)
├── Block-half 1 (Days 1-14): Night Float [HARDCODED]
├── Day 15: Post-Call [HARDCODED, trumps NEURO]
└── Block-half 2 (Days 16-28): Neurology [RULE-BASED]
    ├── fm_clinic_halfdays: 3
    ├── specialty_halfdays: 6
    └── academics_halfdays: 1

NF Coverage Guarantee (per block):
├── Resident A: NICU+NF (NF in half 2)
└── Resident B: NF+Cardio (NF in half 1)
    -> Always 1 resident on NF for entire block
