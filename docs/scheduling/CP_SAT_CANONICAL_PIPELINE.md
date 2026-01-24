# Canonical CP-SAT Pipeline (What Is Enforced Today)

Purpose:
This document describes the authoritative CP-SAT pipeline for schedule generation. It includes only the components that are actually enforced in the canonical path.

---

## New Components in the Canonical CP-SAT Path

1) Canonical CP-SAT enforcement
- SchedulingEngine.generate() forces algorithm="cp_sat".
- SchedulingEngine._run_solver() also forces CP-SAT regardless of caller.

2) Call coverage is enforced in CP-SAT
- Registered by default:
  - OvernightCallCoverageConstraint
  - AdjunctCallExclusionConstraint
  - CallAvailabilityConstraint

3) Call equity affects the objective
- Call equity constraints now use call-eligible indices.
- CP-SAT objective incorporates objective_terms (call equity penalties).

4) Half-day mode uses CP-SAT for call
- In half-day mode, CP-SAT generates call assignments (Sun-Thu).
- Rotation assignments are discarded (expanded from block assignments instead).

5) Faculty AT/C CP-SAT is mandatory
- No greedy fallback if OR-Tools is missing.

6) Activity locking centralization
- activity_locking.py defines locked/preload activity codes.
- Used by expansion + activity solver to protect preloaded/manual work.

7) Documentation and archival
- Canonical pipeline documented here.
- Non-canonical solver paths documented separately.

---

## Diagram (Canonical CP-SAT Flow)

```
                 +--------------------------------+
                 | SchedulingEngine.generate()    |
                 | (forces algorithm=cp_sat)      |
                 +---------------+----------------+
                                 |
                                 v
                  +-------------------------------+
                  | SyncPreloadService             |
                  |  - loads preloads (locked)     |
                  |  - skip stale faculty call     |
                  +---------------+----------------+
                                 |
                                 v
                +----------------------------------+
                | BlockAssignmentExpansionService   |
                |  - expands block -> half-day      |
                |  - respects locked activities     |
                +---------------+------------------+
                                 |
                                 v
                +----------------------------------+
                | SchedulingContext                |
                |  - call-eligible faculty         |
                |  - availability, templates       |
                +---------------+------------------+
                                 |
                                 v
          +-------------------------------------------+
          | CP-SAT Call Solve (CPSATSolver)            |
          |  - call vars (Sun-Thu)                     |
          |  - call coverage constraints               |
          |  - call equity objective_terms             |
          +---------------+---------------------------+
                                 |
                                 v
                +----------------------------------+
                | Sync PCAT/DO from Call            |
                |  - writes locked preload slots    |
                +---------------+------------------+
                                 |
                                 v
                +----------------------------------+
                | CP-SAT Activity Solver            |
                |  - assigns C/LEC/ADV              |
                |  - skips locked/manual slots      |
                +---------------+------------------+
                                 |
                                 v
                +----------------------------------+
                | CP-SAT Faculty AT/C Solver        |
                |  - fills AT + clinic              |
                |  - no greedy fallback             |
                +---------------+------------------+
                                 |
                                 v
                +----------------------------------+
                | Validation + Commit               |
                |  - ACGME validator                |
                +----------------------------------+
```

---

## Component Map (What Happens Where)

### Orchestration
- backend/app/scheduling/engine.py
  - Enforces CP-SAT globally
  - Half-day flow: preloads -> expansion -> CP-SAT call -> PCAT/DO -> CP-SAT activities -> CP-SAT faculty -> validate

### Call Coverage + Equity
- backend/app/scheduling/constraints/manager.py
  - Registers call coverage constraints by default
- backend/app/scheduling/constraints/call_coverage.py
  - Exactly one call per Sun-Thu night
  - Adjunct exclusion, availability enforcement
- backend/app/scheduling/constraints/call_equity.py
  - Equity / spacing / preference penalties
  - Uses call-eligible indices

### CP-SAT Objective Integration
- backend/app/scheduling/solvers.py
  - objective_terms included in objective (call equity affects solution)

### Half-Day Activity Assignment
- backend/app/scheduling/activity_solver.py
  - CP-SAT assignment of C/LEC/ADV
  - Uses centralized activity locking

### Faculty AT/C Assignment
- backend/app/services/faculty_assignment_expansion_service.py
  - CP-SAT model for AT + clinic
  - No greedy fallback

### Activity Locking
- backend/app/utils/activity_locking.py
  - Single source of truth for locked/preload activity codes

---

## Why Non-Canonical Components Are Not Included

This document is a source of truth for what the system actually enforces today. Non-wired or disabled components are excluded to avoid:
- Misleading operators about enforcement
- Hiding data-dependency gaps
- Creating false expectations in schedule review

For non-canonical constraints and solver paths, see:
- docs/scheduling/NON_CANONICAL_CONSTRAINTS.md
