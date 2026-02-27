# OR-Tools CP-SAT 9.8 → 9.12 Migration Analysis

Upload all files from this folder, then paste the prompt below.

---

## Context

Military residency scheduling system using Google OR-Tools CP-SAT solver, currently **pinned to 9.8.x**. The solver assigns activities to half-day slots across 28-day blocks for ~12 residents and ~8 faculty, with 25+ soft constraint penalty weights.

**Known issues on 9.8:**
- Hint preservation is broken (partially fixed 9.9, fully rewritten 9.12)
- `repair_hint = True` + `max_presolve_iterations = 3` is the current workaround
- LP relaxation may be weak for pure binary assignment problems

**Uploaded files:**
- `solver/` — Main CP-SAT solver (solvers.py), activity solver with 25+ weights, fair call optimizer (two-phase), streaming callback, constraint config
- `constraints/` — Call equity constraint using AddMultiplicationEquality

**Problem size:** ~12 workers × 56 half-day slots × 6 activity types × 25 soft constraints = ~4,000 binary variables

---

## Section 1: Changelog Deep Dive (9.8 → 9.9 → 9.10 → 9.11 → 9.12)

Search the OR-Tools GitHub repository releases, changelogs, and commit history for EACH version bump:

For each version (9.9, 9.10, 9.11, 9.12), report:
1. **Breaking changes** — API removals, renames, behavior changes
2. **CP-SAT specific changes** — New constraints, solver improvements, parameter changes
3. **Python API changes** — Method name changes (PascalCase vs snake_case), new/removed methods
4. **Bug fixes** relevant to scheduling problems (hint bugs, symmetry detection, callback issues)

Deliver: Version-by-version migration notes with specific API calls from uploaded code that are affected.

---

## Section 2: API Compatibility Scan

Analyze every OR-Tools API call in the uploaded source files against 9.12 documentation:

1. **Variable creation:** NewBoolVar, NewIntVar — any signature changes?
2. **Constraint methods:** Add, AddExactlyOne, AddAbsEquality, AddMultiplicationEquality, OnlyEnforceIf — any deprecations?
3. **Solver parameters:** max_time_in_seconds, num_search_workers, log_search_progress — any renames or new defaults?
4. **Status constants:** OPTIMAL, FEASIBLE, INFEASIBLE — any enum changes?
5. **Callback pattern:** CpSolverSolutionCallback inheritance — any interface changes?
6. **Objective methods:** Minimize, Maximize — any changes?

For each API call found in the uploaded code, report: file, line, method, compatibility status (OK/DEPRECATED/REMOVED/CHANGED).

---

## Section 3: Hint System Evolution

The hint system is critical for our two-phase solver (rotation phase → activity phase). Research:

1. **9.8 hint behavior** — What exactly is broken? How do hints interact with presolve?
2. **9.9 partial fix** — What was changed? Which hint scenarios work now?
3. **9.12 full rewrite** — What's the new architecture? New parameters?
4. **AddHint API** — Any signature changes across versions?
5. **repair_hint parameter** — Still exists in 9.12? New alternatives?
6. **Best practices** — What's the recommended hint pattern in 9.12 for two-phase solving?

Deliver: Code diff showing what we'd change in our hint usage (currently in `activity_solver.py`).

---

## Section 4: Solver Behavioral Changes

Even with API compatibility, solver behavior can change:

1. **Default search strategy** — Has AUTOMATIC_SEARCH behavior changed?
2. **LP relaxation** — Any improvements for binary assignment problems?
3. **Symmetry detection** — `symmetry_level` parameter behavior across versions
4. **Worker portfolio** — Has the default subsolver portfolio changed?
5. **Presolve** — Any changes affecting our constraint patterns?
6. **Determinism** — Any changes to random_seed behavior with multiple workers?

For our problem size (~4,000 binary vars, 25 soft constraints), what performance changes should we expect?

---

## Section 5: New Features Worth Adopting

What new CP-SAT features in 9.9-9.12 could improve our solver?

1. **New constraint types** — Any new constraint methods useful for scheduling?
2. **New solver parameters** — Any tuning knobs that didn't exist in 9.8?
3. **Improved subsolver strategies** — Any new portfolio strategies?
4. **Better solution logging** — Any improvements to log_search_progress output?
5. **New Python API conveniences** — Any helper methods that simplify our code?

For each new feature, assess: applicability to our problem, expected benefit, adoption effort.

---

## Section 6: Migration Checklist

Based on Sections 1-5, produce an ordered migration checklist:

1. **Pre-migration:** Tests to run, baselines to capture
2. **Dependency update:** pip requirements change, any transitive dependency impacts
3. **Code changes required:** Specific file:line changes (if any)
4. **Code changes recommended:** Optional improvements using new features
5. **Testing strategy:** What to verify after upgrade (correctness, performance, determinism)
6. **Rollback plan:** How to revert if issues found
7. **Risk assessment:** LOW/MEDIUM/HIGH for each change with justification

Deliver: Copy-paste-ready migration checklist with risk ratings.
