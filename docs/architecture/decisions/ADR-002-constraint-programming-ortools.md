# ADR-002: Constraint Programming (OR-Tools) for Scheduling

**Date:** 2024-12
**Status:** Adopted

## Context

Medical residency schedule generation is a complex optimization problem:
- **NP-hard complexity**: Cannot be solved in polynomial time
- **Hard constraints**: ACGME rules must be satisfied (80-hour limit, 1-in-7 days off, supervision ratios)
- **Soft constraints**: Preferences should be optimized (fairness, continuity, personal preferences)
- **Feasibility detection**: Must prove when no valid schedule exists
- **Scalability**: Schedules span weeks/months with dozens of residents

Traditional approaches (manual assignment, simple heuristics) cannot guarantee compliance or optimality.

## Decision

Use **Google OR-Tools CP-SAT solver** for schedule generation:
- Model ACGME rules as **hard constraints** (must satisfy)
- Model preferences as **soft constraints** with weighted objectives
- Use constraint propagation to prune infeasible states
- Solver finds optimal or near-optimal solutions

### Constraint Categories

| Type | Examples | Modeling |
|------|----------|----------|
| **Hard** | 80-hour week limit, supervision ratios | Must satisfy or infeasible |
| **Soft** | Workload balance, preferences | Weighted objective function |
| **Institutional** | Call frequency, clinic requirements | Configurable hard/soft |

## Consequences

### Positive
- **Provably compliant**: Solver guarantees ACGME compliance or reports infeasibility
- **Multi-objective optimization**: Balance coverage, fairness, preferences simultaneously
- **Scalability**: CP-SAT handles real-world schedule sizes (<30 seconds typically)
- **Flexibility**: Easy to add new constraints without rewriting algorithm
- **Explanation**: Solver can identify which constraints cause conflicts

### Negative
- **Solver timeout**: Very complex schedules may hit time limits
- **Constraint encoding complexity**: Translating rules to CP variables requires expertise
- **Black box**: Solution process is not intuitive to non-technical users
- **Debugging difficulty**: Hard to trace why solver made specific choices
- **Memory usage**: Large schedules require significant memory

## Implementation

### Constraint Variable Model
```python
from ortools.sat.python import cp_model

model = cp_model.CpModel()

# Assignment variables: person p assigned to block b with rotation r
assignment = {}
for p in persons:
    for b in blocks:
        for r in rotations:
            assignment[(p, b, r)] = model.NewBoolVar(f'assign_{p}_{b}_{r}')
```

### Hard Constraint Example (80-Hour Rule)
```python
# Person cannot exceed 80 hours per week (rolling average over 4 weeks)
for person in persons:
    for week_start in week_starts:
        four_week_hours = []
        for week_offset in range(4):
            week_hours = sum(
                assignment[(person, block, rotation)] * rotation.hours
                for block in get_week_blocks(week_start + week_offset)
                for rotation in rotations
            )
            four_week_hours.append(week_hours)

        # Average must be <= 80
        model.Add(sum(four_week_hours) <= 80 * 4)
```

### Soft Constraint Example (Workload Balance)
```python
# Minimize variance in workload across persons
workloads = {}
for person in persons:
    workloads[person] = sum(
        assignment[(person, block, rotation)] * rotation.hours
        for block in blocks
        for rotation in rotations
    )

# Minimize max - min (proxy for variance)
max_workload = model.NewIntVar(0, MAX_HOURS, 'max_workload')
min_workload = model.NewIntVar(0, MAX_HOURS, 'min_workload')

model.AddMaxEquality(max_workload, list(workloads.values()))
model.AddMinEquality(min_workload, list(workloads.values()))

# Add to objective with weight
model.Minimize(BALANCE_WEIGHT * (max_workload - min_workload))
```

### Solving with Timeout
```python
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30.0

status = solver.Solve(model)

if status == cp_model.OPTIMAL:
    # Extract optimal solution
    pass
elif status == cp_model.FEASIBLE:
    # Solution found but may not be optimal
    pass
elif status == cp_model.INFEASIBLE:
    # No valid schedule exists - identify conflicting constraints
    pass
```

## Version Management

### Pinned Version: `>=9.8,<9.9`

**Date:** 2026-01-19
**Requirement:** `ortools>=9.8,<9.9` (backend/requirements.txt)
**Latest Available:** v9.15 (Jan 12, 2026) - Python 3.14 support

OR-Tools v9.9 (March 2024) introduced a **breaking API change** from PascalCase to snake_case:

```python
# Current codebase (PascalCase - OR-Tools 9.8)
model.NewBoolVar("x")
model.AddExactlyOne([vars])
solver.Solve(model)

# OR-Tools 9.9+ (snake_case - BREAKS existing code)
model.new_bool_var("x")
model.add_exactly_one([vars])
solver.solve(model)
```

**Impact:** 29 files, ~131 API calls would break on upgrade.

### Decision: Do Not Upgrade

| Factor | Assessment |
|--------|------------|
| Migration effort | 33-49 hours (~1 week) |
| Functional benefit | None - same CP-SAT features |
| Performance benefit | None - solver is C++ |
| Python 3.12 support | Until October 2028 |
| Risk | High effort, zero user-visible improvement |

**Revisit when:** Python 3.14 becomes required (earliest 2027), or a critical CP-SAT bug fix ships only in 9.9+.

### Debunked: Python 3.13/3.14 "Performance Unlock"

Claims that upgrading Python + OR-Tools will "unlock parallelism" or "cut solve time in half" are **false**:

| Claim | Reality |
|-------|---------|
| "GIL removal enables true parallelism" | OR-Tools **already releases the GIL** during C++ computation. The solver's heavy lifting happens in native code. |
| "Subinterpreters enable parallel constraints" | OR-Tools has built-in `num_workers` parallelism. Subinterpreters add overhead, not speed. |
| "30% speedup from tail-call interpreter" | Benchmarks show 5-15%. Irrelevant anyway—solver time is in C++, not Python. |
| "snake_case helps AI code generation" | API style has zero effect on LLM code quality. |

**The truth:** OR-Tools performance ceiling is in C++, not Python. Python version upgrades do not improve solver speed. Optimization gains come from:
- Tuning `num_workers` parameter (already available)
- Better constraint modeling
- Problem decomposition

## References

- [OR-Tools CP-SAT Documentation](https://developers.google.com/optimization/cp/cp_solver)
- `backend/app/scheduling/engine.py` - Schedule generation engine
- `backend/app/scheduling/constraints/` - Constraint implementations
- `docs/architecture/SOLVER_ALGORITHM.md` - Detailed algorithm documentation
- `docs/architecture/CONSTRAINT_INTERACTION_MATRIX.md` - Constraint interactions

## See Also

**Related ADRs:**
- [ADR-009: Time Crystal Scheduling](ADR-009-time-crystal-scheduling.md) - Anti-churn objectives built on CP-SAT
- [ADR-004: Resilience Framework](ADR-004-resilience-framework.md) - Uses solver for fallback schedule generation

**Implementation Code:**
- `backend/app/scheduling/engine.py` - CP-SAT solver integration
- `backend/app/scheduling/constraints/` - ACGME and institutional constraints
- `backend/app/scheduling/solvers/` - Multi-solver architecture

**Architecture Documentation:**
- [Solver Algorithm Details](../SOLVER_ALGORITHM.md) - In-depth algorithm explanation
- [Constraint Interaction Matrix](../CONSTRAINT_INTERACTION_MATRIX.md) - How constraints interact
- [Primary Duty Constraints](../primary-duty-constraints.md) - Core scheduling constraints
- [Multi-Objective Optimization](../multi-objective-optimization.md) - Balancing competing objectives

**API Documentation:**
- [Schedule API](../../api/SCHEDULE_API.md) - Schedule generation endpoints
