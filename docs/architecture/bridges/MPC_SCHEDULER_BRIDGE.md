***REMOVED*** MPC-Scheduler Bridge Specification

**Document Version:** 1.0
**Date:** 2025-12-26
**Status:** Implementation Ready
**Purpose:** Bridge Model Predictive Control (MPC) theory to residency schedule generation

---

***REMOVED******REMOVED*** Table of Contents

1. [Executive Summary](***REMOVED***executive-summary)
2. [Mathematical Foundation](***REMOVED***mathematical-foundation)
3. [Architecture Overview](***REMOVED***architecture-overview)
4. [Dynamic Weight Adjustment](***REMOVED***dynamic-weight-adjustment)
5. [Integration with CP-SAT](***REMOVED***integration-with-cp-sat)
6. [Data Flow](***REMOVED***data-flow)
7. [Iterative Schedule Generation](***REMOVED***iterative-schedule-generation)
8. [Implementation Specification](***REMOVED***implementation-specification)
9. [Test Cases](***REMOVED***test-cases)
10. [References](***REMOVED***references)

---

***REMOVED******REMOVED*** Executive Summary

***REMOVED******REMOVED******REMOVED*** Problem Statement

The current scheduling engine solves the entire academic year (365 days, 730 blocks) as a single monolithic optimization problem. This approach has limitations:

- **Long solve times** for large date ranges (>60 seconds)
- **No adaptation** to changing conditions mid-schedule
- **Static weights** don't respond to system state
- **Cannot incorporate** predictions about future stress

***REMOVED******REMOVED******REMOVED*** Solution: Model Predictive Control

**Model Predictive Control (MPC)** solves scheduling as a rolling-horizon optimization:

1. **Predict** system state over 4-week horizon
2. **Optimize** constraint weights based on predicted conditions
3. **Execute** control horizon (2 weeks) of assignments
4. **Observe** actual results and update model
5. **Recalculate** for next window

**Key Benefits:**

- Faster solve times (smaller optimization windows)
- Adaptive weights respond to system state (approaching crisis → prioritize coverage)
- Explicit handling of future uncertainty
- Natural integration with resilience forecasting

***REMOVED******REMOVED******REMOVED*** Integration Approach

MPC acts as a **meta-controller** that:
- Calls `ResilienceService.get_forecast()` for predicted metrics
- Computes optimal constraint weight trajectory
- Feeds weights to existing `SchedulingEngine.generate()`
- Observes results and updates internal model

**No changes to CP-SAT solver** - MPC adjusts the weights, solver optimizes with those weights.

---

***REMOVED******REMOVED*** Mathematical Foundation

***REMOVED******REMOVED******REMOVED*** MPC Optimization Problem

At each time step $t$, MPC solves:

$$
\min_{w(t), w(t+1), \ldots, w(t+H)} \sum_{k=t}^{t+H} \left[
Q \cdot (c_k - c_{\text{target}})^2 +
R \cdot (u_k - 0.80)^2 +
S \cdot \sigma^2_k +
P \cdot p_k
\right]
$$

**Subject to:**
- ACGME constraints (hard): $h(\mathbf{x}_k) = 0$
- Faculty availability (hard): $a_f(k) \in \{0, 1\}$
- Supervision ratios (hard): $r_{\text{PGY1}} \leq 2, r_{\text{PGY2/3}} \leq 4$
- Stigmergy preferences (soft, weighted by $P$): $\text{trail\_score}_f$

**Decision Variables:**
- $w(k)$ = weight vector at time $k$
  - $w = [Q, R, S, P, \ldots]$ for each soft constraint
- $\mathbf{x}_k$ = schedule assignments at time $k$

**State Variables:**
- $c_k$ = coverage rate at time $k$
- $u_k$ = utilization rate at time $k$
- $\sigma^2_k$ = workload variance at time $k$
- $p_k$ = preference mismatch penalty at time $k$

**Horizons:**
- **Prediction Horizon ($H$):** 4 weeks (28 days, 56 blocks)
  - How far ahead MPC looks to predict future conditions
- **Control Horizon ($M$):** 2 weeks (14 days, 28 blocks)
  - How many weeks of assignments to commit and execute
  - Remaining $H - M$ weeks are discarded and re-solved next iteration

**Recalculation Frequency:**
- Every 1 week (7 days)
- After each control horizon execution, shift forward and re-solve

***REMOVED******REMOVED******REMOVED*** Objective Function Components

***REMOVED******REMOVED******REMOVED******REMOVED*** 1. Coverage Objective ($Q \cdot \text{coverage\_error}$)

Ensures all clinical blocks have adequate coverage.

$$
\text{coverage\_error}_k = (c_{\text{target}} - c_k)^2
$$

- $c_{\text{target}} = 0.95$ (95% coverage target)
- $c_k$ = actual coverage rate at time $k$
- $Q$ = coverage weight (high priority, baseline 1000.0)

**Weight Adjustment Logic:**
```python
if predicted_utilization > 0.85:
    Q_crisis = Q_base * 1.5  ***REMOVED*** Crisis mode: prioritize coverage
elif predicted_utilization < 0.70:
    Q_recovery = Q_base * 0.8  ***REMOVED*** Recovery: can relax slightly
else:
    Q_normal = Q_base
```

***REMOVED******REMOVED******REMOVED******REMOVED*** 2. Utilization Objective ($R \cdot \text{util\_error}$)

Maintains utilization near 80% threshold (queuing theory optimum).

$$
\text{util\_error}_k = (u_k - 0.80)^2
$$

- Target: 80% utilization (20% buffer for surge capacity)
- $u_k$ = faculty utilization rate at time $k$
- $R$ = utilization weight (baseline 20.0)

**Weight Adjustment Logic:**
```python
if predicted_utilization > 0.90:
    R_crisis = R_base * 2.0  ***REMOVED*** Critical: reduce load immediately
elif predicted_utilization > 0.85:
    R_warning = R_base * 1.5  ***REMOVED*** Warning: start reducing
elif predicted_utilization < 0.75:
    R_healthy = R_base * 0.8  ***REMOVED*** Healthy: can increase slightly
```

***REMOVED******REMOVED******REMOVED******REMOVED*** 3. Workload Balance Objective ($S \cdot \text{variance}$)

Ensures equitable distribution across faculty.

$$
\text{workload\_variance}_k = \text{Var}(\{w_{f,k} : f \in \text{Faculty}\})
$$

- $w_{f,k}$ = workload of faculty $f$ at time $k$
- $S$ = equity weight (baseline 10.0)

**Weight Adjustment Logic:**
```python
if max_workload - min_workload > 15:  ***REMOVED*** Large imbalance
    S_rebalance = S_base * 2.0  ***REMOVED*** Prioritize equity
else:
    S_normal = S_base
```

***REMOVED******REMOVED******REMOVED******REMOVED*** 4. Preference Objective ($P \cdot \text{stigmergy\_score}$)

Incorporates learned faculty preferences from stigmergy trails.

$$
\text{preference\_score}_k = \sum_{f \in \text{Faculty}} \sum_{b \in \text{Blocks}_k} \text{trail}_{f,b} \cdot x_{f,b}
$$

- $\text{trail}_{f,b}$ = preference trail strength (0-1) for faculty $f$ at block $b$
- $x_{f,b}$ = 1 if assigned, 0 otherwise
- $P$ = preference weight (baseline 8.0)

**Weight Adjustment Logic:**
```python
if system_status == "GREEN":
    P_normal = P_base  ***REMOVED*** Normal: honor preferences
elif system_status in ["YELLOW", "ORANGE"]:
    P_degrade = P_base * 0.5  ***REMOVED*** Stressed: preferences secondary
else:  ***REMOVED*** RED, BLACK
    P_crisis = P_base * 0.1  ***REMOVED*** Crisis: coverage only
```

---

***REMOVED******REMOVED*** Architecture Overview

***REMOVED******REMOVED******REMOVED*** Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      MPCSchedulerBridge                          │
│                                                                  │
│  ┌────────────────┐         ┌──────────────────┐               │
│  │ State Estimator│◄────────│ Resilience       │               │
│  │                │         │ Service          │               │
│  │ - Current util │         │ - Forecast 4wks  │               │
│  │ - Workload     │         │ - Predict stress │               │
│  │ - Coverage     │         │ - SPC metrics    │               │
│  └────────┬───────┘         └──────────────────┘               │
│           │                                                      │
│           ▼                                                      │
│  ┌────────────────────────────────────────┐                    │
│  │    MPC Optimizer                       │                    │
│  │                                         │                    │
│  │  Input:  predicted_metrics[0..H]       │                    │
│  │  Output: optimal_weights[0..H]         │                    │
│  │                                         │                    │
│  │  minimize: Σ[coverage² + util² + ...]  │                    │
│  └────────────────┬───────────────────────┘                    │
│                   │                                              │
│                   ▼                                              │
│  ┌─────────────────────────────────────────────┐               │
│  │  Weight Selector                            │               │
│  │  - Extract weights[0] for current step     │               │
│  │  - Adjust based on system state            │               │
│  └─────────────────┬───────────────────────────┘               │
│                    │                                             │
└────────────────────┼─────────────────────────────────────────────┘
                     │
                     ▼
        ┌────────────────────────────┐
        │   SchedulingEngine         │
        │   .generate(               │
        │       weights={            │
        │         'coverage': Q,     │
        │         'utilization': R,  │
        │         'equity': S,       │
        │         'preference': P    │
        │       }                    │
        │   )                        │
        └────────────┬───────────────┘
                     │
                     ▼
        ┌────────────────────────────┐
        │   CP-SAT Solver            │
        │   - Hard constraints       │
        │   - Soft constraints       │
        │   - Objective: Σ w_i·c_i  │
        └────────────┬───────────────┘
                     │
                     ▼
              [Assignments]
                     │
                     ▼
        ┌────────────────────────────┐
        │  MPCSchedulerBridge        │
        │  .observe_result()         │
        │  - Update state estimator  │
        │  - Calculate actual metrics│
        │  - Feed to next iteration  │
        └────────────────────────────┘
```

***REMOVED******REMOVED******REMOVED*** Class Hierarchy

```
MPCSchedulerBridge
├── StateEstimator
│   ├── current_utilization: float
│   ├── current_coverage: float
│   ├── current_workload_variance: float
│   └── estimate_state(assignments) -> StateVector
│
├── MPCOptimizer
│   ├── prediction_horizon: int = 4 weeks
│   ├── control_horizon: int = 2 weeks
│   ├── optimize_weights(predicted_metrics) -> WeightTrajectory
│   └── solve_quadratic_program() -> optimal_weights
│
├── WeightScheduler
│   ├── get_weights_for_step(k) -> dict
│   ├── adjust_for_crisis(weights, state) -> dict
│   └── validate_weight_bounds(weights) -> bool
│
└── ResultObserver
    ├── observe(assignments, actual_metrics)
    ├── update_model(prediction_error)
    └── calculate_mpc_performance() -> dict
```

---

***REMOVED******REMOVED*** Dynamic Weight Adjustment

***REMOVED******REMOVED******REMOVED*** Weight Adjustment State Machine

```
System State       Coverage (Q)  Utilization (R)  Equity (S)  Preference (P)
────────────────   ────────────  ───────────────  ──────────  ──────────────
GREEN (util≤75%)      1000          20.0            10.0         8.0
YELLOW (75-80%)       1200          25.0            10.0         6.0
ORANGE (80-85%)       1500          40.0             8.0         4.0
RED (85-90%)          2000          60.0             5.0         2.0
BLACK (>90%)          3000         100.0             3.0         0.5
```

**Transitions:**
- `predicted_utilization` from `ResilienceService.get_forecast(weeks=4)`
- Weights update **before** each MPC iteration
- Smooth transitions using exponential moving average (EMA) to prevent oscillation

***REMOVED******REMOVED******REMOVED*** Weight Update Algorithm

```python
def calculate_dynamic_weights(
    predicted_metrics: dict,
    base_weights: dict,
    system_state: str
) -> dict:
    """
    Calculate dynamic constraint weights based on predicted system state.

    Args:
        predicted_metrics: Forecast from ResilienceService
            {
                'utilization_trajectory': [0.78, 0.81, 0.83, 0.85],
                'coverage_trajectory': [0.95, 0.94, 0.93, 0.92],
                'n1_vulnerable_count': 2,
                'burnout_risk': 0.15
            }
        base_weights: Baseline weights from ConstraintManager
            {
                'coverage': 1000.0,
                'utilization_buffer': 20.0,
                'equity': 10.0,
                'preference': 8.0,
                'hub_protection': 15.0,
                'n1_vulnerability': 25.0
            }
        system_state: Current resilience level ("GREEN", "YELLOW", ...)

    Returns:
        Adjusted weights for this MPC iteration
    """
    weights = base_weights.copy()

    ***REMOVED*** Extract prediction at end of horizon (worst-case planning)
    util_peak = max(predicted_metrics['utilization_trajectory'])
    coverage_min = min(predicted_metrics['coverage_trajectory'])

    ***REMOVED*** === COVERAGE WEIGHT ADJUSTMENT ===
    if coverage_min < 0.90:
        ***REMOVED*** Coverage crisis: drastically increase coverage priority
        weights['coverage'] *= 2.0
    elif coverage_min < 0.93:
        weights['coverage'] *= 1.5

    ***REMOVED*** === UTILIZATION WEIGHT ADJUSTMENT ===
    if util_peak > 0.90:
        ***REMOVED*** Critical overload: emergency reduction
        weights['utilization_buffer'] *= 3.0
    elif util_peak > 0.85:
        ***REMOVED*** Approaching threshold: increase urgency
        weights['utilization_buffer'] *= 2.0
    elif util_peak > 0.80:
        ***REMOVED*** Warning zone: moderate increase
        weights['utilization_buffer'] *= 1.5
    elif util_peak < 0.70:
        ***REMOVED*** Underutilized: can reduce this weight
        weights['utilization_buffer'] *= 0.8

    ***REMOVED*** === EQUITY WEIGHT ADJUSTMENT ===
    ***REMOVED*** During crisis, accept more imbalance to maintain coverage
    if system_state in ["RED", "BLACK"]:
        weights['equity'] *= 0.5
    elif system_state == "ORANGE":
        weights['equity'] *= 0.75
    ***REMOVED*** During recovery, prioritize rebalancing
    elif system_state == "GREEN" and util_peak < 0.75:
        weights['equity'] *= 1.5

    ***REMOVED*** === PREFERENCE WEIGHT ADJUSTMENT ===
    ***REMOVED*** Preferences are a luxury - deprioritize during stress
    if system_state == "BLACK":
        weights['preference'] *= 0.1  ***REMOVED*** Almost ignore
    elif system_state == "RED":
        weights['preference'] *= 0.25
    elif system_state == "ORANGE":
        weights['preference'] *= 0.5
    elif system_state == "GREEN":
        weights['preference'] *= 1.0  ***REMOVED*** Full weight when healthy

    ***REMOVED*** === RESILIENCE CONSTRAINT ADJUSTMENT ===
    ***REMOVED*** N-1 vulnerability more important as we approach crisis
    if predicted_metrics.get('n1_vulnerable_count', 0) > 0:
        weights['n1_vulnerability'] *= 1.5

    ***REMOVED*** Hub protection increases if we're approaching overload
    if util_peak > 0.80:
        weights['hub_protection'] *= 1.5

    ***REMOVED*** === SMOOTHING (Prevent Oscillation) ===
    ***REMOVED*** Use exponential moving average with previous weights
    if hasattr(calculate_dynamic_weights, '_prev_weights'):
        alpha = 0.3  ***REMOVED*** Smoothing factor
        prev = calculate_dynamic_weights._prev_weights
        for key in weights:
            weights[key] = alpha * weights[key] + (1 - alpha) * prev.get(key, weights[key])

    ***REMOVED*** Store for next iteration
    calculate_dynamic_weights._prev_weights = weights.copy()

    return weights
```

***REMOVED******REMOVED******REMOVED*** Crisis Mode Logic

When `ResilienceService` detects impending crisis (predicted utilization > 85%):

1. **Activate Crisis Weights:**
   - Coverage: 3000 (3× baseline)
   - Utilization Buffer: 100 (5× baseline)
   - Equity: 3.0 (0.3× baseline)
   - Preference: 0.5 (0.06× baseline)

2. **Enable Additional Constraints:**
   ```python
   if predicted_utilization > 0.85:
       constraint_manager.enable("N1Vulnerability")
       constraint_manager.enable("HubProtection")
       constraint_manager.enable("UtilizationBuffer")
   ```

3. **Tighten Constraint Parameters:**
   ```python
   UtilizationBufferConstraint.target_utilization = 0.75  ***REMOVED*** Reduce from 0.80
   ```

---

***REMOVED******REMOVED*** Integration with CP-SAT

***REMOVED******REMOVED******REMOVED*** Current CP-SAT Objective Function

The existing CP-SAT solver in `backend/app/scheduling/solvers.py` builds an objective:

```python
***REMOVED*** Simplified from actual code
objective_terms = []

***REMOVED*** Coverage (maximize assignments)
objective_terms.append(coverage_weight * sum(assignment_vars))

***REMOVED*** Equity (minimize variance)
objective_terms.append(equity_weight * workload_variance_penalty)

***REMOVED*** Continuity (prefer stable assignments)
objective_terms.append(continuity_weight * continuity_bonus)

model.Maximize(sum(objective_terms))
```

***REMOVED******REMOVED******REMOVED*** MPC Integration Point

**Current State:**
```python
***REMOVED*** In solvers.py CPSATSolver.solve()
def solve(self, context: SchedulingContext) -> SolverResult:
    ***REMOVED*** Weights are hardcoded or from ConstraintManager defaults
    coverage_weight = 1000.0
    equity_weight = 10.0
    ***REMOVED*** ...
```

**MPC-Enhanced:**
```python
***REMOVED*** In solvers.py CPSATSolver.solve()
def solve(
    self,
    context: SchedulingContext,
    dynamic_weights: dict | None = None  ***REMOVED*** NEW PARAMETER
) -> SolverResult:
    ***REMOVED*** Use MPC-provided weights if available
    if dynamic_weights:
        coverage_weight = dynamic_weights.get('coverage', 1000.0)
        equity_weight = dynamic_weights.get('equity', 10.0)
        ***REMOVED*** ...
    else:
        ***REMOVED*** Fall back to defaults
        coverage_weight = 1000.0
        equity_weight = 10.0

    ***REMOVED*** Rest of solver logic unchanged
```

**No solver algorithm changes** - just parameterized weights.

---

***REMOVED******REMOVED*** Data Flow

***REMOVED******REMOVED******REMOVED*** End-to-End Data Flow Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                    Iteration k (Week k)                           │
└──────────────────────────────────────────────────────────────────┘

INPUT: current_date, previous_assignments

    │
    ▼
┌──────────────────────────────────────────┐
│ 1. ResilienceService.get_forecast()      │
│    Input: current_date, horizon=4 weeks  │
│    Output:                               │
│      - utilization_trajectory[4]         │
│      - coverage_trajectory[4]            │
│      - burnout_risk_trajectory[4]        │
│      - n1_vulnerable_count               │
└──────────────┬───────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────┐
│ 2. MPCSchedulerBridge                    │
│    .optimize_weights(predicted_metrics)  │
│                                          │
│    Algorithm:                            │
│    a) Determine system_state from util  │
│    b) Apply weight adjustment rules     │
│    c) Smooth with EMA                   │
│    d) Validate bounds                   │
│                                          │
│    Output: optimal_weights[0]           │
│      {                                   │
│        'coverage': 1200.0,              │
│        'utilization_buffer': 30.0,      │
│        'equity': 8.0,                   │
│        'preference': 6.0                │
│      }                                   │
└──────────────┬───────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────┐
│ 3. SchedulingEngine.generate()           │
│    Input:                                │
│      - start_date = current_date         │
│      - end_date = current_date + 2 weeks │
│      - algorithm = 'cp_sat'              │
│      - dynamic_weights = optimal_weights │
│                                          │
│    Calls: CPSATSolver.solve(weights)    │
└──────────────┬───────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────┐
│ 4. CP-SAT Solver                         │
│    Builds objective:                     │
│      max: 1200·coverage                  │
│           + 30·util_buffer              │
│           + 8·equity                    │
│           + 6·preference                │
│                                          │
│    Subject to ACGME hard constraints    │
│                                          │
│    Output: assignments[14 days]         │
└──────────────┬───────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────┐
│ 5. MPCSchedulerBridge.observe_result()  │
│    Input: assignments, actual_metrics   │
│                                          │
│    Actions:                              │
│    a) Calculate actual utilization      │
│    b) Compare to prediction             │
│    c) Update state estimator            │
│    d) Log MPC performance metrics       │
└──────────────┬───────────────────────────┘
               │
               ▼
    current_date += 1 week
    REPEAT (next iteration k+1)
```

***REMOVED******REMOVED******REMOVED*** State Transition

```
State at time k:
  S(k) = {
    current_assignments: [Assignment],
    faculty_utilization: {faculty_id: float},
    coverage_rate: float,
    workload_variance: float,
    system_status: "GREEN" | "YELLOW" | ...
  }

Control input u(k):
  u(k) = {
    coverage_weight: float,
    utilization_weight: float,
    equity_weight: float,
    preference_weight: float
  }

State transition:
  S(k+1) = f(S(k), u(k), assignments_generated)

Where f():
  - Executes solver with weights u(k)
  - Generates assignments for control horizon
  - Updates utilization, coverage from assignments
  - Calculates new system_status
```

---

***REMOVED******REMOVED*** Iterative Schedule Generation

***REMOVED******REMOVED******REMOVED*** Algorithm: Rolling Horizon MPC

```python
def generate_schedule_with_mpc(
    start_date: date,
    end_date: date,
    prediction_horizon_weeks: int = 4,
    control_horizon_weeks: int = 2,
) -> list[Assignment]:
    """
    Generate complete schedule using Model Predictive Control.

    Instead of solving entire year at once, solve in 2-week increments
    with 4-week lookahead.

    Args:
        start_date: Academic year start (e.g., 2024-07-01)
        end_date: Academic year end (e.g., 2025-06-30)
        prediction_horizon_weeks: How far ahead to predict (4 weeks)
        control_horizon_weeks: How many weeks to commit (2 weeks)

    Returns:
        Complete year schedule as list of Assignment objects
    """
    mpc_bridge = MPCSchedulerBridge(
        resilience_service=ResilienceService(db=db),
        constraint_manager=ConstraintManager.create_default(),
    )

    all_assignments = []
    current_date = start_date
    iteration = 0

    while current_date < end_date:
        logger.info(f"MPC Iteration {iteration}: {current_date}")

        ***REMOVED*** ═══════════════════════════════════════════════════════
        ***REMOVED*** STEP 1: PREDICTION
        ***REMOVED*** ═══════════════════════════════════════════════════════
        prediction_end = min(
            current_date + timedelta(weeks=prediction_horizon_weeks),
            end_date
        )

        predicted_metrics = resilience_service.get_forecast(
            start_date=current_date,
            end_date=prediction_end,
            current_assignments=all_assignments,
        )
        ***REMOVED*** predicted_metrics = {
        ***REMOVED***     'utilization_trajectory': [0.78, 0.80, 0.82, 0.84],
        ***REMOVED***     'coverage_trajectory': [0.95, 0.94, 0.94, 0.93],
        ***REMOVED***     'burnout_risk_trajectory': [0.10, 0.12, 0.15, 0.18],
        ***REMOVED*** }

        ***REMOVED*** ═══════════════════════════════════════════════════════
        ***REMOVED*** STEP 2: WEIGHT OPTIMIZATION
        ***REMOVED*** ═══════════════════════════════════════════════════════
        optimal_weights = mpc_bridge.optimize_weights(
            predicted_metrics=predicted_metrics,
            current_state=mpc_bridge.state_estimator.current_state,
        )
        ***REMOVED*** optimal_weights = {
        ***REMOVED***     'coverage': 1200.0,
        ***REMOVED***     'utilization_buffer': 30.0,
        ***REMOVED***     'equity': 8.0,
        ***REMOVED***     'preference': 6.0,
        ***REMOVED***     'hub_protection': 15.0,
        ***REMOVED*** }

        logger.debug(f"Optimal weights: {optimal_weights}")

        ***REMOVED*** ═══════════════════════════════════════════════════════
        ***REMOVED*** STEP 3: SOLVE FOR CONTROL HORIZON
        ***REMOVED*** ═══════════════════════════════════════════════════════
        control_end = min(
            current_date + timedelta(weeks=control_horizon_weeks),
            end_date
        )

        ***REMOVED*** Call existing SchedulingEngine with dynamic weights
        engine = SchedulingEngine(
            db=db,
            start_date=current_date,
            end_date=control_end,
        )

        result = engine.generate(
            algorithm='cp_sat',
            timeout_seconds=30.0,  ***REMOVED*** Fast solve for MPC
            dynamic_weights=optimal_weights,  ***REMOVED*** NEW: Pass MPC weights
            preserve_fmit=True,
            preserve_resident_inpatient=True,
        )

        control_assignments = result['assignments']

        logger.info(
            f"Generated {len(control_assignments)} assignments "
            f"for {current_date} to {control_end}"
        )

        ***REMOVED*** ═══════════════════════════════════════════════════════
        ***REMOVED*** STEP 4: OBSERVE RESULT
        ***REMOVED*** ═══════════════════════════════════════════════════════
        actual_metrics = calculate_actual_metrics(control_assignments)

        mpc_bridge.observe_result(
            assignments=control_assignments,
            predicted_metrics=predicted_metrics,
            actual_metrics=actual_metrics,
        )

        ***REMOVED*** Update prediction error for model learning
        prediction_error = {
            'utilization_error': (
                actual_metrics['utilization'] -
                predicted_metrics['utilization_trajectory'][0]
            ),
            'coverage_error': (
                actual_metrics['coverage'] -
                predicted_metrics['coverage_trajectory'][0]
            ),
        }

        logger.debug(f"Prediction error: {prediction_error}")

        ***REMOVED*** ═══════════════════════════════════════════════════════
        ***REMOVED*** STEP 5: COMMIT AND ADVANCE
        ***REMOVED*** ═══════════════════════════════════════════════════════
        all_assignments.extend(control_assignments)
        db.commit()  ***REMOVED*** Persist this batch

        ***REMOVED*** Move horizon forward by control_horizon_weeks
        current_date = control_end
        iteration += 1

        ***REMOVED*** Save checkpoint every 4 weeks
        if iteration % 2 == 0:
            save_mpc_checkpoint(
                iteration=iteration,
                date=current_date,
                assignments=all_assignments,
                weights=optimal_weights,
            )

    logger.info(
        f"MPC schedule generation complete: {len(all_assignments)} "
        f"total assignments over {iteration} iterations"
    )

    return all_assignments


def calculate_actual_metrics(assignments: list[Assignment]) -> dict:
    """Calculate actual metrics from generated assignments."""
    ***REMOVED*** Count assignments per faculty
    faculty_workloads = defaultdict(int)
    for a in assignments:
        faculty_workloads[a.person_id] += 1

    ***REMOVED*** Calculate utilization
    total_assigned = len(assignments)
    total_capacity = len(faculty_workloads) * (len(assignments) / len(faculty_workloads))
    utilization = total_assigned / total_capacity if total_capacity > 0 else 0

    ***REMOVED*** Calculate coverage
    blocks_covered = len(set(a.block_id for a in assignments))
    total_blocks = len(assignments)  ***REMOVED*** Simplified
    coverage = blocks_covered / total_blocks if total_blocks > 0 else 0

    ***REMOVED*** Calculate workload variance
    workload_variance = (
        statistics.variance(faculty_workloads.values())
        if len(faculty_workloads) > 1 else 0
    )

    return {
        'utilization': utilization,
        'coverage': coverage,
        'workload_variance': workload_variance,
    }
```

***REMOVED******REMOVED******REMOVED*** Pseudocode Flow

```
ALGORITHM: MPC_Schedule_Generation
INPUT: start_date, end_date, H=4 weeks, M=2 weeks
OUTPUT: complete_schedule

1. INITIALIZE
   current_date ← start_date
   all_assignments ← []
   state ← initial_state()

2. WHILE current_date < end_date:

   a) PREDICT (Forecast H weeks ahead)
      horizon_end ← current_date + H weeks
      predicted_metrics ← resilience.forecast(current_date, horizon_end)

   b) OPTIMIZE WEIGHTS (Solve MPC problem)
      weights ← solve_mpc_optimization(
          predicted_metrics,
          current_state,
          objective_weights=[Q, R, S, P]
      )

   c) EXECUTE (Solve CP-SAT for M weeks)
      control_end ← current_date + M weeks
      assignments ← cpsat_solve(
          current_date,
          control_end,
          weights=weights
      )

   d) OBSERVE (Update state with actual results)
      actual_metrics ← compute_metrics(assignments)
      state ← update_state(state, assignments, actual_metrics)
      prediction_error ← actual - predicted

   e) COMMIT
      all_assignments ← all_assignments ∪ assignments
      db.commit()

   f) ADVANCE HORIZON
      current_date ← control_end

3. RETURN all_assignments
```

---

***REMOVED******REMOVED*** Implementation Specification

***REMOVED******REMOVED******REMOVED*** File Structure

```
backend/app/scheduling/
├── mpc/
│   ├── __init__.py
│   ├── bridge.py              ***REMOVED*** MPCSchedulerBridge class
│   ├── state_estimator.py     ***REMOVED*** State estimation from assignments
│   ├── weight_optimizer.py    ***REMOVED*** MPC weight optimization logic
│   └── observer.py             ***REMOVED*** Result observation and model update
│
├── engine.py                   ***REMOVED*** MODIFY: Add dynamic_weights parameter
├── solvers.py                  ***REMOVED*** MODIFY: Accept weights in solve()
└── constraints/
    └── manager.py              ***REMOVED*** MODIFY: get_weights() method
```

***REMOVED******REMOVED******REMOVED*** Class: MPCSchedulerBridge

```python
"""
MPC-Scheduler Bridge for adaptive schedule generation.

File: backend/app/scheduling/mpc/bridge.py
"""

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any
from uuid import UUID

from app.resilience.service import ResilienceService
from app.scheduling.constraints import ConstraintManager
from app.scheduling.engine import SchedulingEngine


@dataclass
class MPCConfig:
    """Configuration for MPC scheduler."""

    prediction_horizon_weeks: int = 4
    control_horizon_weeks: int = 2
    recalculation_frequency_days: int = 7

    ***REMOVED*** Base weights (will be adjusted dynamically)
    base_weights: dict[str, float] = None

    ***REMOVED*** Weight adjustment parameters
    crisis_multiplier: float = 2.0
    smoothing_alpha: float = 0.3  ***REMOVED*** EMA smoothing factor

    def __post_init__(self):
        if self.base_weights is None:
            self.base_weights = {
                'coverage': 1000.0,
                'utilization_buffer': 20.0,
                'equity': 10.0,
                'continuity': 5.0,
                'preference': 8.0,
                'hub_protection': 15.0,
                'n1_vulnerability': 25.0,
            }


@dataclass
class StateVector:
    """Current system state for MPC."""

    utilization: float
    coverage: float
    workload_variance: float
    system_status: str  ***REMOVED*** "GREEN", "YELLOW", "ORANGE", "RED", "BLACK"
    n1_vulnerable_count: int
    burnout_risk: float


class MPCSchedulerBridge:
    """
    Bridge between MPC control theory and scheduling engine.

    Implements Model Predictive Control for adaptive schedule generation:
    1. Forecasts system state over prediction horizon
    2. Optimizes constraint weights based on forecast
    3. Executes control horizon with optimal weights
    4. Observes results and updates model

    Usage:
        bridge = MPCSchedulerBridge(resilience_service, constraint_manager)
        schedule = bridge.generate_schedule(start_date, end_date)
    """

    def __init__(
        self,
        resilience_service: ResilienceService,
        constraint_manager: ConstraintManager,
        config: MPCConfig | None = None,
    ):
        self.resilience = resilience_service
        self.constraints = constraint_manager
        self.config = config or MPCConfig()

        ***REMOVED*** State tracking
        self.current_state: StateVector | None = None
        self.weight_history: list[dict] = []
        self.prediction_errors: list[dict] = []

        ***REMOVED*** Smoothing state
        self._previous_weights: dict[str, float] | None = None

    def generate_schedule(
        self,
        db: Any,
        start_date: date,
        end_date: date,
    ) -> list[Any]:
        """
        Generate schedule using MPC rolling horizon.

        See algorithm documentation in docstring at top of file.
        """
        all_assignments = []
        current_date = start_date
        iteration = 0

        while current_date < end_date:
            ***REMOVED*** 1. Predict
            predicted_metrics = self._forecast_horizon(
                current_date,
                all_assignments
            )

            ***REMOVED*** 2. Optimize weights
            optimal_weights = self.optimize_weights(
                predicted_metrics=predicted_metrics,
                current_state=self.current_state,
            )

            ***REMOVED*** 3. Execute control horizon
            control_end = min(
                current_date + timedelta(weeks=self.config.control_horizon_weeks),
                end_date
            )

            engine = SchedulingEngine(
                db=db,
                start_date=current_date,
                end_date=control_end,
                constraint_manager=self.constraints,
            )

            result = engine.generate(
                algorithm='cp_sat',
                timeout_seconds=30.0,
                dynamic_weights=optimal_weights,
            )

            control_assignments = result.get('assignments', [])

            ***REMOVED*** 4. Observe
            actual_metrics = self._calculate_actual_metrics(control_assignments)
            self.observe_result(
                assignments=control_assignments,
                predicted_metrics=predicted_metrics,
                actual_metrics=actual_metrics,
            )

            ***REMOVED*** 5. Commit and advance
            all_assignments.extend(control_assignments)
            current_date = control_end
            iteration += 1

        return all_assignments

    def optimize_weights(
        self,
        predicted_metrics: dict,
        current_state: StateVector | None,
    ) -> dict[str, float]:
        """
        Optimize constraint weights based on predicted system state.

        Implements dynamic weight adjustment logic described in
        "Dynamic Weight Adjustment" section.
        """
        weights = self.config.base_weights.copy()

        ***REMOVED*** Extract predictions
        util_trajectory = predicted_metrics.get('utilization_trajectory', [0.75])
        coverage_trajectory = predicted_metrics.get('coverage_trajectory', [0.95])

        util_peak = max(util_trajectory)
        coverage_min = min(coverage_trajectory)

        ***REMOVED*** Determine system state
        if util_peak > 0.90:
            system_state = "BLACK"
        elif util_peak > 0.85:
            system_state = "RED"
        elif util_peak > 0.80:
            system_state = "ORANGE"
        elif util_peak > 0.75:
            system_state = "YELLOW"
        else:
            system_state = "GREEN"

        ***REMOVED*** Apply adjustment rules
        weights = self._apply_weight_adjustments(
            weights=weights,
            util_peak=util_peak,
            coverage_min=coverage_min,
            system_state=system_state,
            predicted_metrics=predicted_metrics,
        )

        ***REMOVED*** Smooth with EMA
        if self._previous_weights:
            alpha = self.config.smoothing_alpha
            weights = {
                key: alpha * weights[key] + (1 - alpha) * self._previous_weights.get(key, weights[key])
                for key in weights
            }

        self._previous_weights = weights.copy()
        self.weight_history.append({
            'weights': weights.copy(),
            'system_state': system_state,
            'util_peak': util_peak,
        })

        return weights

    def _apply_weight_adjustments(
        self,
        weights: dict,
        util_peak: float,
        coverage_min: float,
        system_state: str,
        predicted_metrics: dict,
    ) -> dict:
        """Apply weight adjustment rules based on predicted state."""
        ***REMOVED*** Coverage adjustments
        if coverage_min < 0.90:
            weights['coverage'] *= 2.0
        elif coverage_min < 0.93:
            weights['coverage'] *= 1.5

        ***REMOVED*** Utilization adjustments
        if util_peak > 0.90:
            weights['utilization_buffer'] *= 3.0
        elif util_peak > 0.85:
            weights['utilization_buffer'] *= 2.0
        elif util_peak > 0.80:
            weights['utilization_buffer'] *= 1.5
        elif util_peak < 0.70:
            weights['utilization_buffer'] *= 0.8

        ***REMOVED*** Equity adjustments
        if system_state in ["RED", "BLACK"]:
            weights['equity'] *= 0.5
        elif system_state == "ORANGE":
            weights['equity'] *= 0.75
        elif system_state == "GREEN" and util_peak < 0.75:
            weights['equity'] *= 1.5

        ***REMOVED*** Preference adjustments
        preference_multipliers = {
            "BLACK": 0.1,
            "RED": 0.25,
            "ORANGE": 0.5,
            "YELLOW": 0.75,
            "GREEN": 1.0,
        }
        weights['preference'] *= preference_multipliers.get(system_state, 1.0)

        ***REMOVED*** Resilience constraint adjustments
        if predicted_metrics.get('n1_vulnerable_count', 0) > 0:
            weights['n1_vulnerability'] *= 1.5

        if util_peak > 0.80:
            weights['hub_protection'] *= 1.5

        return weights

    def observe_result(
        self,
        assignments: list,
        predicted_metrics: dict,
        actual_metrics: dict,
    ):
        """Observe actual results and update state estimator."""
        ***REMOVED*** Calculate prediction error
        prediction_error = {
            'utilization_error': (
                actual_metrics['utilization'] -
                predicted_metrics['utilization_trajectory'][0]
            ),
            'coverage_error': (
                actual_metrics['coverage'] -
                predicted_metrics['coverage_trajectory'][0]
            ),
        }

        self.prediction_errors.append(prediction_error)

        ***REMOVED*** Update current state
        self.current_state = StateVector(
            utilization=actual_metrics['utilization'],
            coverage=actual_metrics['coverage'],
            workload_variance=actual_metrics.get('workload_variance', 0.0),
            system_status=self._determine_status(actual_metrics['utilization']),
            n1_vulnerable_count=actual_metrics.get('n1_vulnerable_count', 0),
            burnout_risk=actual_metrics.get('burnout_risk', 0.0),
        )

    def _forecast_horizon(
        self,
        current_date: date,
        existing_assignments: list,
    ) -> dict:
        """Forecast system state over prediction horizon."""
        horizon_end = current_date + timedelta(
            weeks=self.config.prediction_horizon_weeks
        )

        return self.resilience.get_forecast(
            start_date=current_date,
            end_date=horizon_end,
            current_assignments=existing_assignments,
        )

    def _calculate_actual_metrics(self, assignments: list) -> dict:
        """Calculate actual metrics from assignments."""
        ***REMOVED*** Implementation from generate_schedule_with_mpc example
        from collections import defaultdict
        import statistics

        faculty_workloads = defaultdict(int)
        for a in assignments:
            faculty_workloads[a.person_id] += 1

        total_assigned = len(assignments)
        total_capacity = (
            len(faculty_workloads) * (len(assignments) / len(faculty_workloads))
            if faculty_workloads else 1
        )
        utilization = total_assigned / total_capacity if total_capacity > 0 else 0

        blocks_covered = len(set(a.block_id for a in assignments))
        total_blocks = len(assignments)
        coverage = blocks_covered / total_blocks if total_blocks > 0 else 0

        workload_variance = (
            statistics.variance(faculty_workloads.values())
            if len(faculty_workloads) > 1 else 0
        )

        return {
            'utilization': utilization,
            'coverage': coverage,
            'workload_variance': workload_variance,
        }

    def _determine_status(self, utilization: float) -> str:
        """Determine system status from utilization."""
        if utilization > 0.90:
            return "BLACK"
        elif utilization > 0.85:
            return "RED"
        elif utilization > 0.80:
            return "ORANGE"
        elif utilization > 0.75:
            return "YELLOW"
        else:
            return "GREEN"

    def get_mpc_performance_report(self) -> dict:
        """Generate MPC performance metrics."""
        if not self.prediction_errors:
            return {}

        util_errors = [e['utilization_error'] for e in self.prediction_errors]
        coverage_errors = [e['coverage_error'] for e in self.prediction_errors]

        import statistics

        return {
            'total_iterations': len(self.weight_history),
            'mean_utilization_error': statistics.mean(util_errors),
            'mean_coverage_error': statistics.mean(coverage_errors),
            'weight_adjustments': len([
                w for w in self.weight_history
                if w['system_state'] != "GREEN"
            ]),
            'crisis_iterations': len([
                w for w in self.weight_history
                if w['system_state'] in ["RED", "BLACK"]
            ]),
        }
```

***REMOVED******REMOVED******REMOVED*** Modifications to Existing Files

***REMOVED******REMOVED******REMOVED******REMOVED*** engine.py

```python
***REMOVED*** In SchedulingEngine.generate()
def generate(
    self,
    pgy_levels: list[int] | None = None,
    rotation_template_ids: list[UUID] | None = None,
    algorithm: str = "greedy",
    timeout_seconds: float = 60.0,
    check_resilience: bool = True,
    preserve_fmit: bool = True,
    preserve_resident_inpatient: bool = True,
    preserve_absence: bool = True,
    dynamic_weights: dict[str, float] | None = None,  ***REMOVED*** NEW PARAMETER
) -> dict:
    """
    Generate a complete schedule.

    Args:
        ... (existing args)
        dynamic_weights: Optional MPC-provided constraint weights.
                        If provided, overrides ConstraintManager defaults.
                        Format: {'coverage': 1200.0, 'equity': 8.0, ...}
    """
    ***REMOVED*** Existing code...

    ***REMOVED*** Step 5: Run solver
    solver_result = self._run_solver(
        algorithm,
        context,
        timeout_seconds,
        dynamic_weights=dynamic_weights  ***REMOVED*** Pass through
    )
```

***REMOVED******REMOVED******REMOVED******REMOVED*** solvers.py

```python
***REMOVED*** In CPSATSolver.solve()
def solve(
    self,
    context: SchedulingContext,
    immutable_assignments: list[Assignment] | None = None,
    dynamic_weights: dict[str, float] | None = None,  ***REMOVED*** NEW PARAMETER
) -> SolverResult:
    """
    Solve using Google OR-Tools CP-SAT solver.

    Args:
        ... (existing args)
        dynamic_weights: Optional weight overrides from MPC.
                        If provided, uses these instead of constraint manager weights.
    """
    ***REMOVED*** Build objective function
    objective_terms = []

    ***REMOVED*** Get weights (use dynamic if provided, else constraint manager)
    if dynamic_weights:
        coverage_weight = dynamic_weights.get('coverage', 1000.0)
        equity_weight = dynamic_weights.get('equity', 10.0)
        ***REMOVED*** ... etc
    else:
        ***REMOVED*** Extract from constraint manager (existing logic)
        soft_constraints = self.constraint_manager.get_soft_constraints()
        coverage_weight = next(
            (c.weight for c in soft_constraints if c.name == "Coverage"),
            1000.0
        )
        ***REMOVED*** ... etc

    ***REMOVED*** Rest of solver logic unchanged
```

---

***REMOVED******REMOVED*** Test Cases

***REMOVED******REMOVED******REMOVED*** Unit Tests

***REMOVED******REMOVED******REMOVED******REMOVED*** 1. Weight Adjustment Logic

```python
def test_weight_adjustment_crisis_mode():
    """Test that weights adjust correctly during predicted crisis."""
    bridge = MPCSchedulerBridge(
        resilience_service=mock_resilience,
        constraint_manager=ConstraintManager.create_default(),
    )

    ***REMOVED*** Simulate predicted crisis (utilization approaching 90%)
    predicted_metrics = {
        'utilization_trajectory': [0.82, 0.85, 0.88, 0.91],
        'coverage_trajectory': [0.95, 0.94, 0.93, 0.92],
    }

    weights = bridge.optimize_weights(
        predicted_metrics=predicted_metrics,
        current_state=None,
    )

    ***REMOVED*** Coverage should increase (crisis response)
    assert weights['coverage'] > 1000.0, "Coverage weight should increase in crisis"

    ***REMOVED*** Utilization buffer should increase significantly
    assert weights['utilization_buffer'] > 40.0, "Util buffer should increase"

    ***REMOVED*** Equity should decrease (sacrifice for coverage)
    assert weights['equity'] < 10.0, "Equity should decrease in crisis"

    ***REMOVED*** Preference should decrease drastically
    assert weights['preference'] < 4.0, "Preferences deprioritized in crisis"


def test_weight_adjustment_recovery_mode():
    """Test that weights adjust for recovery when utilization is healthy."""
    bridge = MPCSchedulerBridge(
        resilience_service=mock_resilience,
        constraint_manager=ConstraintManager.create_default(),
    )

    ***REMOVED*** Simulate healthy state (utilization 70%)
    predicted_metrics = {
        'utilization_trajectory': [0.70, 0.71, 0.72, 0.73],
        'coverage_trajectory': [0.95, 0.95, 0.96, 0.96],
    }

    weights = bridge.optimize_weights(
        predicted_metrics=predicted_metrics,
        current_state=None,
    )

    ***REMOVED*** Equity should increase (rebalance during recovery)
    assert weights['equity'] >= 10.0, "Equity should be prioritized in recovery"

    ***REMOVED*** Preference should be full weight
    assert weights['preference'] >= 8.0, "Preferences honored when healthy"

    ***REMOVED*** Utilization buffer can relax slightly
    assert weights['utilization_buffer'] <= 20.0


def test_weight_smoothing_prevents_oscillation():
    """Test that EMA smoothing prevents rapid weight changes."""
    bridge = MPCSchedulerBridge(
        resilience_service=mock_resilience,
        constraint_manager=ConstraintManager.create_default(),
        config=MPCConfig(smoothing_alpha=0.3),
    )

    ***REMOVED*** First iteration: normal state
    weights_1 = bridge.optimize_weights(
        predicted_metrics={'utilization_trajectory': [0.75], 'coverage_trajectory': [0.95]},
        current_state=None,
    )

    ***REMOVED*** Second iteration: sudden spike (should be smoothed)
    weights_2 = bridge.optimize_weights(
        predicted_metrics={'utilization_trajectory': [0.90], 'coverage_trajectory': [0.95]},
        current_state=None,
    )

    ***REMOVED*** Third iteration: back to normal
    weights_3 = bridge.optimize_weights(
        predicted_metrics={'utilization_trajectory': [0.75], 'coverage_trajectory': [0.95]},
        current_state=None,
    )

    ***REMOVED*** Weights should not change dramatically between iterations
    delta_1_2 = abs(weights_2['utilization_buffer'] - weights_1['utilization_buffer'])
    delta_2_3 = abs(weights_3['utilization_buffer'] - weights_2['utilization_buffer'])

    ***REMOVED*** With smoothing, changes should be moderated
    assert delta_1_2 < 50.0, "Smoothing should prevent drastic changes"
    assert delta_2_3 < 50.0, "Smoothing should prevent drastic changes"
```

***REMOVED******REMOVED******REMOVED******REMOVED*** 2. MPC Iteration Logic

```python
def test_mpc_generates_control_horizon_only():
    """Test that MPC only commits control horizon, discards rest."""
    bridge = MPCSchedulerBridge(
        resilience_service=mock_resilience,
        constraint_manager=ConstraintManager.create_default(),
        config=MPCConfig(
            prediction_horizon_weeks=4,
            control_horizon_weeks=2,
        ),
    )

    start_date = date(2024, 7, 1)
    control_end = date(2024, 7, 15)  ***REMOVED*** 2 weeks

    ***REMOVED*** Mock engine that would generate 4 weeks if asked
    mock_engine = Mock(spec=SchedulingEngine)
    mock_engine.generate.return_value = {
        'assignments': [
            Mock(block=Mock(date=date(2024, 7, 5))),  ***REMOVED*** Week 1 - should keep
            Mock(block=Mock(date=date(2024, 7, 12))), ***REMOVED*** Week 2 - should keep
            Mock(block=Mock(date=date(2024, 7, 19))), ***REMOVED*** Week 3 - should discard
            Mock(block=Mock(date=date(2024, 7, 26))), ***REMOVED*** Week 4 - should discard
        ]
    }

    ***REMOVED*** Run MPC iteration (mocked)
    ***REMOVED*** ... implementation

    ***REMOVED*** Verify only 2 weeks committed
    committed_assignments = [
        a for a in mock_engine.generate.return_value['assignments']
        if a.block.date < control_end
    ]

    assert len(committed_assignments) == 2, "Should only commit control horizon"


def test_mpc_advances_horizon_correctly():
    """Test that MPC shifts horizon forward after each iteration."""
    config = MPCConfig(
        prediction_horizon_weeks=4,
        control_horizon_weeks=2,
    )

    start_date = date(2024, 7, 1)

    ***REMOVED*** Iteration 1
    current_date_1 = start_date
    control_end_1 = current_date_1 + timedelta(weeks=2)

    ***REMOVED*** Iteration 2 should start where iteration 1 ended
    current_date_2 = control_end_1
    expected_date_2 = date(2024, 7, 15)

    assert current_date_2 == expected_date_2, "Horizon should advance by control horizon"
```

***REMOVED******REMOVED******REMOVED******REMOVED*** 3. Prediction Error Tracking

```python
def test_mpc_tracks_prediction_errors():
    """Test that MPC records prediction vs actual for model learning."""
    bridge = MPCSchedulerBridge(
        resilience_service=mock_resilience,
        constraint_manager=ConstraintManager.create_default(),
    )

    ***REMOVED*** Predicted metrics
    predicted = {
        'utilization_trajectory': [0.78, 0.80, 0.82],
        'coverage_trajectory': [0.95, 0.94, 0.93],
    }

    ***REMOVED*** Actual metrics (after generation)
    actual = {
        'utilization': 0.82,  ***REMOVED*** Higher than predicted 0.78
        'coverage': 0.93,     ***REMOVED*** Lower than predicted 0.95
    }

    ***REMOVED*** Observe result
    bridge.observe_result(
        assignments=[Mock()],
        predicted_metrics=predicted,
        actual_metrics=actual,
    )

    ***REMOVED*** Check that error was recorded
    assert len(bridge.prediction_errors) == 1

    error = bridge.prediction_errors[0]
    assert error['utilization_error'] == pytest.approx(0.04, abs=0.01)  ***REMOVED*** 0.82 - 0.78
    assert error['coverage_error'] == pytest.approx(-0.02, abs=0.01)    ***REMOVED*** 0.93 - 0.95
```

***REMOVED******REMOVED******REMOVED*** Integration Tests

***REMOVED******REMOVED******REMOVED******REMOVED*** 4. End-to-End MPC Schedule Generation

```python
@pytest.mark.integration
def test_mpc_generates_full_year_schedule(db_session):
    """Test that MPC can generate a complete academic year schedule."""
    start_date = date(2024, 7, 1)
    end_date = date(2025, 6, 30)  ***REMOVED*** 12 months

    resilience = ResilienceService(db=db_session)
    constraints = ConstraintManager.create_resilience_aware(tier=1)

    bridge = MPCSchedulerBridge(
        resilience_service=resilience,
        constraint_manager=constraints,
        config=MPCConfig(
            prediction_horizon_weeks=4,
            control_horizon_weeks=2,
        ),
    )

    ***REMOVED*** Generate schedule
    assignments = bridge.generate_schedule(
        db=db_session,
        start_date=start_date,
        end_date=end_date,
    )

    ***REMOVED*** Verify complete coverage
    expected_days = (end_date - start_date).days
    expected_blocks = expected_days * 2  ***REMOVED*** AM + PM

    blocks_covered = len(set(a.block_id for a in assignments))
    coverage_rate = blocks_covered / expected_blocks

    assert coverage_rate >= 0.90, f"Coverage should be ≥90%, got {coverage_rate:.1%}"

    ***REMOVED*** Verify ACGME compliance
    validator = ACGMEValidator(db=db_session)
    validation = validator.validate_all(start_date, end_date)

    assert validation.valid, f"Schedule should be ACGME compliant: {validation.violations}"

    ***REMOVED*** Verify MPC iterations executed
    expected_iterations = (expected_days // 14) + 1  ***REMOVED*** Every 2 weeks
    assert len(bridge.weight_history) >= expected_iterations - 2  ***REMOVED*** Allow some tolerance


@pytest.mark.integration
def test_mpc_adapts_to_changing_conditions(db_session):
    """Test that MPC adjusts weights when conditions change mid-schedule."""
    start_date = date(2024, 7, 1)
    end_date = date(2024, 9, 1)  ***REMOVED*** 2 months

    ***REMOVED*** Create mock resilience that simulates worsening conditions
    class DegradingResilienceService(ResilienceService):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.call_count = 0

        def get_forecast(self, **kwargs):
            self.call_count += 1
            ***REMOVED*** Simulate gradual degradation
            base_util = 0.75 + (self.call_count * 0.03)
            return {
                'utilization_trajectory': [base_util, base_util + 0.02, base_util + 0.04, base_util + 0.06],
                'coverage_trajectory': [0.95, 0.94, 0.93, 0.92],
            }

    resilience = DegradingResilienceService(db=db_session)
    constraints = ConstraintManager.create_default()

    bridge = MPCSchedulerBridge(
        resilience_service=resilience,
        constraint_manager=constraints,
    )

    ***REMOVED*** Generate schedule
    assignments = bridge.generate_schedule(
        db=db_session,
        start_date=start_date,
        end_date=end_date,
    )

    ***REMOVED*** Verify that weights increased as conditions degraded
    weight_history = bridge.weight_history

    first_iteration = weight_history[0]
    last_iteration = weight_history[-1]

    ***REMOVED*** Utilization buffer weight should have increased
    assert last_iteration['weights']['utilization_buffer'] > first_iteration['weights']['utilization_buffer']

    ***REMOVED*** Coverage weight should have increased
    assert last_iteration['weights']['coverage'] > first_iteration['weights']['coverage']

    ***REMOVED*** Preference weight should have decreased
    assert last_iteration['weights']['preference'] < first_iteration['weights']['preference']

    ***REMOVED*** System status should have degraded
    assert last_iteration['system_state'] in ["ORANGE", "RED"], \
        "System should recognize degraded state"
```

***REMOVED******REMOVED******REMOVED*** Performance Tests

***REMOVED******REMOVED******REMOVED******REMOVED*** 5. MPC Solve Time

```python
@pytest.mark.performance
def test_mpc_iteration_completes_within_time_limit(db_session):
    """Test that each MPC iteration completes in reasonable time."""
    import time

    bridge = MPCSchedulerBridge(
        resilience_service=ResilienceService(db=db_session),
        constraint_manager=ConstraintManager.create_default(),
        config=MPCConfig(control_horizon_weeks=2),
    )

    start_date = date(2024, 7, 1)
    end_date = date(2024, 7, 15)  ***REMOVED*** 2 weeks

    start_time = time.time()

    assignments = bridge.generate_schedule(
        db=db_session,
        start_date=start_date,
        end_date=end_date,
    )

    elapsed = time.time() - start_time

    ***REMOVED*** Single 2-week solve should complete in <30 seconds
    assert elapsed < 30.0, f"MPC iteration took {elapsed:.1f}s, should be <30s"


@pytest.mark.performance
def test_mpc_faster_than_monolithic_for_large_ranges(db_session):
    """Test that MPC is faster than monolithic solve for long periods."""
    import time

    start_date = date(2024, 7, 1)
    end_date = date(2024, 10, 1)  ***REMOVED*** 3 months

    ***REMOVED*** Monolithic solve
    engine_mono = SchedulingEngine(db=db_session, start_date=start_date, end_date=end_date)

    start_mono = time.time()
    result_mono = engine_mono.generate(algorithm='cp_sat', timeout_seconds=120.0)
    time_mono = time.time() - start_mono

    ***REMOVED*** MPC solve
    bridge = MPCSchedulerBridge(
        resilience_service=ResilienceService(db=db_session),
        constraint_manager=ConstraintManager.create_default(),
    )

    start_mpc = time.time()
    assignments_mpc = bridge.generate_schedule(db=db_session, start_date=start_date, end_date=end_date)
    time_mpc = time.time() - start_mpc

    ***REMOVED*** MPC should be faster for long ranges
    assert time_mpc < time_mono * 1.2, \
        f"MPC ({time_mpc:.1f}s) should be comparable or faster than monolithic ({time_mono:.1f}s)"
```

---

***REMOVED******REMOVED*** References

***REMOVED******REMOVED******REMOVED*** Primary Sources

1. **MPC Theory:**
   - `docs/research/exotic-control-theory-for-scheduling.md` (Section 3: Model Predictive Control)
   - Optimization problem formulation (lines 1037-1500)
   - Receding horizon algorithm

2. **Scheduling Engine:**
   - `backend/app/scheduling/engine.py` (SchedulingEngine class)
   - Current constraint-based optimization approach
   - CP-SAT integration points

3. **Resilience Framework:**
   - `backend/app/resilience/service.py` (ResilienceService)
   - Forecasting methods for MPC prediction horizon
   - Health status calculation

4. **Constraint Weights:**
   - `backend/app/scheduling/constraints/resilience.py`
     - HubProtectionConstraint: weight=15.0
     - UtilizationBufferConstraint: weight=20.0
     - N1VulnerabilityConstraint: weight=25.0
   - `backend/app/scheduling/constraints/manager.py`
     - Coverage: weight=1000.0
     - Equity: weight=10.0
     - Continuity: weight=5.0
     - Preference: weight=8.0

***REMOVED******REMOVED******REMOVED*** Related Documentation

- **Cross-Disciplinary Resilience:** `docs/architecture/cross-disciplinary-resilience.md`
  - 80% utilization threshold (queuing theory)
  - Tier 1/2/3 resilience concepts

- **Solver Algorithm:** `docs/architecture/SOLVER_ALGORITHM.md`
  - CP-SAT objective function construction
  - Hard vs soft constraint handling

- **ACGME Compliance:** `backend/app/scheduling/validator.py`
  - 80-hour rule enforcement
  - Supervision ratio validation

***REMOVED******REMOVED******REMOVED*** External References

- **Model Predictive Control:** Camacho & Bordons, "Model Predictive Control" (2nd Ed)
- **Queuing Theory:** Erlang-C formula for utilization thresholds
- **Google OR-Tools:** CP-SAT solver documentation

---

***REMOVED******REMOVED*** Appendix A: Weight Sensitivity Analysis

***REMOVED******REMOVED******REMOVED*** Base Weights vs Adjusted Weights

| Constraint          | Base | GREEN | YELLOW | ORANGE | RED  | BLACK |
|---------------------|------|-------|--------|--------|------|-------|
| Coverage            | 1000 | 1000  | 1200   | 1500   | 2000 | 3000  |
| Utilization Buffer  | 20   | 16    | 25     | 40     | 60   | 100   |
| Equity              | 10   | 15    | 10     | 8      | 5    | 3     |
| Continuity          | 5    | 5     | 5      | 5      | 5    | 5     |
| Preference          | 8    | 8     | 6      | 4      | 2    | 0.5   |
| Hub Protection      | 15   | 15    | 15     | 22     | 22   | 22    |
| N1 Vulnerability    | 25   | 25    | 25     | 25     | 38   | 38    |

**Observations:**
- Coverage dominates in all states (highest weight)
- Utilization buffer increases exponentially with crisis severity
- Preference weight drops to near-zero in crisis
- Continuity remains stable (schedule stability important)

---

***REMOVED******REMOVED*** Appendix B: MPC Performance Metrics

***REMOVED******REMOVED******REMOVED*** Metrics to Track

```python
@dataclass
class MPCPerformanceMetrics:
    """Metrics for evaluating MPC performance."""

    ***REMOVED*** Prediction accuracy
    mean_utilization_error: float  ***REMOVED*** |predicted - actual| utilization
    mean_coverage_error: float     ***REMOVED*** |predicted - actual| coverage
    prediction_rmse: float          ***REMOVED*** Root mean square error

    ***REMOVED*** Computational efficiency
    mean_iteration_time: float      ***REMOVED*** Average time per iteration (seconds)
    total_solve_time: float         ***REMOVED*** Total time for full schedule
    iterations_count: int           ***REMOVED*** Number of MPC iterations

    ***REMOVED*** Adaptation effectiveness
    weight_adjustment_count: int    ***REMOVED*** How many times weights changed
    crisis_iterations: int          ***REMOVED*** Iterations in RED/BLACK state
    system_state_transitions: int   ***REMOVED*** Number of state changes

    ***REMOVED*** Schedule quality
    final_coverage_rate: float      ***REMOVED*** Overall coverage achieved
    final_utilization_rate: float   ***REMOVED*** Overall utilization
    acgme_compliant: bool           ***REMOVED*** Pass ACGME validation

    ***REMOVED*** Resilience indicators
    n1_pass_rate: float             ***REMOVED*** % of schedule that passes N-1
    hub_overload_incidents: int     ***REMOVED*** Times hub faculty exceeded threshold
    buffer_exhaustion_count: int    ***REMOVED*** Times utilization > 90%
```

**Success Criteria:**
- Mean prediction error < 5%
- Mean iteration time < 30 seconds
- Final coverage ≥ 95%
- ACGME compliant: True
- N-1 pass rate ≥ 80%

---

**End of Specification**

This bridge specification is ready for implementation. See `backend/app/scheduling/mpc/` for implementation files.
