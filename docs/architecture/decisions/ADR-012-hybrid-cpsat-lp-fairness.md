# ADR-012: Hybrid CP-SAT + LP Fairness Layer

**Date:** 2026-01
**Status:** Proposed
**Extends:** [ADR-002: Constraint Programming (OR-Tools)](ADR-002-constraint-programming-ortools.md)

## Context

The current CP-SAT solver (ADR-002) handles discrete assignment decisions well but struggles with fairness balancing:

- **Current approach**: Soft constraints with hand-tuned weights (`BALANCE_WEIGHT * (max_workload - min_workload)`)
- **Problem**: Weights require manual tuning, don't adapt to roster changes, and provide weak guidance to the solver
- **Symptom**: Suboptimal fairness outcomes despite long solve times; weights that work for one block fail for another

The CP-SAT solver is excellent at yes/no decisions (Dr. X on Call Friday? Resident Y in MICU Block 7?) but fairness is a continuous optimization problem better suited to Linear Programming.

## Decision

Implement a **three-stage hybrid architecture** combining LP for fairness guidance with CP-SAT for discrete assignment:

### Stage A: LP Pre-Pass (Fairness Targets)

**Purpose:** Compute optimal fairness targets and identify "expensive" resources.

**Variables:**
- Total nights per person over horizon
- Total weekends per person
- Clinic sessions per person
- Call frequency metrics

**Objective:** Minimize variance from targets:
```
minimize Σᵢ w_hours·|hoursᵢ - targetᵢ| + w_weekends·|wkndᵢ - targetᵢ|
```

**Output:**
- Target ranges per person
- **Dual values** (shadow prices) indicating how "expensive" it is to add one more hour/night for each person

### Stage B: CP-SAT Placement (Discrete Assignments)

**Purpose:** Place residents into slots respecting hard constraints, guided by LP duals.

**Hard Rules (unchanged):**
- ACGME duty limits (80-hour, 1-in-7, supervision)
- Coverage requirements
- FMIT protections, DONSAs
- Call policies (Sun-Thu vs Fri/Sat)

**Soft Rules (LP-guided):**
- Penalize assignments that push people into "expensive" (high-dual) categories
- `cost += dual_weight[p] * X[p,s]` for slots affecting tight resources

**Search Hints:**
- Prioritize filling slots for people with low dual penalties
- Add no-good cuts for patterns the LP marks as costly

### Stage C: LP Polish/Repair

**Purpose:** Fine-tune continuous variables after discrete choices are fixed.

**Actions:**
- Fix CP-SAT assignment decisions
- Re-solve a small LP to balance floaters/clinic sessions for hour equity
- If imbalance exceeds threshold, feed cuts back to CP-SAT and re-run

## Rationale

| Aspect | CP-SAT Only | Hybrid CP-SAT + LP |
|--------|-------------|---------------------|
| Fairness guidance | Static weights | Data-driven duals |
| Weight tuning | Manual, per-block | Automatic, adaptive |
| Search efficiency | Explores unfair branches | Prunes early via duals |
| N-1 resilience | Slow re-solve | Re-run LP, quick CP-SAT adapt |
| Solve time | Longer (weak guidance) | Shorter (LP steers search) |

### Why LP Duals Work

Linear programming **dual values** quantify the marginal cost of a constraint:
- If Person A's weekend constraint dual is high → they're at/near weekend limit
- If Person B's dual is low → they have capacity
- CP-SAT uses this signal: prefer assigning Person B to weekend calls

This replaces hand-picked penalty weights with mathematically grounded guidance.

## Consequences

### Positive
- **Less tuning**: Replace brittle weights with data-driven duals
- **Faster solves**: LP steers CP-SAT away from bad branches early
- **Adaptive fairness**: LP automatically adjusts when roster changes (deployments, leave)
- **Explainable**: Can show "Person X got fewer weekends because they were at capacity"
- **N-1 ready**: On roster change, rerun Stage A for new duals; CP-SAT adapts quickly

### Negative
- **Added complexity**: Three-stage pipeline vs single solver
- **Two libraries**: Requires both OR-Tools (CP-SAT) and LP solver (PuLP or OR-Tools LP)
- **Iteration overhead**: May require Stage B → Stage C → Stage B loops
- **Testing burden**: Need integration tests for stage handoffs

### Risks
- **Dual interpretation**: Duals from relaxed LP may not perfectly map to discrete problem
- **Cycling**: Stage B ↔ Stage C could cycle without convergence guarantees
- **Performance regression**: If LP overhead exceeds savings from guided search

## Implementation Sketch

### Stage A: LP Pre-Pass
```python
from pulp import LpProblem, LpMinimize, LpVariable, lpSum

# Variables: total nights/weekends per person
nights = {p: LpVariable(f'nights_{p}', lowBound=0) for p in persons}
weekends = {p: LpVariable(f'weekends_{p}', lowBound=0) for p in persons}

# Deviation variables for abs value
nights_over = {p: LpVariable(f'nights_over_{p}', lowBound=0) for p in persons}
nights_under = {p: LpVariable(f'nights_under_{p}', lowBound=0) for p in persons}

problem = LpProblem("Fairness_Targets", LpMinimize)

# Objective: minimize deviation from targets
target_nights = total_nights / len(persons)
problem += lpSum(nights_over[p] + nights_under[p] for p in persons)

# Constraints: capture deviation
for p in persons:
    problem += nights[p] - target_nights == nights_over[p] - nights_under[p]

problem.solve()

# Extract duals for fairness constraints
duals = {p: constraint.pi for p, constraint in fairness_constraints.items()}
```

### Stage B: CP-SAT with Dual Penalties
```python
from ortools.sat.python import cp_model

model = cp_model.CpModel()

# Assignment variables
X = {(p, s): model.NewBoolVar(f'assign_{p}_{s}') for p in persons for s in slots}

# Hard constraints (existing code)
add_acgme_constraints(model, X)
add_coverage_constraints(model, X)

# Soft constraints: LP-guided penalties
objective_terms = []
for p in persons:
    for s in slots:
        if is_night_slot(s):
            # Higher penalty for people with high dual (at capacity)
            penalty = int(duals[p] * SCALE_FACTOR)
            objective_terms.append(X[(p, s)] * penalty)

model.Minimize(sum(objective_terms))
```

### Stage C: LP Polish
```python
# Fix discrete assignments from Stage B
for (p, s), var in X.items():
    if solver.Value(var) == 1:
        # Fix this assignment
        fixed_assignments.append((p, s))

# Re-solve LP with fixed assignments for floater/clinic balance
# If imbalance > threshold, add cuts and re-run Stage B
```

## Migration Path

1. **Phase 1**: Implement LP pre-pass as standalone script, validate duals make sense
2. **Phase 2**: Feed duals to CP-SAT as soft constraints, compare solution quality
3. **Phase 3**: Add Stage C polish loop, measure convergence
4. **Phase 4**: Integrate into scheduling pipeline, replace existing balance weights

## Evaluation Criteria

| Metric | Current Baseline | Target |
|--------|------------------|--------|
| Weekend variance (std dev) | TBD | < 1.0 per block |
| Night call variance | TBD | < 2.0 per block |
| Solve time (30-day horizon) | TBD | ≤ baseline |
| Manual weight adjustments | 3-5 per block | 0 |

## References

- [ADR-002: Constraint Programming](ADR-002-constraint-programming-ortools.md) - Current CP-SAT approach
- [Multi-Objective Optimization](../multi-objective-optimization.md) - Existing fairness strategies
- `backend/app/scheduling/engine.py` - Current solver integration
- `backend/requirements.txt` - OR-Tools 9.8, PuLP 2.7+

## Related Work

- Benders decomposition (LP master + integer subproblem)
- Lagrangian relaxation (duals guide integer search)
- Column generation (iterative LP + pricing)

This proposal adapts these classical OR techniques for the specific structure of residency scheduling.

---

*Proposed for evaluation. Implementation would require benchmarking against current approach.*
