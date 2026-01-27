# CP-SAT Mental Model for Residency Scheduling

> **Audience:** Humans who need to understand, debug, or tune the constraint-based scheduler.
>
> **Last Updated:** 2026-01-27

---

## What Is CP-SAT?

CP-SAT (Constraint Programming - Satisfiability) is Google OR-Tools' constraint solver. It finds assignments that satisfy all constraints, then optimizes an objective function.

Think of it as: **"Prove a valid schedule exists, then find the best one."**

---

## The Core Mental Shift

### Manual Scheduling (Human Approach)
1. Place high-priority items first
2. Fit other things around them
3. Make judgment calls when conflicts arise
4. Adjust as you go

### CP-SAT (How It Works)
1. See ALL constraints simultaneously
2. Find ANY assignment satisfying ALL constraints
3. If impossible, fail entirely (no partial credit)
4. If possible, optimize toward objective

**Key insight:** Your manual process has implicit flexibility. CP-SAT has none unless you explicitly encode it.

---

## Hard vs Soft Constraints

### Hard Constraints
**Definition:** Physically or logically impossible to violate.

| Constraint | Why Hard |
|------------|----------|
| One activity per slot | Can't be in two places (physics) |
| Locked slots unchanged | User's explicit intent |
| Physical capacity ≤ 8 | Exam rooms are finite (space) |
| ACGME duty hours | Accreditation risk (legal) |

**If violated:** Model is INFEASIBLE. No schedule produced.

### Soft Constraints
**Definition:** Desirable but not mandatory. Violations incur penalties.

| Constraint | Why Soft |
|------------|----------|
| AT coverage | 98% supervision > no schedule |
| Activity minimums | 3 clinics instead of 4 is suboptimal, not catastrophic |
| Physical capacity ≤ 6 | Crowded but functional |
| SM alignment | Nice to have, not critical |

**If violated:** Penalty subtracted from objective. Schedule still produced.

### The Decision Rule
Ask: "If this is violated by 1 unit, is the schedule usable?"
- **No** → Hard constraint
- **Yes, but worse** → Soft constraint with penalty

---

## Penalty Weights

Penalties define priority ordering. Relative values matter, not absolute.

### Recommended Hierarchy

| Tier | Constraint | Penalty | Rationale |
|------|------------|---------|-----------|
| **Safety** | AT coverage shortfall | 50 | Supervision gaps are serious |
| **Training** | Clinic min shortfall | 25 | Core training requirement |
| | Activity min shortfall | 10 | Important but flexible |
| **Operations** | Physical capacity >6 | 15 | Uncomfortable, not dangerous |
| | Faculty clinic shortfall | 10 | Staffing preference |
| **Preferences** | SM alignment | 8 | Nice to have |
| | Activity max overage | 5 | Slight overexposure is fine |

### The Math

With these weights, the solver will:
- Sacrifice 5 activity max overages to save 1 AT coverage (5×5=25 < 50)
- Sacrifice 2 clinic mins to save 1 AT coverage (2×25=50 = 50)
- Never sacrifice AT coverage for SM alignment (50 >> 8)

### Principle
```
Safety > Training > Operations > Preferences
  50   >   25/10  >    15/10   >    8/5
```

Each tier ~2-3x the tier below.

---

## Common Misconceptions

### 1. "Important" ≠ "Hard"

**Wrong thinking:** "AT coverage is critical → make it hard"

**Right thinking:** "Hard" means physically impossible to violate, not "really important."

High penalty accomplishes "really try" without causing infeasibility.

### 2. Constraints Interact Multiplicatively

**Wrong thinking:** "A is feasible. B is feasible. A+B is feasible."

**Right thinking:** A × B × C × D can be infeasible even when each alone is fine.

Example:
- Faculty X must do AT (coverage)
- Faculty X max clinic = 2 (cap)
- SM resident needs SM faculty (alignment)
- Faculty X is the only SM faculty
- **Result:** Impossible

### 3. Timeout ≠ Infeasible

| Status | Meaning |
|--------|---------|
| OPTIMAL | Best possible solution found |
| FEASIBLE | A valid solution (maybe not optimal) |
| INFEASIBLE | **Proved** no solution exists |
| UNKNOWN | Ran out of time, solution might exist |

INFEASIBLE is a mathematical proof. UNKNOWN means "try longer or relax constraints."

### 4. No Partial Credit

```python
model.Add(coverage >= demand)  # Violated by 0.001 = INFEASIBLE
```

A constraint is satisfied or the entire model fails. This is why soft constraints exist.

### 5. First Feasible ≠ Good

The solver finds *any* valid assignment first, then improves. With short timeout, you get a feasible but possibly terrible solution.

### 6. Preloads Are Constraints Too

Every locked slot removes flexibility. Heavy preloading (60%+) can make the remaining problem unsolvable.

### 7. Small Changes → Wildly Different Results

Adding one constraint can:
- 10x slower
- 10x faster (by pruning search space)
- Flip feasible ↔ infeasible
- Completely change the solution

CP-SAT is chaotic. Don't expect linear cause-and-effect.

---

## Debugging Infeasibility

### The Problem
CP-SAT says "no solution exists" but doesn't say which constraint killed it.

### The Method: Subtraction

1. Comment out constraints until feasible
2. Add back one by one
3. The constraint that breaks it = your culprit

```python
# model.Add(at_coverage)       # Try without
# model.Add(sm_alignment)      # Try without
model.Add(one_per_slot)        # Keep (physics)
```

### Diagnostic Snapshots

When infeasible, dump:
- Slot counts by type
- Requirement totals vs available slots
- Per-constraint feasibility checks

The activity solver writes these to `/tmp/activity_failure_*.json`.

---

## Performance Tuning

### Variable Domains Matter

```python
# Slow: considers 0-1000
x = model.NewIntVar(0, 1000, "x")

# Fast: considers 0-10
x = model.NewIntVar(0, 10, "x")
```

Tighter bounds = faster solving. If shortfall can't exceed 5, don't allow 100.

### Parallelism Has Limits

```python
solver.parameters.num_search_workers = 8
```

- Workers explore different strategies (don't split problem spatially)
- Diminishing returns after 8-16 workers
- Some problems don't parallelize

### Constraint Tightness > Problem Size

- 10,000 variables + loose constraints → seconds
- 100 variables + tight constraints → might never solve

Your problem (~40,000 variables) is small. The difficulty is constraint tightness.

---

## The Solver Has No Memory

Each `solve()` call starts fresh. It doesn't remember:
- Last week's solution
- Similar problems it solved before
- Your intent

For continuity, you must encode it explicitly (warm starts, fixed variables).

---

## Quick Reference

### When Adding a Constraint

1. Is violation physically impossible? → Hard
2. Is violation bad but survivable? → Soft with penalty
3. What tier is it? → Set penalty relative to that tier
4. Does it interact with existing constraints? → Test combinations

### When Debugging Infeasibility

1. Check if INFEASIBLE (proved) or UNKNOWN (timeout)
2. Read failure snapshot for obvious issues (min > slots)
3. Remove constraints until feasible
4. Add back to find culprit
5. Convert culprit to soft constraint

### When Solution Is Bad

1. Check if OPTIMAL or just FEASIBLE
2. Increase timeout
3. Review penalty ratios (are priorities right?)
4. Check if data quality issue (requirements > capacity)

---

## Summary

CP-SAT is a proof engine. Your job:

1. **Define "valid" loosely enough** that proofs succeed (soft constraints)
2. **Use the objective** to get good solutions within validity space (penalties)
3. **Debug by subtraction** when things break
4. **Trust the math** - if it says infeasible, it's infeasible

The manual scheduling process succeeds because you have implicit flexibility, sequential placement, and judgment calls. CP-SAT needs all of that encoded explicitly.

---

*Document created from debugging sessions on the activity solver, January 2026.*
