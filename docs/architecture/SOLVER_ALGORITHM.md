***REMOVED*** Solver Algorithm Documentation

Comprehensive documentation of the scheduling engine's constraint-based optimization system.

> **Last Updated:** 2025-12-24
> **Purpose:** Technical reference for understanding schedule generation internals

---

***REMOVED******REMOVED*** Table of Contents

1. [Overview](***REMOVED***overview)
2. [Algorithm Architecture](***REMOVED***algorithm-architecture)
3. [High-Level Flow](***REMOVED***high-level-flow)
4. [Key Components](***REMOVED***key-components)
5. [Constraint System](***REMOVED***constraint-system)
6. [Data Structures](***REMOVED***data-structures)
7. [Input/Output Flow](***REMOVED***inputoutput-flow)
8. [Optimization Techniques](***REMOVED***optimization-techniques)
9. [Performance Characteristics](***REMOVED***performance-characteristics)
10. [Best Practices](***REMOVED***best-practices)
11. [Files and Locations](***REMOVED***files-and-locations)

---

***REMOVED******REMOVED*** Overview

The Residency Scheduler uses a **multi-algorithm, constraint-based optimization system** for generating medical residency schedules. It combines classical operations research techniques (constraint programming, linear programming) with modular constraint management to produce ACGME-compliant schedules.

***REMOVED******REMOVED******REMOVED*** Design Philosophy

- **Constraint-first**: All scheduling rules (ACGME, availability, resilience) are expressed as composable constraints
- **Multi-solver support**: Different algorithms for different performance/quality tradeoffs
- **Separation of concerns**: Constraints are independent of solver implementation
- **Fail-safe**: Atomic transactions ensure no partial schedules are created

---

***REMOVED******REMOVED*** Algorithm Architecture

***REMOVED******REMOVED******REMOVED*** Solver Types

The system implements **four main solver algorithms** with different performance characteristics:

| Solver | Type | Performance | Best For |
|--------|------|-------------|----------|
| **Greedy** | Heuristic | <1s (<1000 blocks) | Quick solutions, explanations |
| **CP-SAT** | Constraint Programming | 1-60s (medium-large) | Optimal solutions, complex constraints |
| **PuLP** | Linear Programming | 1-30s (large problems) | Speed, scalability |
| **Hybrid** | CP-SAT + PuLP fallback | 60-300s | Reliability, best results |

**Alternative Solvers (experimental):**
- **Pyomo**: Rich mathematical modeling with sensitivity analysis
- **Quantum-Inspired**: Simulated annealing and QUBO formulation
- **Tensegrity**: Structural resilience-based optimization

***REMOVED******REMOVED******REMOVED*** Algorithm Selection Guide

```
complexity_score < 20  → greedy     (<1 second, needs explanation)
complexity_score < 50  → pulp       (1-10 seconds, fast)
complexity_score < 75  → cp_sat     (10-60 seconds, optimal)
complexity_score >= 75 → hybrid     (60-300s, fallback reliability)
```

---

***REMOVED******REMOVED*** High-Level Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. INPUT: Residents, Faculty, Blocks, Rotation Templates    │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│ 2. BUILD AVAILABILITY MATRIX from Absences                  │
│    - Mark blocking vs. partial absences                     │
│    - Create {person_id → {block_id → availability}}         │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│ 3. CREATE SCHEDULING CONTEXT                                │
│    - Bundle all data for solvers (avoids DB queries)        │
│    - Load resilience data (hub scores, N-1 vulnerable)      │
│    - Build lookup indices for fast access                   │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│ 4. SELECT & RUN SOLVER ALGORITHM                            │
│    - Apply modular constraint system                        │
│    - Solve with selected backend (greedy/CP-SAT/PuLP)       │
│    - Return assignments as (person_id, block_id, template)  │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│ 5. ASSIGN FACULTY SUPERVISION (Post-processing)             │
│    - Group resident assignments by block                    │
│    - Calculate required faculty (ACGME ratios)              │
│    - Assign least-loaded available faculty                  │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│ 6. VALIDATE ACGME COMPLIANCE                                │
│    - Check 80-hour rule (rolling 4-week windows)            │
│    - Check 1-in-7 rule (days off)                           │
│    - Verify supervision ratios                              │
│    - Audit NF→PC transitions                                │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│ 7. OUTPUT: Validated Schedule                               │
│    - Persistent in database (all-or-nothing transaction)    │
│    - Returns validation results & resilience warnings       │
└─────────────────────────────────────────────────────────────┘
```

---

***REMOVED******REMOVED*** Key Components

***REMOVED******REMOVED******REMOVED*** 1. SchedulingEngine (engine.py)

**Purpose:** Orchestrates the entire scheduling process

**Key Methods:**
| Method | Purpose |
|--------|---------|
| `generate()` | Main entry point, returns complete schedule with validation |
| `_build_availability_matrix()` | Preprocesses absences into lookup matrix |
| `_build_context()` | Creates SchedulingContext with all scheduling data |
| `_run_solver()` | Executes selected algorithm |
| `_assign_faculty()` | Post-solver faculty supervision assignment |
| `_populate_resilience_data()` | Integrates resilience constraints |

**Features:**
- Automatic algorithm fallback (CP-SAT → Greedy if timeout)
- FMIT assignment preservation (faculty on inpatient)
- Pre/post resilience health checks
- NF→PC audit for Night Float to Post-Call transitions
- Atomic transaction boundaries (all-or-nothing)

***REMOVED******REMOVED******REMOVED*** 2. Solver Implementations (solvers.py)

***REMOVED******REMOVED******REMOVED******REMOVED*** GreedySolver

**Algorithm:**
```
1. Score blocks by difficulty (fewest eligible residents = hardest)
2. Process hardest blocks first
3. For each block:
   - Find eligible residents (check availability)
   - Score candidates: prefer fewer current assignments
   - Select highest-scoring resident
   - Choose best template for rotation distribution
4. Generate explainability (why this resident? confidence?)
```

**Advantages:** Fast, transparent, needs no external packages
**Limitations:** Not optimal, greedy myopia, can get stuck locally

***REMOVED******REMOVED******REMOVED******REMOVED*** CPSATSolver

**Algorithm:**
```
1. Create 3D binary decision variables: x[resident, block, template]
2. Add base constraint: ≤1 rotation per resident per block
3. Apply all enabled constraints from ConstraintManager
4. Maximize: coverage × 1000 - equity_penalty - template_balance_penalty
5. Solve with OR-Tools CP-SAT (parallel workers)
6. Extract solution
```

**Advantages:** Optimal within timeout, constraint propagation, parallel solving
**Limitations:** Requires OR-Tools package, slower on very large problems
**Progress Tracking:** Redis callback tracks solution progress in real-time

***REMOVED******REMOVED******REMOVED******REMOVED*** PuLPSolver

**Algorithm:**
```
1. Create 3D binary variables: x[resident, block, template]
2. Add constraints (one rotation per block)
3. Apply ConstraintManager constraints
4. Maximize same objective as CP-SAT
5. Solve with LP backend (CBC/GLPK/Gurobi)
6. Extract solution
```

**Advantages:** Very fast, works with multiple backends
**Limitations:** Linear programming (some constraints require linearization)

***REMOVED******REMOVED******REMOVED******REMOVED*** HybridSolver

**Algorithm:**
```
1. Try CP-SAT with 60s timeout → if succeeds, return
2. Fallback to PuLP with 30s timeout → if succeeds, return
3. Return failure if both fail
```

**Best Practice:** Use for production schedules (reliability + quality)

***REMOVED******REMOVED******REMOVED*** 3. Validator (validator.py)

**ACGME Compliance Validation:**

```python
validator = ACGMEValidator(db)
result = validator.validate_all(start_date, end_date)
***REMOVED*** Returns: ValidationResult with violations, coverage_rate, statistics
```

**Checks Performed:**
1. **80-hour rule**: All rolling 4-week windows checked
2. **1-in-7 rule**: Max consecutive days without day off
3. **Supervision ratios**: Faculty count vs. resident count per block
4. **Coverage rate**: % of blocks assigned (target: 100%)

---

***REMOVED******REMOVED*** Constraint System

***REMOVED******REMOVED******REMOVED*** Architecture

```
Constraint (ABC)
  ├─ HardConstraint (must be satisfied)
  │   ├─ AvailabilityConstraint
  │   ├─ EightyHourRuleConstraint
  │   ├─ OneInSevenRuleConstraint
  │   └─ SupervisionRatioConstraint
  │
  └─ SoftConstraint (optimization objectives)
      ├─ EquityConstraint
      ├─ ContinuityConstraint
      ├─ CoverageConstraint
      ├─ HubProtectionConstraint (resilience)
      ├─ UtilizationBufferConstraint (resilience)
      └─ PreferenceTrailConstraint (stigmergy)
```

***REMOVED******REMOVED******REMOVED*** Constraint Manager

- **Composable**: add/remove/enable/disable constraints dynamically
- **Priority-based**: sorts by ConstraintPriority.CRITICAL → LOW
- **Multi-backend**: `apply_to_cpsat()`, `apply_to_pulp()`, `validate()`

***REMOVED******REMOVED******REMOVED*** Hard Constraints (ACGME)

| Constraint | Priority | Description |
|------------|----------|-------------|
| **Availability** | CRITICAL | No assignments during blocking absences (TDY, deployment, medical) |
| **80-Hour Rule** | CRITICAL | Max 80 hours/week averaged over rolling 4-week (28-day) windows |
| **1-in-7 Rule** | CRITICAL | At least one 24-hour period off every 7 days |
| **Supervision Ratios** | CRITICAL | PGY-1: 1:2, PGY-2/3: 1:4 faculty-to-resident ratios |
| **Capacity** | CRITICAL | At most 1 rotation per block per person |

**80-Hour Rule Enforcement:**
- Max blocks ≤ 53 per 28-day window
- Calculation: 6 hours/block × 53 = 318 hours = ~75 hrs/week (under 80)
- Checks ALL possible 28-day windows, not just calendar weeks

**1-in-7 Rule Enforcement:**
- Max consecutive assigned days ≤ 6
- Ensures rest period every 7 days

***REMOVED******REMOVED******REMOVED*** Soft Constraints (Optimization)

| Constraint | Weight | Description |
|------------|--------|-------------|
| **Coverage** | 1000 | Maximize blocks assigned |
| **Equity** | 10 | Balance workload across residents |
| **Template Balance** | 5 | Distribute across rotation types |
| **Continuity** | Tunable | Prefer consecutive assignments |
| **Hub Protection** | Resilience | Don't over-assign critical faculty |
| **Utilization Buffer** | Resilience | Keep utilization < 80% |

***REMOVED******REMOVED******REMOVED*** Constraint Application

For CP-SAT solver:
```python
***REMOVED*** Create decision variables
x[r_i, b_i, t_i] = model.NewBoolVar(f"x_{r_i}_{b_i}_{t_i}")

***REMOVED*** Add base constraint
model.Add(sum(rotations_for_block) <= 1)

***REMOVED*** Apply all enabled constraints
for constraint in constraint_manager.get_enabled():
    constraint.add_to_cpsat(model, variables, context)

***REMOVED*** Define objective
coverage = sum(x.values())
model.Maximize(coverage * 1000 - equity_penalty * 10 - template_balance * 5)

***REMOVED*** Solve
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 60
status = solver.Solve(model)
```

***REMOVED******REMOVED******REMOVED*** Constraint Tuning Example

```python
manager = ConstraintManager()
manager.add(AvailabilityConstraint())       ***REMOVED*** Must have
manager.add(EightyHourRuleConstraint())     ***REMOVED*** Must have
manager.add(EquityConstraint(weight=10.0))  ***REMOVED*** Soft, tunable
manager.add(ContinuityConstraint(weight=5.0))

***REMOVED*** Disable for faster solving if needed
if need_quick_result:
    manager.disable("Continuity")
```

---

***REMOVED******REMOVED*** Data Structures

***REMOVED******REMOVED******REMOVED*** Availability Matrix

```python
{
    resident_id: {
        block_id: {
            'available': bool,           ***REMOVED*** Can be assigned?
            'replacement': str,          ***REMOVED*** Activity (e.g., "TDY")
            'partial_absence': bool      ***REMOVED*** Partial or full blocking?
        }
    }
}
```

**Classification Logic:**
- **Blocking**: Deployment, TDY, extended medical → `available = False`
- **Partial**: Vacation, conference → `available = True, partial_absence = True`

***REMOVED******REMOVED******REMOVED*** SchedulingContext

```python
@dataclass
class SchedulingContext:
    residents: list[Person]
    faculty: list[Person]
    blocks: list[Block]
    templates: list[RotationTemplate]

    ***REMOVED*** Lookup indices for O(1) access
    resident_idx: dict[UUID, int]
    block_idx: dict[UUID, int]
    template_idx: dict[UUID, int]
    blocks_by_date: dict[date, list[Block]]

    ***REMOVED*** Availability lookup
    availability: dict[UUID, dict[UUID, dict]]

    ***REMOVED*** Resilience data (Tier 1)
    hub_scores: dict[UUID, float]              ***REMOVED*** Network centrality
    current_utilization: float                 ***REMOVED*** System utilization rate
    n1_vulnerable_faculty: set[UUID]           ***REMOVED*** Single points of failure
    preference_trails: dict[UUID, dict]        ***REMOVED*** Stigmergy preferences
    zone_assignments: dict[UUID, str]          ***REMOVED*** Blast radius zones
```

***REMOVED******REMOVED******REMOVED*** SolverResult

```python
class SolverResult:
    success: bool                              ***REMOVED*** Feasible/optimal found?
    assignments: list[tuple[UUID, UUID, UUID]] ***REMOVED*** (person_id, block_id, template_id)
    status: str                                ***REMOVED*** "optimal", "feasible", "infeasible"
    objective_value: float                     ***REMOVED*** Objective function value
    runtime_seconds: float                     ***REMOVED*** Solver time
    solver_status: str                         ***REMOVED*** Solver-specific status
    statistics: dict                           ***REMOVED*** Solver statistics
    explanations: dict                         ***REMOVED*** Per-assignment explanations (greedy)
```

---

***REMOVED******REMOVED*** Input/Output Flow

***REMOVED******REMOVED******REMOVED*** API Entry Point

```python
engine = SchedulingEngine(
    db=session,
    start_date=date(2025, 1, 1),
    end_date=date(2025, 12, 31)
)

result = engine.generate(
    pgy_levels=[1, 2, 3],                    ***REMOVED*** Optional filter
    rotation_template_ids=None,               ***REMOVED*** None = all clinic templates
    algorithm="cp_sat",                       ***REMOVED*** "greedy", "pulp", "hybrid"
    timeout_seconds=60.0,
    check_resilience=True,
    preserve_fmit=True                       ***REMOVED*** Keep faculty assignments
)
```

***REMOVED******REMOVED******REMOVED*** Output Structure

```python
{
    "status": "success" | "partial" | "failed",
    "message": str,
    "total_assigned": int,                   ***REMOVED*** Number of assignments created
    "total_blocks": int,                     ***REMOVED*** Total blocks in range
    "validation": {
        "valid": bool,
        "total_violations": int,
        "violations": [Violation],           ***REMOVED*** ACGME violations
        "coverage_rate": float,              ***REMOVED*** % blocks assigned
        "statistics": dict                   ***REMOVED*** Residents scheduled, etc.
    },
    "run_id": UUID,                          ***REMOVED*** ScheduleRun record ID
    "solver_stats": {
        "total_blocks": int,
        "total_residents": int,
        "coverage_rate": float,
        "branches": int,                     ***REMOVED*** CP-SAT branches explored
        "conflicts": int                     ***REMOVED*** CP-SAT conflicts
    },
    "nf_pc_audit": {                         ***REMOVED*** Night Float → Post-Call audit
        "compliant": bool,
        "total_nf_transitions": int,
        "violations": [NFPCAuditViolation]
    },
    "resilience": {                          ***REMOVED*** Resilience health assessment
        "pre_generation_status": str,        ***REMOVED*** GREEN, YELLOW, ORANGE, RED, BLACK
        "post_generation_status": str,
        "utilization_rate": float,           ***REMOVED*** Target: <0.80
        "n1_compliant": bool,                ***REMOVED*** Can survive loss of 1 faculty?
        "n2_compliant": bool,                ***REMOVED*** Can survive loss of 2 faculty?
        "warnings": [str],                   ***REMOVED*** Actionable warnings
        "immediate_actions": [str]           ***REMOVED*** Critical actions needed
    }
}
```

---

***REMOVED******REMOVED*** Optimization Techniques

***REMOVED******REMOVED******REMOVED*** 1. Pre-Processing

- **Availability Matrix Caching**: Build once, O(1) lookups during solving
- **Infeasible Pair Pruning**: Remove (resident, block) pairs that can't be assigned
- **Block Clustering**: Group by week/month for batch processing

***REMOVED******REMOVED******REMOVED*** 2. Complexity Estimation

```python
complexity = optimizer.estimate_complexity(context)
***REMOVED*** Returns: {
***REMOVED***   "score": 0-100,           ***REMOVED*** 0-20: greedy, 20-50: pulp, 50-75: cp_sat, 75+: hybrid
***REMOVED***   "variables": int,         ***REMOVED*** residents × blocks × templates
***REMOVED***   "constraints": int,       ***REMOVED*** All constraint equations
***REMOVED***   "sparsity": float,        ***REMOVED*** Unavailable slots / total slots
***REMOVED***   "recommended_solver": str
***REMOVED*** }
```

***REMOVED******REMOVED******REMOVED*** 3. Objective Function Decomposition

| Priority | Weight | Objective |
|----------|--------|-----------|
| Primary | 1000× | Coverage (blocks assigned) |
| Secondary | 10× | Equity penalty (workload balance) |
| Tertiary | 5× | Template balance penalty (rotation diversity) |

***REMOVED******REMOVED******REMOVED*** 4. Constraint Propagation (CP-SAT)

- Automatically prunes search space by deriving implications from constraints
- Reduces solving time by 5-10× compared to naive enumeration

***REMOVED******REMOVED******REMOVED*** 5. Template Balance Penalty

```python
***REMOVED*** Prevents all assignments going to one rotation type
max_template_count = model.NewIntVar(0, max_val, "max_template")
for template_id, count_vars in template_counts.items():
    model.Add(max_template_count >= count_vars)

***REMOVED*** Penalize max count in objective
objective -= template_balance_penalty * 5
```

---

***REMOVED******REMOVED*** Performance Characteristics

***REMOVED******REMOVED******REMOVED*** Scaling by Problem Size

| Problem Size | Greedy | PuLP | CP-SAT | Hybrid |
|---|---|---|---|---|
| <100 blocks | <0.1s | 0.5s | 1s | 1s |
| 100-500 blocks | 0.1s | 1-5s | 5-15s | 5-30s |
| 500-2000 blocks | 0.5-1s | 5-30s | 30-120s | 30-300s |
| >2000 blocks | 1-10s | timeout | timeout | hybrid fallback |

***REMOVED******REMOVED******REMOVED*** Complexity Factors

- **Variables**: residents × blocks × templates (can exceed 100k)
- **Constraints**: availability + 80-hour + 1-in-7 + capacity (can exceed 50k)
- **Sparsity**: More absences = easier problem (pruned search space)

---

***REMOVED******REMOVED*** Best Practices

***REMOVED******REMOVED******REMOVED*** 1. Solver Selection

| Use Case | Recommended Solver | Reason |
|----------|-------------------|--------|
| Demo/testing | `greedy` | Fast, with explanations |
| Production schedules | `hybrid` | Reliability + quality |
| Quick re-optimization | `pulp` | Speed for iterations |
| Maximum quality | `cp_sat` | Optimal solution |

***REMOVED******REMOVED******REMOVED*** 2. Incremental Scheduling

```python
***REMOVED*** Keep some assignments fixed during re-optimization
existing = db.query(Assignment).filter(...).all()
result = solver.solve(context, existing_assignments=existing)
```

***REMOVED******REMOVED******REMOVED*** 3. Transaction Management

- All assignments created in single transaction
- Failure → complete rollback (no partial data)
- ScheduleRun record tracks status: `in_progress → success/partial/failed`

***REMOVED******REMOVED******REMOVED*** 4. Concurrency Control

```python
***REMOVED*** Row-level locking prevents concurrent generations racing
blocks = (
    db.query(Block)
    .filter(Block.date >= start_date, Block.date <= end_date)
    .with_for_update(nowait=False)  ***REMOVED*** Wait for lock
    .all()
)
```

---

***REMOVED******REMOVED*** Files and Locations

| File | Purpose |
|------|---------|
| `backend/app/scheduling/engine.py` | Main orchestration |
| `backend/app/scheduling/solvers.py` | Solver implementations |
| `backend/app/scheduling/constraints/manager.py` | Constraint composition |
| `backend/app/scheduling/constraints/acgme.py` | ACGME rules |
| `backend/app/scheduling/constraints/resilience.py` | Resilience constraints |
| `backend/app/scheduling/validator.py` | ACGME compliance validation |
| `backend/app/scheduling/optimizer.py` | Complexity estimation & preprocessing |
| `backend/app/scheduling/explainability.py` | Greedy solver explanations |
| `backend/app/scheduling/pyomo_solver.py` | Sensitivity analysis solver |
| `backend/app/scheduling/quantum/` | Quantum-inspired solvers |

---

***REMOVED******REMOVED*** Related Documentation

- [Advanced Scheduling](advanced-scheduling.md) - Game theory, AIS, tensegrity algorithms
- [Cross-Disciplinary Resilience](cross-disciplinary-resilience.md) - Resilience framework integration
- [ACGME Compliance](../user-guide/acgme-compliance.md) - Regulatory requirements
- [API Reference](../api/scheduling.md) - API endpoints for scheduling

---

***REMOVED******REMOVED*** Summary

The scheduling engine is a **production-grade constraint satisfaction and optimization system** that:

1. **Supports multiple solvers** (greedy, CP-SAT, PuLP, hybrid) for different performance/quality tradeoffs
2. **Enforces ACGME compliance** through hard constraints (80-hour rule, 1-in-7, supervision)
3. **Optimizes workload equity** through soft constraints with tunable weights
4. **Integrates resilience** (hub protection, utilization buffers, N-1 contingency)
5. **Provides transparency** through constraint-based modeling and explainability
6. **Ensures correctness** through atomic transactions and comprehensive validation
7. **Scales efficiently** through availability matrix caching and complexity-aware solver selection

The modular constraint system enables domain experts to compose scheduling rules without modifying solver code, making the system extensible for different residency programs with unique requirements.

---

*This document is maintained as a living reference. Update when scheduling algorithms or constraints change.*
