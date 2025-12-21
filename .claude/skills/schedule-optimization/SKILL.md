---
name: schedule-optimization
description: Multi-objective schedule optimization expertise using constraint programming and Pareto optimization. Use when generating schedules, improving coverage, balancing workloads, or resolving conflicts. Integrates with OR-Tools solver and resilience framework.
---

# Schedule Optimization Skill

Expert knowledge for generating and optimizing medical residency schedules using constraint programming and multi-objective optimization.

## When This Skill Activates

- Generating new schedules
- Optimizing existing schedules
- Balancing workload distribution
- Resolving scheduling conflicts
- Improving coverage patterns
- Reducing schedule fragmentation

## Optimization Objectives

### Primary Objectives (Hard Constraints)
These MUST be satisfied - schedule is invalid without them:

| Constraint | Description | Priority |
|------------|-------------|----------|
| ACGME Compliance | 80-hour, 1-in-7, supervision | P0 |
| Qualification Match | Only assign qualified personnel | P0 |
| No Double-Booking | One person, one place at a time | P0 |
| Minimum Coverage | Required staffing levels met | P0 |

### Secondary Objectives (Soft Constraints)
Optimize these after hard constraints satisfied:

| Objective | Description | Weight |
|-----------|-------------|--------|
| Fairness | Even workload distribution | 0.25 |
| Preferences | Honor stated preferences | 0.20 |
| Continuity | Minimize handoffs | 0.20 |
| Efficiency | Minimize gaps/fragments | 0.15 |
| Resilience | Maintain backup capacity | 0.20 |

## Solver Architecture

### Google OR-Tools CP-SAT
Primary constraint programming solver:

```python
# Located in: backend/app/scheduling/engine.py
from ortools.sat.python import cp_model

model = cp_model.CpModel()
# Define variables, constraints, objectives
solver = cp_model.CpSolver()
status = solver.Solve(model)
```

### Solver Configuration
| Parameter | Default | Description |
|-----------|---------|-------------|
| `max_time_seconds` | 300 | Solver timeout |
| `num_workers` | 8 | Parallel threads |
| `log_search_progress` | True | Show progress |

## Optimization Strategies

### 1. Pareto Optimization
Find solutions that balance multiple objectives:

```
No single "best" solution - instead find Pareto frontier:
- Solution A: Best fairness, moderate efficiency
- Solution B: Best efficiency, moderate fairness
- Solution C: Balanced trade-off
```

**MCP Tool:**
```
Tool: generate_pareto_schedules
Input: { objectives: [...], constraints: [...] }
Output: { frontier: [solution1, solution2, ...] }
```

### 2. Iterative Improvement
Start with feasible solution, improve incrementally:

```
1. Generate any valid schedule
2. Identify worst metric
3. Local search for improvements
4. Repeat until no improvement or timeout
```

### 3. Decomposition
Break large problem into smaller sub-problems:

```
Full Year Schedule
    ├── Q1 (Jan-Mar)
    │   ├── Month 1
    │   │   ├── Week 1-2
    │   │   └── Week 3-4
    │   └── ...
    └── Q2-Q4 (similar)
```

## Coverage Optimization

### Target Coverage Levels
| Rotation | Minimum | Target | Maximum |
|----------|---------|--------|---------|
| Inpatient | 2 | 3 | 4 |
| Emergency | 3 | 4 | 5 |
| Clinic | 1 | 2 | 3 |
| Procedures | 1 | 2 | 2 |

### Coverage Gap Resolution

**Step 1: Identify Gap**
```sql
SELECT date, session, rotation, COUNT(*) as coverage
FROM assignments
WHERE date BETWEEN :start AND :end
GROUP BY date, session, rotation
HAVING COUNT(*) < minimum_coverage;
```

**Step 2: Find Candidates**
- Available personnel (not scheduled)
- Under hour limits
- Qualified for rotation
- Fair workload consideration

**Step 3: Assign and Validate**
- Make assignment
- Re-run compliance check
- Update metrics

## Workload Balancing

### Fairness Metrics

| Metric | Formula | Target |
|--------|---------|--------|
| Gini Coefficient | Distribution equality | < 0.15 |
| Std Dev Hours | σ of weekly hours | < 5 |
| Max/Min Ratio | Highest/Lowest load | < 1.3 |

### Balancing Algorithm

```python
def balance_workload(assignments):
    while gini_coefficient(assignments) > 0.15:
        overloaded = find_highest_load()
        underloaded = find_lowest_load()

        # Find swappable shift
        shift = find_transferable_shift(overloaded, underloaded)
        if shift and is_valid_transfer(shift):
            transfer(shift, from=overloaded, to=underloaded)
        else:
            break  # No valid transfers available
```

## Preference Handling

### Preference Types
| Type | Priority | Example |
|------|----------|---------|
| Hard Block | Highest | "Cannot work Dec 25" |
| Soft Preference | Medium | "Prefer AM shifts" |
| Historical Pattern | Low | Past scheduling data |

### Preference Satisfaction
Aim for:
- 100% hard blocks honored
- 80%+ soft preferences
- 70%+ historical patterns

## Resilience Integration

### 80% Utilization Rule
Never schedule above 80% capacity (queuing theory):

```
If utilization > 80%:
    - Queue delays grow exponentially
    - No buffer for emergencies
    - Burnout risk increases
```

### N-1 Contingency
Schedule must remain valid if any one person unavailable:

```
Tool: run_contingency_analysis_resilience_tool
Check: Remove each person, verify coverage holds
```

### Static Fallbacks
Pre-compute backup schedules for common failure scenarios:

```
Tool: get_static_fallbacks_tool
Returns: { scenario: backup_schedule, ... }
```

## Optimization Workflow

### New Schedule Generation

**Step 1: Gather Inputs**
```yaml
inputs:
  - personnel: All available faculty/residents
  - rotations: Required rotation coverage
  - preferences: Submitted preferences
  - constraints: ACGME + program rules
  - horizon: Date range to schedule
```

**Step 2: Initialize Solver**
```python
engine = SchedulingEngine(
    solver="or-tools",
    objectives=["compliance", "fairness", "preferences"],
    timeout=300
)
```

**Step 3: Generate Solutions**
```python
solutions = engine.solve(inputs)
# Returns Pareto frontier of valid schedules
```

**Step 4: Present Options**
Show decision-makers 3-5 options with trade-offs:
- Option A: Maximizes fairness
- Option B: Maximizes preferences
- Option C: Balanced approach

**Step 5: Select and Finalize**
- Human selects preferred option
- System validates one more time
- Publish to calendar system

### Existing Schedule Optimization

**Step 1: Analyze Current State**
```
Tool: analyze_schedule_health
Returns: {
  compliance_score,
  fairness_score,
  coverage_gaps,
  improvement_opportunities
}
```

**Step 2: Identify Improvements**
Rank opportunities by impact/effort:
- Quick wins: Single swap fixes issue
- Medium effort: Multi-swap optimization
- Major restructure: Requires re-solve

**Step 3: Apply Changes**
- Execute as atomic transaction
- Validate after each change
- Rollback if validation fails

## Common Scenarios

### Scenario: New Block Schedule
**Input:** Need 13-week rotation schedule
**Process:**
1. Load rotation templates
2. Apply qualification constraints
3. Balance across 13 weeks
4. Optimize for preferences
5. Validate ACGME compliance
6. Generate 3 options for review

### Scenario: Coverage Emergency
**Input:** 3 faculty out sick tomorrow
**Process:**
1. Identify critical gaps
2. Query backup pool
3. Optimize minimal disruption
4. Execute emergency swaps
5. Document and rebalance later

### Scenario: Fairness Complaint
**Input:** Resident claims unfair workload
**Process:**
1. Run fairness analysis
2. Compare to cohort
3. If valid, identify rebalancing swaps
4. Execute approved changes
5. Monitor going forward

## Performance Metrics

### Solver Performance
| Metric | Target | Action if Missed |
|--------|--------|------------------|
| Solve Time | < 5 min | Increase timeout or decompose |
| Solution Quality | > 90% optimal | Tune weights |
| Constraint Satisfaction | 100% hard | Debug constraints |

### Schedule Quality
| Metric | Target | Measurement |
|--------|--------|-------------|
| ACGME Compliance | 100% | Zero violations |
| Coverage | 100% | All slots filled |
| Fairness (Gini) | < 0.15 | Weekly calculation |
| Preference Match | > 80% | Survey feedback |

## MCP Tools Reference

| Tool | Purpose |
|------|---------|
| `generate_schedule` | Create new schedule |
| `optimize_schedule` | Improve existing schedule |
| `analyze_schedule_health` | Quality metrics |
| `generate_pareto_schedules` | Multi-objective options |
| `validate_schedule` | Compliance check |
| `run_contingency_analysis_resilience_tool` | N-1/N-2 analysis |
