# Greedy Solver Mental Model

> **Audience:** Humans who need to understand when and how to use the greedy scheduler.
>
> **Last Updated:** 2026-01-27

---

## What Is the Greedy Solver?

A fast heuristic algorithm that makes locally optimal choices at each step without considering global consequences.

Think of it as: **"Handle the hardest cases first, always pick the fairest option."**

---

## How It Works

### The Algorithm

```
1. Calculate difficulty for each block (count eligible residents)
2. Sort blocks: hardest first (fewest eligible residents)
3. For each block:
   a. Find all eligible residents
   b. Score each: prefer those with fewer assignments (equity)
   c. Pick the highest-scoring resident
   d. Pick the template with fewest total uses (distribution)
   e. Record the assignment
   f. Update counts
```

### Why Hardest First?

If Block A has only 2 eligible residents and Block B has 10, assign Block A first. If you assign Block B first, you might use one of the 2 residents who could have covered Block A, leaving Block A impossible.

This is called **Most Constrained Variable (MCV)** heuristic.

### Why Fewest Assignments?

If Resident X has 5 assignments and Resident Y has 2, pick Y. This naturally balances workload without complex optimization.

This is called **greedy equity**.

---

## When to Use Greedy

### Good For

| Scenario | Why |
|----------|-----|
| Quick prototyping | Sub-second results |
| Simple schedules | Few constraints, obvious solutions |
| Explainability needed | Generates human-readable decision logs |
| Fallback solver | Always produces *something* |
| Debugging | Deterministic, easy to trace |

### Bad For

| Scenario | Why |
|----------|-----|
| Optimal solutions needed | Greedy is myopic, misses better global solutions |
| Complex constraint interactions | Doesn't backtrack when stuck |
| Tight feasibility | May fail where CP-SAT/PuLP would succeed |
| Production schedules | Quality matters more than speed |

---

## Key Characteristics

### Always Succeeds (Sort Of)

Greedy never returns "infeasible." It returns whatever it managed to assign, even if that's 60% coverage. This has tradeoffs:

- Upside: Always produces *something* to start from
- Downside: Partial schedules may go unnoticed

Always check the `coverage_rate` in statistics.

### Deterministic

Same inputs → same outputs. No randomness. This makes debugging easy but means you can't "retry for a better result."

### No Backtracking

Once greedy assigns Resident X to Block A, it never reconsiders. If that choice makes Block B impossible, too bad.

CP-SAT and PuLP can backtrack. Greedy cannot.

### Generates Explanations

Unique feature: greedy logs *why* each decision was made.

```python
result.explanations[(resident_id, block_id)] = {
    "confidence": "high",  # or "medium", "low"
    "trade_off_summary": "Selected for equity (fewest assignments)",
    "alternatives_considered": [...],
    "constraint_evaluations": [...]
}
```

Useful for audits and debugging.

---

## Performance

| Problem Size | Expected Runtime |
|--------------|------------------|
| <100 blocks | <0.1 seconds |
| <1,000 blocks | 0.1-1 seconds |
| <10,000 blocks | 1-10 seconds |

Greedy is O(blocks × residents × templates), roughly linear in practice.

---

## Common Pitfalls

### 1. Assuming 100% Coverage

Greedy might skip blocks if no valid assignment exists at that moment. Always check:

```python
if result.statistics["coverage_rate"] < 0.95:
    logger.warning("Greedy achieved only partial coverage")
```

### 2. Template Concentration

Early versions assigned everything to the first valid template. Now fixed: picks template with fewest total assignments. But if one template has much higher capacity, it may still dominate.

### 3. Greedy Myopia

Example:
- Block A: Residents X, Y eligible
- Block B: Only Resident X eligible
- Greedy processes A first, assigns X
- Block B now impossible

CP-SAT would see this coming. Greedy doesn't.

### 4. No Soft Constraints

Greedy either satisfies a constraint or doesn't. There's no "penalty for violation" like in CP-SAT. If you need soft constraints, use a different solver.

---

## Tuning Greedy

### There's Not Much to Tune

Greedy has few parameters:
- `timeout_seconds`: Rarely hit (it's fast)
- `generate_explanations`: Enable for debugging, disable for speed

The algorithm itself is fixed. If greedy isn't working, switch solvers.

### Improving Results

1. **Pre-filter templates:** Remove templates that shouldn't be assigned
2. **Pre-sort residents:** If you have preferences, encode them in availability
3. **Use as seed:** Run greedy, then feed result to CP-SAT as warm start

---

## Comparison to Other Solvers

| Aspect | Greedy | PuLP | CP-SAT |
|--------|--------|------|--------|
| Speed | Fastest | Fast | Slowest |
| Optimality | No guarantee | Good | Optimal (if found) |
| Backtracking | No | Yes | Yes |
| Soft constraints | No | Limited | Full support |
| Explanations | Yes | No | No |
| Dependencies | None | PuLP package | OR-Tools |

---

## Decision Guide

```
Need a schedule in <1 second?
  → Use Greedy

Need to explain every decision?
  → Use Greedy

Need optimal or near-optimal?
  → Use CP-SAT

Need guaranteed coverage?
  → Use CP-SAT or Hybrid

Just exploring/prototyping?
  → Use Greedy
```

---

## Summary

Greedy is the **fast, dumb, transparent** solver:
- Fast: Sub-second for most problems
- Dumb: No global optimization, no backtracking
- Transparent: Full explanation of every decision

Use it for prototyping, debugging, and when speed matters more than quality. For production schedules, use CP-SAT or Hybrid.

---

*Document created January 2026.*
