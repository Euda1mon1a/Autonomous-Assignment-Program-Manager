# GUI Editability Boundary

> Status: Draft target-state guidance
> Audience: Humans designing admin UI, API surface, and scheduler policy ownership

## Purpose

This document defines the final boundary for scheduler editability.

It answers four questions:

1. What should be editable in the GUI?
2. What should be stored in Postgres but not exposed directly in the GUI?
3. What should remain Python-only?
4. What still needs migration before the boundary is clean?

This is narrower than `POLICY_STORAGE_BOUNDARY.md`.
That document defines DB vs Python ownership.
This document defines UI vs DB-only vs Python-only ownership.

## Executive Summary

The target architecture is:

- GUI edits human policy and operational facts
- Postgres stores both editable policy and non-editable supporting data
- Python implements solver logic and enforcement

The GUI should never be a thin editor for Python constants.

## Decision Rule

Use this test before adding any new scheduler field:

| Question | Ownership |
|---|---|
| Should a coordinator or chief change this without a deploy? | GUI-editable |
| Should the system persist it, but humans should not manipulate it routinely? | DB-backed but not GUI-worthy |
| Does changing it mean changing solver logic rather than policy? | Python-only |
| Is it currently human-owned but still trapped in code? | Still needs migration |

## 1. GUI-Editable

These are the values humans should be able to change through admin UI and API.

### Constraint controls

- enable or disable state
- soft weights
- descriptive metadata if it affects operator understanding

Examples:

- `constraint_configurations` rows
- constraint admin page controls

Notes:

- A GUI weight control is valid only if the solver actually consumes that weight.
- If a constraint is still "soft by class" but hard in `add_to_cpsat()`, the UI should not pretend it is fully tunable.

### Primary duty policy

- duty name
- clinic minimum per week
- clinic maximum per week
- available weekdays

Examples:

- `primary_duty_configs`

Why:

- these are coordinator-owned scheduling rules
- they vary by person or duty
- they should not require a deploy

### Rotation template preload classification

- `is_offsite`
- `is_lec_exempt`
- `is_continuity_exempt`
- `is_saturday_off`
- `preload_activity_code`

Why:

- these drive preload behavior and exemption behavior
- they are operational template attributes, not solver internals

### Template and requirement policy

- `max_residents`
- `includes_weekend_work`
- `requires_specialty`
- resident weekly requirements
- protected slots
- activity requirements
- leave eligibility on templates

Why:

- these are planning inputs
- they should be editable by authorized humans

### Human-owned preferences and overrides

- faculty schedule preferences
- blocked weeks
- preferred weeks
- person-specific clinic caps
- person-specific call preferences

Why:

- these are operational preferences and overrides
- they should be auditable and editable without code changes

### Global scheduling policy already modeled as settings

- work hours per week
- consecutive day limits
- supervision ratios
- any effective-dated institutional scheduling settings

Why:

- once a setting exists as application data, humans expect it to be the source of truth

## 2. DB-Backed But Not GUI-Worthy

These should live in Postgres, but not necessarily be exposed in the main admin UI.

### Audit and history data

- version tables
- created or updated timestamps
- audit logs
- schedule history and provenance

Why:

- valuable for traceability
- not part of routine human editing

### Join tables and linkage data

- foreign-key relationships
- linking records between duties, people, templates, assignments
- internal association rows

Why:

- humans care about the outcome, not the raw linkage mechanics

### Derived or generated scheduling state

- solver snapshots
- generated assignments
- validation outputs
- metrics caches
- background task state

Why:

- these are machine outputs, not policy inputs

### Internal metadata that supports UI but should not be freely edited

- internal IDs
- archived-by metadata
- sync bookkeeping
- migration-seeded defaults

Why:

- store them in DB
- avoid making them routine admin controls

## 3. Python-Only Forever

These should stay code, even in the ideal end-state.

### Constraint implementations

- constraint classes
- `add_to_cpsat()`
- `add_to_pulp()`
- `validate()`

Why:

- this is solver behavior
- it requires code review and tests

### CP-SAT model structure

- variable creation
- objective assembly
- penalty variable construction
- implication logic
- equality and capacity expressions

Why:

- these are algorithm mechanics, not policy

### Translation and orchestration logic

- loading DB policy into scheduling context
- building eligibility sets
- solver orchestration
- result extraction
- schedule generation workflow

Why:

- these are implementation details

### True physical impossibilities

These should remain enforced in code even if their enabling metadata is DB-backed:

- actual availability blocking
- actual call availability blocking
- actual room or physician capacity limits
- protected or locked slots that represent immutable upstream facts

Why:

- these are hard model invariants
- the GUI may change the source data, but not the enforcement mechanism

## 4. Still Needs Migration

These are the main remaining places where the boundary is not yet clean.

### Role-derived clinic limits and call preferences

Current problem:

- `Person` still derives clinic caps and call preferences from role in Python properties

Examples:

- weekly clinic limit
- block clinic limit
- avoid Tuesday call
- prefer Wednesday call

Target:

- store human-owned role policy in DB
- keep Python only for enforcement

### Call and FMIT calendar policy

Current problem:

- overnight-call days and FMIT week shape are still embedded as code constants

Examples:

- Sun-Thu overnight call
- Fri-Sat FMIT ownership
- FMIT week defined as Fri-Thu

Target:

- one DB-backed policy source if operations may change it

### Curriculum timing rules

Current problem:

- some Wednesday rules are still fixed in code

Examples:

- Wednesday AM intern-only behavior
- related protected academic slots

Target:

- if mutable by the program, move to DB-backed requirements or patterns
- if truly immutable institutional law, keep code + document it clearly

### Hard-vs-soft solver semantics

Current problem:

- some constraints are now typed as soft but are still partially enforced with hard solver expressions

Why this matters for GUI:

- the GUI cannot safely present a weight slider as meaningful unless the solver actually uses penalties

Target:

- each GUI-tunable soft constraint should have:
  - DB-backed weight
  - actual penalty-variable implementation
  - clear operator-facing semantics

### Factory and default-construction assumptions

Current problem:

- some default constraint-manager paths now implicitly depend on DB access

Why this matters for GUI and admin tooling:

- admin pages, seed paths, and validation tools should not break because policy loading assumptions changed

Target:

- explicit DB requirements
- explicit fallback policy
- no accidental hidden dependency on a live DB session

## Practical Target State

The clean end-state should look like this:

### GUI-editable

- constraint enable/disable
- soft weights
- primary duty config
- preload classification
- template operational attributes
- person-level preferences and overrides
- application scheduling settings

### DB-backed but not GUI-first

- audit history
- linkage tables
- generated scheduling state
- internal metadata

### Python-only

- solver implementation
- constraint logic
- CP-SAT modeling
- orchestration
- enforcement of physical impossibilities

### Remaining migrations

- role-derived policy
- call/FMIT calendar rules
- mutable curriculum timing rules
- incomplete soft-constraint refactors

## Anti-Patterns

Do not do these:

- add a GUI toggle that does not change solver behavior
- mark something configurable when Python still ignores the DB value
- expose raw internal linkage fields because "they are in the table"
- build a GUI for algorithm constants
- treat class inheritance alone as proof that a constraint is operationally soft

## Definition Of Done

The editability boundary is healthy when:

- every human-owned scheduling policy has a DB source of truth
- every GUI control maps to a real backend behavior change
- every soft constraint exposed in UI is actually implemented with penalties
- no operator needs a deploy to change policy
- no operator can accidentally edit solver internals through the UI
