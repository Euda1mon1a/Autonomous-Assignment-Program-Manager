# PuLP (Linear Programming) Mental Model

> **Audience:** Humans who need to understand when and how to use the PuLP/LP scheduler.
>
> **Last Updated:** 2026-01-27

---

## What Is PuLP?

PuLP is a Linear Programming (LP) solver. It finds the best solution to a problem where:
- **Variables** are continuous or binary (0/1)
- **Constraints** are linear equations/inequalities
- **Objective** is a linear function to maximize/minimize

Think of it as: **"Solve the math problem exactly, but only if the math is simple enough."**

---

## How It Works

### The Mathematical Model

```
Maximize:
    1000 × coverage - 10 × equity_penalty - 5 × template_imbalance

Subject to:
    x[resident, block, template] ∈ {0, 1}  (binary decision)
    Σ x[r, b, *] = 1  for each resident-block (exactly one rotation)
    Σ x[*, b, t] ≤ capacity[t]  (template capacity)
    ... more linear constraints ...
```

### What "Linear" Means

Linear constraints look like: `a₁x₁ + a₂x₂ + ... ≤ b`

**Linear (OK):**
- `assignments[X] + assignments[Y] ≤ 10`
- `3 × slot_A + 2 × slot_B = 5`

**Non-linear (NOT OK):**
- `assignments[X] × assignments[Y] ≤ 10` (multiplication of variables)
- `if slot_A then slot_B` (logical implication without linearization)
- `max(slot_A, slot_B) ≤ 5` (max/min of variables)

### Linearization Tricks

Some non-linear constraints CAN be converted to linear:

**Max constraint:** `z ≤ max(x, y)`
```
z ≤ x + M × (1 - b)
z ≤ y + M × b
b ∈ {0, 1}
```

**Implication:** `x = 1 → y = 1`
```
y ≥ x
```

These tricks add complexity and variables. Too many → slow solving.

---

## When to Use PuLP

### Good For

| Scenario | Why |
|----------|-----|
| Large problems | Scales better than CP-SAT on big instances |
| Simple constraints | LP is fast when constraints are naturally linear |
| Feasibility focus | Finding *any* valid solution quickly |
| Production environments | CBC solver is robust and well-tested |

### Bad For

| Scenario | Why |
|----------|-----|
| Complex logical constraints | Linearization is messy and slow |
| Many "if-then" rules | Each requires helper variables |
| Need optimality proof | LP relaxation may not be tight |
| Highly constrained problems | CP-SAT's propagation is better |

---

## Key Characteristics

### Branch-and-Bound for Binary Variables

When variables are binary (0/1), PuLP uses Branch-and-Bound:
1. Relax binary to continuous [0, 1]
2. Solve relaxed LP (fast)
3. If solution is integer, done
4. Otherwise, branch on a fractional variable
5. Repeat recursively

This can be fast or slow depending on problem structure.

### Objective Function Matters

Unlike CP-SAT, PuLP is highly sensitive to objective weights:
- `coverage × 1000` means coverage dominates
- `equity × 10` means equity is secondary
- Bad weights → bad solutions

The weights in our solver:
```python
COVERAGE_WEIGHT = 1000      # Fill slots
EQUITY_PENALTY_WEIGHT = 10  # Balance workload
TEMPLATE_BALANCE_WEIGHT = 5 # Distribute across rotations
```

### Solver Backends

PuLP supports multiple backends:
- **CBC (default):** Open-source, good quality, bundled with PuLP
- **GLPK:** Open-source alternative
- **Gurobi:** Commercial, very fast (requires license)
- **CPLEX:** Commercial, very fast (requires license)

Our code uses CBC by default. For faster solving, consider commercial solvers.

---

## Performance

| Problem Size | CBC Expected Runtime |
|--------------|---------------------|
| <100 blocks | <1 second |
| <500 blocks | 1-10 seconds |
| <2000 blocks | 10-60 seconds |
| >2000 blocks | May timeout |

Performance depends heavily on constraint complexity. More "if-then" logic = slower.

---

## Differences from CP-SAT

| Aspect | PuLP (LP) | CP-SAT |
|--------|-----------|--------|
| Variable types | Continuous, Integer, Binary | Integer, Boolean |
| Constraint style | Linear equations | Any logical expression |
| Propagation | Limited | Powerful |
| Scaling | Better on large simple problems | Better on complex problems |
| Non-linear | Requires linearization | Native support |
| Soft constraints | Natural (penalty in objective) | Requires encoding |

### When CP-SAT Beats PuLP

- Many logical constraints (if-then, or, not)
- Symmetry in the problem
- Tight constraint interactions
- Need proof of optimality

### When PuLP Beats CP-SAT

- Very large problems with simple structure
- Linear objectives with linear constraints
- When you have access to Gurobi/CPLEX
- Continuous variables needed (not our case)

---

## Common Pitfalls

### 1. Forgetting Linearization Costs

Each non-linear constraint you linearize adds variables and constraints. A problem with 50 "max" constraints might add 150+ helper variables, slowing everything down.

### 2. Weak LP Relaxation

If the LP relaxation (continuous version) is far from the integer solution, Branch-and-Bound takes forever. This is called a "weak relaxation."

Symptoms:
- Large gap between LP bound and best integer solution
- Solver explores millions of nodes
- Timeout with suboptimal solution

### 3. Numerical Precision

LP solvers use floating-point math. Sometimes:
- A variable is 0.9999999 instead of 1
- Constraints are violated by 1e-8

Use tolerances when checking solutions:
```python
if pulp.value(x[r, b, t]) > 0.5:  # Not == 1
    assignments.append(...)
```

### 4. Ignoring Infeasibility Diagnosis

When PuLP returns "Infeasible", it doesn't tell you why. Unlike CP-SAT, there's no built-in conflict analysis.

Debugging approach:
1. Remove constraints until feasible
2. Add back one by one
3. The constraint that breaks it is the culprit

---

## Our PuLP Implementation

### Decision Variables

```python
x[r_i, b_i, t_i] = 1 if resident r assigned to template t in block b
f[f_i, b_i, t_i] = 1 if faculty f assigned to template t in block b
call[f_i, b_i, "overnight"] = 1 if faculty f on call for block b
```

### Core Constraints

1. **One rotation per person per block:**
   ```python
   for each (resident, block):
       Σ x[r, b, *] == 1
   ```

2. **At most one rotation per faculty per block:**
   ```python
   for each (faculty, block):
       Σ f[f, b, *] <= 1
   ```

3. **Constraint manager constraints:** Applied via `constraint_manager.apply_to_pulp()`

### Objective

```python
Maximize:
    1000 × Σ x[all]                    # Coverage
    - 10 × equity_penalty              # Workload balance
    - 5 × max_template_count           # Template distribution
```

---

## Tuning PuLP

### Timeout

```python
solver = PuLPSolver(timeout_seconds=120.0)
```

Longer timeout = better solution (usually). But diminishing returns after ~60s for most problems.

### Solver Backend

```python
solver = PuLPSolver(solver_backend="PULP_CBC_CMD")
```

Options: `PULP_CBC_CMD`, `GLPK_CMD`, `GUROBI_CMD`, `CPLEX_CMD`

If you have Gurobi/CPLEX licenses, they're 10-100x faster.

### MIP Gap

The CBC solver has a "MIP gap" setting - it stops when solution is within X% of optimal. Default is usually 0.01% (very tight). Relaxing to 1% can speed up solving significantly.

Not currently exposed in our code, but could be added:
```python
solver = pulp.PULP_CBC_CMD(msg=0, timeLimit=60, gapRel=0.01)
```

---

## Decision Guide

```
Problem is large (>1000 blocks) and simple?
  → Use PuLP

Problem has complex logical constraints?
  → Use CP-SAT

Need fastest possible solution?
  → Try PuLP first, fall back to Greedy

Have Gurobi/CPLEX license?
  → PuLP with commercial backend

Just want "whatever works"?
  → Use Hybrid (tries CP-SAT, falls back to PuLP)
```

---

## Summary

PuLP is the **mathematical, scalable, but limited** solver:
- Mathematical: Solves a well-defined optimization problem
- Scalable: Handles large problems better than CP-SAT
- Limited: Only linear constraints, requires linearization tricks

Use it for large simple problems. For complex constraint logic, use CP-SAT. For quick-and-dirty, use Greedy. For production, use Hybrid.

---

*Document created January 2026.*
