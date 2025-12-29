# Time Crystal Anti-Churn Integration Guide

This guide shows how to integrate the time crystal anti-churn objective function into the existing scheduling engine.

## Overview

The time crystal objective minimizes schedule churn while maintaining constraint satisfaction. This prevents unnecessary disruption to residents' schedules during regeneration.

## Quick Start

### 1. Basic Usage

```python
from app.scheduling.periodicity import (
    ScheduleSnapshot,
    time_crystal_objective,
    calculate_schedule_rigidity,
    estimate_churn_impact,
)

# Before regenerating schedule, capture current state
current_snapshot = ScheduleSnapshot.from_assignments(
    assignments=current_assignments,
    metadata={"algorithm": "cp_sat", "version": "2.0"}
)

# After solver runs, compare proposed vs current
proposed_snapshot = ScheduleSnapshot.from_tuples(
    assignment_tuples=solver_result.assignments
)

# Check rigidity before committing
rigidity = calculate_schedule_rigidity(proposed_snapshot, current_snapshot)
if rigidity < 0.7:
    logger.warning(f"Schedule changed significantly (rigidity={rigidity:.2f})")

# Get detailed impact analysis
impact = estimate_churn_impact(current_snapshot, proposed_snapshot)
print(f"Impact: {impact['severity']}")
print(f"Affected people: {impact['affected_people']}")
print(f"Recommendation: {impact['recommendation']}")
```

### 2. Integration with Existing Solvers

#### Option A: Post-Solver Evaluation (Simplest)

Add rigidity checking after solver runs but before committing to database:

```python
# In engine.py, after solver.solve()
from app.scheduling.periodicity import ScheduleSnapshot, estimate_churn_impact

def generate(self, algorithm="cp_sat", max_churn_severity="moderate", **kwargs):
    # ... existing code ...

    # Run solver
    result = solver.solve(context, existing_assignments)

    if result.success:
        # NEW: Check churn impact before accepting
        current_snapshot = ScheduleSnapshot.from_assignments(existing_assignments)
        proposed_snapshot = ScheduleSnapshot.from_tuples(result.assignments)

        impact = estimate_churn_impact(current_snapshot, proposed_snapshot)

        # Reject if churn is too high
        severity_order = ["minimal", "low", "moderate", "high", "critical"]
        if severity_order.index(impact["severity"]) > severity_order.index(max_churn_severity):
            logger.warning(
                f"Rejecting schedule due to excessive churn: {impact['severity']} "
                f"(max allowed: {max_churn_severity})"
            )
            return {
                "status": "rejected",
                "reason": f"Churn too high: {impact['recommendation']}",
                "impact": impact,
            }

    # ... continue with existing code ...
```

#### Option B: Integrate into Solver Objective (Advanced)

Modify solvers to optimize for both constraints AND rigidity:

```python
# In solvers.py - CP-SAT example

def solve(self, context: SchedulingContext, existing_assignments: list[Assignment] = None) -> SolverResult:
    # ... existing setup code ...

    # NEW: Build current assignment tracking
    current_assignment_map = {}
    if existing_assignments:
        for assignment in existing_assignments:
            key = (assignment.person_id, assignment.block_id)
            current_assignment_map[key] = assignment.rotation_template_id

    # ... existing variable creation ...

    # OBJECTIVE FUNCTION (Modified)
    # Add anti-churn penalty term

    churn_penalty_vars = []
    for person in context.residents:
        for block in context.blocks:
            for template in context.templates:
                # Check if this differs from current assignment
                current_template = current_assignment_map.get(
                    (person.id, block.id), None
                )

                if current_template is not None:
                    # This block was already assigned
                    if current_template != template.id:
                        # Different template = churn
                        churn_indicator = model.NewBoolVar(
                            f"churn_{person.id}_{block.id}_{template.id}"
                        )
                        # churn_indicator = 1 if this assignment differs from current
                        model.Add(churn_indicator == x[(person.id, block.id, template.id)])
                        churn_penalty_vars.append(churn_indicator)

    # Original objective terms
    coverage_penalty = ... # existing
    equity_penalty = ... # existing
    template_balance_penalty = ... # existing

    # NEW: Churn penalty
    churn_penalty = sum(churn_penalty_vars)

    # Weighted objective
    # alpha = 0.3 means 30% weight on minimizing churn
    alpha = 0.3  # Make this configurable
    model.Minimize(
        int((1 - alpha) * (coverage_penalty + equity_penalty + template_balance_penalty))
        + int(alpha * 100 * churn_penalty)  # Scale churn penalty
    )

    # ... rest of solver ...
```

#### Option C: Constraint-Based Churn Limit (Recommended)

Add a soft constraint that penalizes excessive churn:

```python
# In constraints/base.py or constraints/stability.py (new file)

class AntiChurnConstraint(SoftConstraint):
    """
    Soft constraint that penalizes schedule changes.

    Penalizes assignments that differ from the current schedule,
    encouraging stability while allowing necessary changes.
    """

    def __init__(
        self,
        current_assignments: list[Assignment],
        max_churn_per_person: int = 5,
        priority: ConstraintPriority = ConstraintPriority.MEDIUM,
    ):
        super().__init__(
            name="anti_churn",
            constraint_type=ConstraintType.CONTINUITY,
            priority=priority,
        )

        # Build lookup: (person_id, block_id) -> template_id
        self.current_map = {
            (a.person_id, a.block_id): a.rotation_template_id
            for a in current_assignments
        }
        self.max_churn_per_person = max_churn_per_person

    def add_to_cpsat(self, model, x, context: SchedulingContext) -> None:
        """Add anti-churn penalty to CP-SAT model."""
        from ortools.sat.python import cp_model

        churn_by_person = {}

        for person in context.residents:
            churn_count = model.NewIntVar(0, len(context.blocks), f"churn_{person.id}")
            churn_indicators = []

            for block in context.blocks:
                current_template = self.current_map.get((person.id, block.id))

                if current_template is not None:
                    for template in context.templates:
                        if template.id != current_template:
                            # This would be a change
                            var_name = f"{person.id}_{block.id}_{template.id}"
                            if var_name in x:
                                churn_indicators.append(x[var_name])

            # churn_count = sum of all changes for this person
            model.Add(churn_count == sum(churn_indicators))
            churn_by_person[person.id] = churn_count

            # Soft penalty: prefer to stay under max_churn_per_person
            # This will be added to the objective function
            excess = model.NewIntVar(0, len(context.blocks), f"churn_excess_{person.id}")
            model.AddMaxEquality(excess, [churn_count - self.max_churn_per_person, 0])

        return churn_by_person  # Return for use in objective

    def validate(
        self, assignments: list[Assignment], context: SchedulingContext
    ) -> ConstraintResult:
        """Validate anti-churn constraint (always soft, never fails)."""
        churn_by_person = defaultdict(int)
        total_churn = 0

        for assignment in assignments:
            current_template = self.current_map.get(
                (assignment.person_id, assignment.block_id)
            )
            if current_template and current_template != assignment.rotation_template_id:
                churn_by_person[assignment.person_id] += 1
                total_churn += 1

        # Calculate penalty
        penalty = sum(
            max(0, count - self.max_churn_per_person)
            for count in churn_by_person.values()
        )

        return ConstraintResult(
            satisfied=True,  # Soft constraint, never fails
            penalty=float(penalty),
        )
```

Then register it in `ConstraintManager`:

```python
# In constraints/manager.py

def create_anti_churn_manager(
    existing_assignments: list[Assignment],
    max_churn_per_person: int = 5,
) -> ConstraintManager:
    """
    Create constraint manager with anti-churn enabled.

    Args:
        existing_assignments: Current schedule assignments
        max_churn_per_person: Maximum acceptable changes per person

    Returns:
        ConstraintManager with anti-churn constraint registered
    """
    manager = ConstraintManager.create_default()

    # Add anti-churn constraint
    anti_churn = AntiChurnConstraint(
        current_assignments=existing_assignments,
        max_churn_per_person=max_churn_per_person,
        priority=ConstraintPriority.MEDIUM,
    )
    manager.add_constraint(anti_churn)

    return manager
```

## Configuration

### Environment Variables

Add to `.env`:

```bash
# Time Crystal Anti-Churn Settings
SCHEDULE_ANTI_CHURN_ENABLED=true
SCHEDULE_ANTI_CHURN_ALPHA=0.3        # Rigidity weight (0.0-1.0)
SCHEDULE_ANTI_CHURN_MAX_PER_PERSON=5 # Max changes per person
SCHEDULE_MAX_CHURN_SEVERITY=moderate # minimal|low|moderate|high|critical
```

### Engine Configuration

```python
# In engine.py

def generate(
    self,
    algorithm="cp_sat",
    enable_anti_churn: bool = True,
    anti_churn_alpha: float = 0.3,
    max_churn_severity: str = "moderate",
    **kwargs
):
    """
    Generate schedule with optional anti-churn optimization.

    Args:
        enable_anti_churn: Use time crystal anti-churn objective
        anti_churn_alpha: Weight for rigidity (0.0-1.0)
        max_churn_severity: Maximum acceptable churn level
    """
    # ... implementation using options above ...
```

## Monitoring and Metrics

### Dashboard Integration

Track rigidity metrics over time:

```python
# In analytics or monitoring service

def track_schedule_generation(
    schedule_run: ScheduleRun,
    current_snapshot: ScheduleSnapshot,
    proposed_snapshot: ScheduleSnapshot,
):
    """Record rigidity metrics for analysis."""
    rigidity = calculate_schedule_rigidity(proposed_snapshot, current_snapshot)
    impact = estimate_churn_impact(current_snapshot, proposed_snapshot)

    # Store in schedule_run metadata
    schedule_run.metadata = {
        **schedule_run.metadata,
        "rigidity": rigidity,
        "churn_impact": impact,
        "anti_churn_enabled": True,
    }

    # Emit metrics for Prometheus/Grafana
    metrics.histogram("schedule.rigidity", rigidity)
    metrics.gauge("schedule.affected_people", impact["affected_people"])
```

### Prometheus Metrics

```python
from prometheus_client import Histogram, Gauge

schedule_rigidity = Histogram(
    "schedule_rigidity",
    "Schedule rigidity score (0-1)",
    buckets=[0.0, 0.5, 0.7, 0.85, 0.95, 1.0]
)

schedule_churn_people = Gauge(
    "schedule_churn_affected_people",
    "Number of people affected by schedule changes"
)
```

## Testing

### Unit Tests

See `tests/scheduling/periodicity/test_anti_churn.py` for comprehensive unit tests.

### Integration Tests

```python
# tests/integration/test_anti_churn_integration.py

@pytest.mark.integration
async def test_schedule_regeneration_with_anti_churn(db, sample_schedule):
    """Test that regenerating schedule preserves most assignments."""
    # Get current assignments
    current_assignments = await get_assignments(db, sample_schedule.id)

    # Regenerate with anti-churn enabled
    engine = SchedulingEngine(db, start_date, end_date)
    result = await engine.generate(
        algorithm="cp_sat",
        enable_anti_churn=True,
        anti_churn_alpha=0.5,  # High stability preference
    )

    # Check rigidity
    assert result["rigidity"] > 0.7, "Schedule changed too much"
    assert result["impact"]["severity"] in ["minimal", "low"]
```

### Load Tests

```python
# load-tests/scenarios/anti-churn-regeneration.js

import { check } from 'k6';
import http from 'k6/http';

export let options = {
  vus: 10,
  duration: '5m',
};

export default function() {
  // Generate baseline schedule
  let baseline = http.post(`${BASE_URL}/schedule/generate`, {
    algorithm: 'cp_sat',
    enable_anti_churn: false,
  });

  // Regenerate with anti-churn
  let regenerated = http.post(`${BASE_URL}/schedule/generate`, {
    algorithm: 'cp_sat',
    enable_anti_churn: true,
    anti_churn_alpha: 0.3,
  });

  check(regenerated, {
    'rigidity > 0.7': (r) => JSON.parse(r.body).rigidity > 0.7,
    'runtime < 60s': (r) => r.timings.duration < 60000,
  });
}
```

## Best Practices

1. **Start Conservative**: Use `alpha=0.3` (30% stability weight) initially
2. **Monitor Impact**: Track rigidity metrics over time to tune alpha
3. **Gradual Rollout**: Enable for incremental regenerations first, then full regenerations
4. **User Communication**: Show impact estimate before publishing schedule
5. **Emergency Override**: Allow administrators to disable anti-churn for major restructuring

## Troubleshooting

### Issue: Rigidity too high (solver can't improve schedule)

**Solution**: Lower alpha value or disable anti-churn temporarily

```python
engine.generate(algorithm="cp_sat", anti_churn_alpha=0.1)  # Lower weight
```

### Issue: Rigidity too low (too much churn)

**Solution**: Increase alpha value or reduce max_churn_per_person

```python
engine.generate(
    algorithm="cp_sat",
    anti_churn_alpha=0.5,  # Higher weight
    max_churn_per_person=3,  # Stricter limit
)
```

### Issue: Solver timeout with anti-churn enabled

**Solution**: Anti-churn adds variables - increase timeout or use hybrid solver

```python
engine.generate(
    algorithm="hybrid",  # Use hybrid for complex problems
    timeout_seconds=120,  # Increase timeout
)
```

## References

- [Planning with Minimal Disruption](https://arxiv.org/abs/2508.15358) (Shleyfman et al., 2025)
- [Forecasting Interrupted Time Series](https://www.tandfonline.com/doi/full/10.1080/01605682.2024.2395315)
- [SYNERGY_ANALYSIS.md Section 11](../../../docs/SYNERGY_ANALYSIS.md#11-time-crystal-dynamics-for-schedule-stability)
- [Hamming Distance Metric Learning](https://www.researchgate.net/publication/283326408_Hamming_Distance_Metric_Learning)
