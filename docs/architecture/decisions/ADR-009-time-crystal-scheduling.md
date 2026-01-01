# ADR-009: Time Crystal Scheduling (Anti-Churn)

**Date:** 2025-12 (Session 20)
**Status:** Adopted

## Context

Schedule regeneration creates significant disruption:
- **Unnecessary churn**: Minor input changes cause major schedule rearrangements
- **Resident dissatisfaction**: Frequent changes disrupt personal planning
- **Cognitive load**: Coordinators must track what changed and why
- **Trust erosion**: Unstable schedules reduce confidence in the system

Standard optimization solvers find *an* optimal solution, not necessarily *the most similar* optimal solution to the previous schedule.

## Decision

Implement **Time Crystal Scheduling** with anti-churn objectives:

### Core Concepts

| Concept | Source | Application |
|---------|--------|-------------|
| **Anti-Churn Objective** | Operations research | Minimize edit distance from previous schedule |
| **Subharmonic Detection** | Physics | Identify natural cycles (7d, 14d, 28d ACGME windows) |
| **Stroboscopic Checkpoints** | Physics | State advances at discrete boundaries only |
| **Rigidity Scoring** | Materials science | Measure schedule stability (0.0-1.0) |

### Implementation Strategy

1. **Warm Start**: Initialize solver with previous schedule as starting point
2. **Edit Distance Penalty**: Add soft constraint penalizing changes from previous
3. **Boundary Detection**: Only regenerate at natural boundaries (week start, block end)
4. **Stability Metrics**: Track rigidity score and report to users

## Consequences

### Positive
- **Reduced volatility**: Schedules remain stable unless necessary
- **Higher satisfaction**: Residents prefer predictable schedules
- **Warm start efficiency**: Solver finds solutions faster with good initial state
- **Transparency**: Users see explicit "changes from previous" report
- **Configurable tradeoff**: Balance stability vs. optimality via weight parameter

### Negative
- **May sacrifice optimality**: Stable solution may not be globally optimal
- **Requires previous schedule**: Cold start has no reference point
- **Complexity**: Additional solver constraints and metrics
- **Parameter tuning**: Anti-churn weight must be calibrated per institution

## Implementation

### Anti-Churn Objective
```python
def add_anti_churn_objective(model, current_assignments, previous_assignments):
    """Penalize changes from previous schedule."""
    changes = []

    for (person, block, rotation) in current_assignments:
        prev_value = previous_assignments.get((person, block, rotation), 0)
        curr_var = current_assignments[(person, block, rotation)]

        # Variable = 1 if changed (either added or removed)
        changed = model.NewBoolVar(f'changed_{person}_{block}_{rotation}')
        model.Add(curr_var != prev_value).OnlyEnforceIf(changed)
        model.Add(curr_var == prev_value).OnlyEnforceIf(changed.Not())

        changes.append(changed)

    # Total changes to minimize
    total_changes = model.NewIntVar(0, len(changes), 'total_changes')
    model.Add(total_changes == sum(changes))

    return total_changes, ANTI_CHURN_WEIGHT
```

### Subharmonic Detection
```python
def detect_subharmonics(schedule_history: list[Schedule]) -> list[int]:
    """Identify natural periodicity in schedule patterns."""
    # Look for patterns at 7-day, 14-day, 28-day intervals
    CANDIDATE_PERIODS = [7, 14, 21, 28]

    detected = []
    for period in CANDIDATE_PERIODS:
        if has_strong_autocorrelation(schedule_history, period):
            detected.append(period)

    return detected
```

### Rigidity Score
```python
def calculate_rigidity(current: Schedule, proposed: Schedule) -> float:
    """Calculate schedule rigidity score (0.0-1.0).

    1.0 = completely rigid (identical schedules)
    0.0 = completely flexible (no overlap)
    """
    current_assignments = set(current.get_all_assignments())
    proposed_assignments = set(proposed.get_all_assignments())

    overlap = current_assignments & proposed_assignments
    union = current_assignments | proposed_assignments

    if not union:
        return 1.0  # Both empty = identical

    return len(overlap) / len(union)
```

### Stroboscopic Checkpoints
```python
def should_regenerate(current_date: date, last_regen: date) -> bool:
    """Only regenerate at natural boundaries."""
    # Weekly boundary (Sunday/Monday)
    if current_date.weekday() == 0 and last_regen.weekday() != 0:
        return True

    # Block boundary (based on academic calendar)
    if is_block_boundary(current_date):
        return True

    # ACGME 4-week averaging window boundary
    days_since = (current_date - last_regen).days
    if days_since >= 28:
        return True

    return False
```

## User Interface

### Change Report
```
Schedule Regeneration Report
============================
Rigidity Score: 0.85 (high stability maintained)
Total Changes: 12 assignments modified

Changes by Type:
- Swaps applied: 3
- Coverage gaps filled: 5
- Optimization improvements: 4

Affected Residents:
- Dr. Smith: 2 block changes
- Dr. Jones: 1 block change
...
```

### Stability Settings
```yaml
anti_churn:
  enabled: true
  weight: 10.0      # Higher = more stability preference
  min_rigidity: 0.7 # Alert if below this threshold
  report_changes: true
```

## References

- `docs/architecture/TIME_CRYSTAL_ANTI_CHURN.md` - Detailed concept documentation
- `backend/app/scheduling/anti_churn.py` - Implementation
- `backend/app/scheduling/periodicity/` - Subharmonic detection
- `.claude/dontreadme/synthesis/CROSS_DISCIPLINARY_CONCEPTS.md` - Concept mappings

## See Also

**Related ADRs:**
- [ADR-002: Constraint Programming](ADR-002-constraint-programming-ortools.md) - CP-SAT solver foundation for anti-churn
- [ADR-004: Resilience Framework](ADR-004-resilience-framework.md) - Stability enhances resilience
- [ADR-006: Swap System](../../.claude/dontreadme/synthesis/DECISIONS.md#adr-006-swap-system-with-auto-matching) - Swaps trigger schedule changes

**Implementation Code:**
- `backend/app/scheduling/anti_churn.py` - Anti-churn objective implementation
- `backend/app/scheduling/periodicity/subharmonics.py` - Cycle detection
- `backend/app/scheduling/stability/rigidity.py` - Rigidity scoring
- `backend/app/scheduling/engine.py` - Warm-start integration

**Architecture Documentation:**
- [Time Crystal Anti-Churn](../TIME_CRYSTAL_ANTI_CHURN.md) - Full conceptual documentation
- [Solver Algorithm](../SOLVER_ALGORITHM.md) - How anti-churn integrates with CP-SAT
- [Circadian Workload Resonance](../circadian-workload-resonance.md) - Related temporal patterns

**API Documentation:**
- [Schedule API](../../api/SCHEDULE_API.md) - Schedule generation with anti-churn

**User Guide:**
- Stability settings and rigidity score interpretation (to be documented)
