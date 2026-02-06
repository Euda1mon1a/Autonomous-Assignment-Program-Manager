# Constraint Propagation Methodology

**Purpose:** Framework for understanding and solving constraint satisfaction problems in scheduling

---

## When to Use This Methodology

Apply when:
- Adding or modifying scheduling constraints
- Debugging constraint violations
- Optimizing solver performance
- Analyzing constraint interactions
- Designing new constraint types

---

## Core Concepts

### 1. Constraint Satisfaction Problem (CSP) Framing

#### Problem Components

```
CSP = (V, D, C)

Where:
  V = Variables (assignments to schedule)
  D = Domains (possible values for each variable)
  C = Constraints (restrictions on variable combinations)
```

**For Residency Scheduling:**

```python
# Variables (V)
V = {
    "assignment_123": Assignment(person=?, rotation=?, date=?, session=?),
    "assignment_124": Assignment(person=?, rotation=?, date=?, session=?),
    ...
}

# Domains (D)
D = {
    "assignment_123.person": [PGY1-01, PGY1-02, ..., FAC-05],
    "assignment_123.rotation": [inpatient, peds_clinic, procedures, ...],
    "assignment_123.date": [2026-03-12, 2026-03-13, ...],
    "assignment_123.session": [AM, PM]
}

# Constraints (C)
C = {
    acgme_80_hour,
    acgme_1_in_7,
    supervision_ratio,
    rotation_coverage,
    no_double_booking,
    credential_requirements,
    ...
}
```

### 2. Constraint Types

#### Hard Constraints (Must Satisfy)

| Constraint | Type | Scope |
|------------|------|-------|
| ACGME 80-hour rule | Global temporal | Per person, 4-week window |
| ACGME 1-in-7 rule | Global temporal | Per person, 7-day window |
| Supervision ratio | Local structural | Per rotation, per session |
| No double-booking | Binary | Per person, per datetime |
| Credential match | Binary | Person-rotation pairs |

#### Soft Constraints (Optimize)

| Constraint | Weight | Objective |
|------------|--------|-----------|
| Preference satisfaction | 5 | Maximize |
| Fairness (Gini) | 3 | Minimize |
| Workload balance | 2 | Minimize variance |
| Weekend distribution | 2 | Minimize variance |
| Continuity of care | 1 | Maximize consecutive days on rotation |

### 3. Constraint Propagation Algorithm

#### Forward Checking

**Purpose:** Eliminate values from domains that violate constraints

```python
def forward_checking(assignment, constraints):
    """
    After assigning a value to a variable, remove incompatible
    values from other variables' domains.

    Example:
      If we assign PGY1-01 to inpatient on 2026-03-12 AM:
      - Remove PGY1-01 from all other assignments on same datetime (no double-booking)
      - Update available supervision slots for that session
      - Check if remaining assignments can still satisfy coverage
    """
    for constraint in constraints:
        affected_variables = constraint.get_affected_variables(assignment)

        for var in affected_variables:
            # Remove incompatible values from domain
            var.domain = [val for val in var.domain if constraint.allows(var, val)]

            # If domain becomes empty, backtrack
            if len(var.domain) == 0:
                return FAILURE

    return SUCCESS
```

#### Arc Consistency (AC-3)

**Purpose:** Ensure every value in a variable's domain has at least one compatible value in related variables' domains

```python
def ac3(variables, constraints):
    """
    Enforce arc consistency across all constraints.

    Example:
      For supervision_ratio constraint:
      - If rotation requires 2 faculty
      - And only 2 faculty remain in domain
      - Then both must be assigned (no choice)
      - Propagate this to other constraints
    """
    queue = [(Xi, Xj) for constraint in constraints
                      for Xi, Xj in constraint.get_arcs()]

    while queue:
        (Xi, Xj) = queue.pop()

        if revise(Xi, Xj):
            if len(Xi.domain) == 0:
                return FAILURE

            # Add all arcs (Xk, Xi) back to queue
            for Xk in Xi.neighbors:
                queue.append((Xk, Xi))

    return SUCCESS

def revise(Xi, Xj):
    """Remove values from Xi.domain that have no support in Xj.domain"""
    revised = False

    for x in Xi.domain[:]:  # Iterate over copy
        if not any(constraint.allows(x, y) for y in Xj.domain):
            Xi.domain.remove(x)
            revised = True

    return revised
```

#### Constraint Propagation Flow

```
1. Initial Assignment
   └─> Assign variable (e.g., PGY1-01 to inpatient on 2026-03-12 AM)

2. Forward Checking
   └─> Remove incompatible values from related variables
       ├─> Remove PGY1-01 from other 2026-03-12 AM assignments
       ├─> Reduce supervision slots for inpatient 2026-03-12 AM
       └─> Update coverage counter for inpatient

3. Arc Consistency
   └─> Propagate domain reductions through constraint graph
       ├─> Check if remaining people can cover remaining shifts
       ├─> Verify ACGME constraints still satisfiable
       └─> Ensure all rotations can meet minimum coverage

4. Conflict Detection
   └─> If any domain becomes empty → BACKTRACK
   └─> If all domains non-empty → CONTINUE
```

---

## Backtracking Strategies

### 1. Chronological Backtracking (Naive)

```python
def chronological_backtracking(assignment, variables):
    """
    Backtrack to most recent assignment.

    Problem: Doesn't learn from conflicts.
    May repeat same mistake many times.
    """
    if is_complete(assignment):
        return assignment

    var = select_unassigned_variable(variables)

    for value in var.domain:
        if is_consistent(value, assignment):
            assignment[var] = value
            result = chronological_backtracking(assignment, variables)
            if result != FAILURE:
                return result
            del assignment[var]  # Backtrack

    return FAILURE
```

### 2. Conflict-Directed Backjumping

```python
def backjumping(assignment, variables):
    """
    Backtrack to the variable that caused the conflict.

    Advantage: Skips irrelevant variables.
    Learns from conflicts.
    """
    if is_complete(assignment):
        return assignment

    var = select_unassigned_variable(variables)
    conflict_set = set()

    for value in var.domain:
        if is_consistent(value, assignment):
            assignment[var] = value
            result, conflicts = backjumping(assignment, variables)
            if result != FAILURE:
                return result, conflict_set
            conflict_set.update(conflicts)
            del assignment[var]
        else:
            # Track which variables caused inconsistency
            conflict_set.update(get_conflicting_vars(var, value, assignment))

    return FAILURE, conflict_set
```

### 3. Dynamic Backtracking (Intelligent)

```python
def dynamic_backtracking(assignment, variables, decisions):
    """
    Intelligently reorder decisions to avoid conflicts.

    Used by CP-SAT solver.
    Learns conflict clauses.
    """
    while not is_complete(assignment):
        var = select_most_constrained_variable(variables)  # MRV heuristic
        value = select_least_constraining_value(var)      # LCV heuristic

        decision_level = len(decisions)
        decisions.append((var, value))

        if not propagate_constraints(assignment, var, value):
            # Conflict detected - learn and backtrack
            conflict_clause = analyze_conflict(assignment, decisions)
            backtrack_level = learn_from_conflict(conflict_clause, decisions)

            # Backtrack to learned level, not just previous
            rollback_to_level(assignment, decisions, backtrack_level)
        else:
            assignment[var] = value

    return assignment
```

---

## Variable and Value Ordering Heuristics

### Variable Ordering

#### Minimum Remaining Values (MRV)

**Choose variable with smallest domain first**

```python
def select_variable_mrv(variables):
    """
    Variable with fewest legal values remaining.

    Rationale: Fail fast - if we're going to fail, find out early.

    Example:
      - Assignment A: domain = [PGY1-01, PGY1-02, PGY1-03, PGY2-01]
      - Assignment B: domain = [FAC-001]
      - Choose B (only 1 option, must assign correctly)
    """
    unassigned = [v for v in variables if not v.is_assigned()]
    return min(unassigned, key=lambda v: len(v.domain))
```

#### Degree Heuristic (Tie-Breaker)

**Choose variable involved in most constraints**

```python
def select_variable_degree(variables):
    """
    Variable with most constraints with other unassigned variables.

    Rationale: Constrain others early to reduce search space.

    Example:
      - Supervision ratio constraint affects all assignments in a session
      - Coverage constraint affects all assignments in a rotation
      - Choose assignment that participates in most constraints
    """
    unassigned = [v for v in variables if not v.is_assigned()]
    return max(unassigned, key=lambda v: v.constraint_count())
```

### Value Ordering

#### Least Constraining Value (LCV)

**Choose value that leaves most options for other variables**

```python
def select_value_lcv(variable):
    """
    Value that rules out fewest values in other variables.

    Rationale: Keep options open for future assignments.

    Example:
      Assigning person to rotation:
      - PGY1-01 is needed for many other rotations (high constraint)
      - PGY1-04 has fewer constraints
      - Choose PGY1-04 first (less constraining)
    """
    def count_conflicts(value):
        conflicts = 0
        for neighbor in variable.neighbors:
            for neighbor_val in neighbor.domain:
                if not is_compatible(value, neighbor_val):
                    conflicts += 1
        return conflicts

    return min(variable.domain, key=count_conflicts)
```

---

## Optimization vs Feasibility

### Two-Phase Approach

#### Phase 1: Find Feasible Solution

**Goal:** Satisfy all hard constraints

```python
def find_feasible_solution(variables, hard_constraints):
    """
    Ignore soft constraints initially.
    Just find ANY solution that satisfies hard constraints.

    Uses: Pure constraint satisfaction (no optimization).
    """
    solution = backtracking_search(variables, hard_constraints)

    if solution is None:
        # No feasible solution exists
        # Relax constraints or report infeasibility
        return analyze_infeasibility(variables, hard_constraints)

    return solution
```

#### Phase 2: Optimize Soft Constraints

**Goal:** Improve solution quality while maintaining feasibility

```python
def optimize_solution(initial_solution, soft_constraints):
    """
    Starting from feasible solution, optimize soft constraints.

    Methods:
    - Local search (hill climbing, simulated annealing)
    - Linear programming (if constraints are linear)
    - Branch and bound
    """
    current = initial_solution
    best = initial_solution
    best_score = evaluate_soft_constraints(best, soft_constraints)

    for iteration in range(max_iterations):
        neighbor = generate_neighbor(current)  # Small modification

        if satisfies_hard_constraints(neighbor):
            score = evaluate_soft_constraints(neighbor, soft_constraints)

            if score > best_score:
                best = neighbor
                best_score = score

        current = neighbor  # Or use acceptance criterion (SA)

    return best
```

### Multi-Objective Optimization

**Handle conflicting soft constraints using Pareto frontier**

```python
def pareto_optimization(initial_solution, objectives):
    """
    Find Pareto-optimal solutions (no objective can improve without hurting another).

    Objectives might conflict:
    - Maximize preference satisfaction vs Minimize workload variance
    - Maximize continuity vs Maximize fairness
    """
    pareto_frontier = [initial_solution]

    for candidate in generate_candidates():
        if satisfies_hard_constraints(candidate):
            scores = [obj.evaluate(candidate) for obj in objectives]

            # Check if candidate dominates or is dominated
            dominated = False
            to_remove = []

            for frontier_sol in pareto_frontier:
                frontier_scores = [obj.evaluate(frontier_sol) for obj in objectives]

                if dominates(scores, frontier_scores):
                    to_remove.append(frontier_sol)
                elif dominates(frontier_scores, scores):
                    dominated = True
                    break

            if not dominated:
                pareto_frontier = [s for s in pareto_frontier if s not in to_remove]
                pareto_frontier.append(candidate)

    return pareto_frontier

def dominates(scores1, scores2):
    """scores1 dominates scores2 if >= on all and > on at least one"""
    return all(s1 >= s2 for s1, s2 in zip(scores1, scores2)) and \
           any(s1 > s2 for s1, s2 in zip(scores1, scores2))
```

---

## Constraint Debugging Workflow

### Step 1: Isolate the Conflict

```python
def isolate_conflict(assignment, constraints):
    """
    Find minimal subset of constraints causing infeasibility.

    Method: Binary search over constraint set.
    """
    if is_satisfiable(assignment, constraints):
        return None  # No conflict

    # Try each constraint individually
    for c in constraints:
        if not is_satisfiable(assignment, [c]):
            return [c]  # Single constraint is unsatisfiable

    # Binary search for minimal unsatisfiable subset
    return find_minimal_conflict_set(assignment, constraints)
```

### Step 2: Analyze Constraint Interactions

```python
def analyze_interactions(constraints):
    """
    Build constraint dependency graph.

    Example:
      - acgme_80_hour depends on assignment counts
      - supervision_ratio depends on person-rotation assignments
      - coverage depends on rotation-date assignments
    """
    graph = {}

    for c1 in constraints:
        graph[c1] = []
        for c2 in constraints:
            if c1 != c2 and constraints_interact(c1, c2):
                graph[c1].append(c2)

    return graph
```

### Step 3: Visualize Constraint Propagation

```markdown
After assigning PGY1-01 to inpatient on 2026-03-12 AM:

1. no_double_booking:
   PGY1-01 domain for other 2026-03-12 AM slots → EMPTY

2. supervision_ratio:
   inpatient 2026-03-12 AM residents: 1 (needs 2:1 faculty)
   Available faculty for inpatient: [FAC-001, FAC-002, FAC-003]
   Required: at least 1 faculty

3. coverage:
   inpatient 2026-03-12 AM: 1/3 assigned

4. acgme_80_hour:
   PGY1-01 hours for week starting 2026-03-12: +8 hours
   Total: 32 hours (well below 80)

All constraints still satisfiable → CONTINUE
```

---

## Common Pitfalls

### 1. Over-Constraining

**Problem:** Too many hard constraints, no feasible solution

**Solution:** Convert some hard constraints to soft (with high penalty)

```python
# Instead of:
hard_constraints = [acgme_80_hour, acgme_1_in_7, coverage, fairness, preferences]

# Use:
hard_constraints = [acgme_80_hour, acgme_1_in_7, coverage]
soft_constraints = [
    (fairness, weight=3),
    (preferences, weight=2)
]
```

### 2. Premature Commitment

**Problem:** Early assignments constrain later ones unnecessarily

**Solution:** Use variable ordering heuristics (MRV, degree)

### 3. Ignoring Symmetry

**Problem:** Solver wastes time exploring symmetric solutions

**Solution:** Add symmetry-breaking constraints

```python
# If PGY1-01 and PGY1-02 are interchangeable:
# Break symmetry by ordering them
if person1.id < person2.id:
    add_constraint(person1.first_assignment <= person2.first_assignment)
```

### 4. Poor Objective Function

**Problem:** Objective doesn't reflect true goals

**Solution:** Validate objective with stakeholders, use multi-objective

---

## Integration with Solver (CP-SAT)

### Translating Constraints to CP-SAT

```python
from ortools.sat.python import cp_model

model = cp_model.CpModel()

# Variables
assignments = {}
for person in people:
    for date in dates:
        for session in sessions:
            var_name = f"{person.id}_{date}_{session}"
            assignments[var_name] = model.NewIntVar(0, len(rotations), var_name)

# Constraint: No double-booking
for person in people:
    for date in dates:
        # Each person can only be in one rotation per session
        model.AddAtMostOne([
            assignments[f"{person.id}_{date}_{session}"] == rotation_id
            for session in sessions
            for rotation_id in rotation_ids
        ])

# Constraint: Coverage
for rotation in rotations:
    for date in dates:
        for session in sessions:
            # At least min_coverage people assigned
            assigned_count = sum([
                assignments[f"{p.id}_{date}_{session}"] == rotation.id
                for p in people
            ])
            model.Add(assigned_count >= rotation.min_coverage)

# Solve
solver = cp_model.CpSolver()
status = solver.Solve(model)
```

---

## Quick Reference

### Decision Tree: Constraint Problem Solving

```
Problem: Need to add/modify constraint

1. Is it hard or soft?
   HARD → Must satisfy (e.g., ACGME compliance)
   SOFT → Optimize (e.g., preferences)

2. What is the scope?
   GLOBAL → Affects all variables (e.g., fairness)
   LOCAL  → Affects subset (e.g., supervision ratio)
   BINARY → Affects pairs (e.g., no double-booking)

3. When to check?
   PRE-ASSIGNMENT  → Forward checking
   POST-ASSIGNMENT → Arc consistency propagation
   FINAL           → Complete solution validation

4. What to do on violation?
   HARD → BACKTRACK (no choice)
   SOFT → RECORD PENALTY (continue)

5. How to order variables?
   Use MRV → Fail fast
   Use DEGREE → Constrain others early

6. How to order values?
   Use LCV → Keep options open
```

---

## Related Documentation

- `docs/architecture/SOLVER_ALGORITHM.md` - Solver implementation
- `.claude/Hooks/post-schedule-generation.md` - Capture constraint results
- `.claude/skills/constraint-preflight/SKILL.md` - Pre-commit constraint checks
- `backend/app/scheduling/constraints/` - Constraint implementations
