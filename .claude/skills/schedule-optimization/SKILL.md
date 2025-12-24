---
name: schedule-optimization
description: Multi-objective schedule optimization expertise using constraint programming and Pareto optimization. Use when generating schedules, improving coverage, balancing workloads, or resolving conflicts. Integrates with OR-Tools solver and resilience framework.
---

# Schedule Optimization Skill

Expert knowledge for generating and optimizing medical residency schedules using constraint programming and multi-objective optimization.

## Solver Status (2025-12-24) - ALL FIXED

| Issue | Status | Fix Applied |
|-------|--------|-------------|
| Greedy template selection | FIXED | Selects template with fewest assignments |
| CP-SAT no template balance | FIXED | Added template_balance_penalty to objective |
| Template filtering missing | FIXED | `_get_rotation_templates()` defaults to `activity_type="clinic"` |

See `backend/app/scheduling/solvers.py` header for implementation details.

## Architecture: Block vs Half-Day Scheduling

**IMPORTANT:** This system has two distinct scheduling modes:

| Mode | Rotations | Assignment Unit | Solver Role |
|------|-----------|-----------------|-------------|
| **Block-Assigned** | FMIT, NF, Inpatient, NICU | Full block or half-block | Pre-assigned, NOT optimized |
| **Half-Day Optimized** | Clinic, Specialty | Half-day (AM/PM) | Solver optimizes these |

**The solvers are ONLY for outpatient half-day optimization.** Block-assigned rotations
are handled separately and should NOT be passed to the solver.

If solver assigns everyone to NF/PC/inpatient, check that templates are filtered
to `activity_type == "clinic"` in `engine._get_rotation_templates()`.

### Night Float (NF) Half-Block Mirrored Pairing

NF has idiosyncratic half-block constraints - residents are paired in mirrored patterns:

```
Block 5 (4 weeks):
├── Half 1 (Days 1-14)     ├── Half 2 (Days 15-28)
│                          │
│ Resident A: NF           │ Resident A: NICU (or elective)
│ Resident B: NEURO        │ Resident B: NF
```

**Key rules:**
- NF is assigned per **half-block** (2 weeks), not full block
- Residents are **mirrored pairs**: one on NF half 1, partner on NF half 2
- The non-NF half is a mini 2-week rotation (NICU, NEURO, elective)
- **Post-Call (PC)** day required after NF ends (Day 15 or Day 1 of next block)
- Exactly 1 resident on NF per half-block

**Files:** See `backend/app/scheduling/constraints/night_float_post_call.py` and
`docs/development/CODEX_SYSTEM_OVERVIEW.md` for full NF/PC constraint logic.

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

## REQUIRED: Documentation After Each Step

**Every scheduling task MUST include documentation updates.** This prevents knowledge loss
between sessions and ensures issues are tracked properly.

### Documentation Checkpoint Protocol

After EACH significant step, document:

1. **What was attempted** - The specific action or fix tried
2. **What happened** - Actual results (success, failure, unexpected behavior)
3. **What was learned** - New understanding of the system
4. **What needs to happen next** - Remaining work or blockers

### Where to Document

| Finding Type | Location | Example |
|--------------|----------|---------|
| Bug/Known Issue | `solvers.py` header | Template selection bug |
| Architecture insight | This skill file | Block vs half-day modes |
| Workaround | Code comments + skill | Manual adjustment needed |
| Fix needed | TODO in code + HUMAN_TODO.md | Template filtering |

### Planning Template

When starting a scheduling task, create a plan that includes documentation:

```markdown
## Task: [Description]

### Phase 1: Investigation
- [ ] Explore current state
- [ ] Document findings in [location]

### Phase 2: Implementation
- [ ] Make changes
- [ ] Document what changed in commit message

### Phase 3: Verification
- [ ] Test the changes
- [ ] Document results (success/failure)

### Phase 4: Documentation Update
- [ ] Update skill if new knowledge gained
- [ ] Update code comments if behavior clarified
- [ ] Update HUMAN_TODO.md if manual work needed
```

### Anti-Pattern: Silent Failures

**DO NOT:**
- Discover an issue and only mention it in chat
- Switch to a "workaround" without documenting why
- Assume the next session will remember context

**DO:**
- Add issues to code headers immediately
- Update skill files with architectural insights
- Create explicit TODOs for unfixed problems
