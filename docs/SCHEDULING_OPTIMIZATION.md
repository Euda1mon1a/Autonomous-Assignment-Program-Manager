# Scheduling Algorithm Optimization

## Document Purpose

This document analyzes the current scheduling engine implementation, identifies bottlenecks and limitations, and proposes optimization strategies using constraint programming (CP-SAT).

**Author:** Opus 4.5 (Strategic Architect)
**Status:** RESEARCH IN PROGRESS
**Last Updated:** 2024-12-13

---

## Table of Contents

1. [Current Implementation Analysis](#current-implementation-analysis)
2. [Complexity Analysis](#complexity-analysis)
3. [Identified Bottlenecks](#identified-bottlenecks)
4. [OR-Tools/CP-SAT Overview](#or-toolscp-sat-overview)
5. [Proposed Optimization Strategy](#proposed-optimization-strategy)
6. [CP-SAT Implementation Design](#cp-sat-implementation-design)
7. [Migration Path](#migration-path)
8. [Performance Expectations](#performance-expectations)

---

## Current Implementation Analysis

### Overview

The current scheduling engine (`backend/app/scheduling/engine.py`) uses a **greedy algorithm** with the following phases:

| Phase | Description | Implementation |
|-------|-------------|----------------|
| Phase 0 | Absence loading | Build availability matrix from absences |
| Phase 1 | Block creation | Ensure half-day blocks exist for date range |
| Phase 2 | Resident assignment | Greedy assignment with equity tracking |
| Phase 3 | Faculty assignment | Supervision ratio enforcement |
| Phase 4 | Validation | ACGME compliance checking |

### Current Algorithm: Greedy Assignment

```python
# Simplified logic from _assign_residents_greedy()
def _assign_residents_greedy(self, residents, templates, blocks):
    # Sort blocks by difficulty (fewest eligible residents = harder)
    sorted_blocks = sorted(blocks, key=lambda b: count_eligible(b))

    # Track assignments for equity
    assignment_counts = {r.id: 0 for r in residents}

    for block in sorted_blocks:
        eligible = [r for r in residents if is_available(r, block)]
        if not eligible:
            continue  # No one available - GAP

        # Select resident with fewest assignments (equity heuristic)
        selected = min(eligible, key=lambda r: assignment_counts[r.id])
        create_assignment(selected, block)
        assignment_counts[selected.id] += 1
```

### Strengths of Current Implementation

1. **Simple and fast** - O(n log n) for block sorting + O(b * r) for assignment
2. **Predictable behavior** - Easy to understand and debug
3. **Equity heuristic** - Attempts to balance workload across residents
4. **Difficulty-first ordering** - Handles constrained blocks before flexible ones

### Limitations of Current Implementation

1. **No backtracking** - Cannot undo poor early decisions
2. **Local optimization only** - No global view of constraint satisfaction
3. **No preference handling** - Cannot incorporate resident preferences
4. **Suboptimal coverage** - May leave gaps that could be filled with better assignment order
5. **No constraint negotiation** - If constraints conflict, silently fails
6. **Limited ACGME enforcement** - Validates after the fact, doesn't prevent violations

---

## Complexity Analysis

### Time Complexity

| Operation | Complexity | Notes |
|-----------|------------|-------|
| Block creation | O(d) | d = number of days |
| Availability matrix | O(p * b * a) | p=people, b=blocks, a=absences |
| Block sorting | O(b log b) | One-time sort |
| Greedy assignment | O(b * r) | b=blocks, r=residents |
| Faculty assignment | O(b * f) | f=faculty |
| Validation | O(a * v) | a=assignments, v=validators |
| **Total** | O(p * b * a) | Dominated by availability matrix |

### Current Performance Characteristics

For a typical academic year schedule:
- **Days:** ~365
- **Blocks:** ~730 (AM/PM per day)
- **Residents:** ~30
- **Faculty:** ~20
- **Absences:** ~200

**Estimated operations:** 730 * 50 * 200 = 7.3M operations for availability matrix

### Identified Performance Hotspots

1. **Availability matrix construction** (lines 144-196)
   - Triple nested loop: people × blocks × absences
   - No indexing on absences by person

2. **Database queries inside loops** (lines 294-296)
   - Queries Person table for each block during faculty assignment
   - Could be pre-loaded

3. **Commit per save** (lines 356-360)
   - Individual adds followed by single commit
   - Not a significant issue but could batch

---

## Identified Bottlenecks

### Algorithm Bottlenecks

#### 1. No Constraint Propagation

The greedy algorithm cannot "see ahead" to anticipate constraint violations.

**Example scenario:**
- Block A has only Resident X available
- Block B has Residents X and Y available
- Greedy processes B first (arbitrary), assigns X
- Block A now has NO eligible residents → coverage gap

**Impact:** Avoidable coverage gaps

#### 2. No Global Optimization

The algorithm optimizes locally (equity per assignment) without considering:
- Total coverage rate
- Minimizing constraint violations
- Balancing weekly workload patterns
- Minimizing consecutive shifts

#### 3. Rigid Constraint Handling

Current implementation has binary constraints (available/not available):
- No soft preferences (prefer but not require)
- No constraint relaxation when infeasible
- No explanation of why assignments failed

#### 4. Limited Faculty Assignment Logic

Faculty assignment (lines 273-322) uses simple ratio calculation:
- Doesn't consider faculty specialties vs. rotation needs
- Doesn't balance faculty workload over time
- Doesn't account for faculty preferences

### Data Model Bottlenecks

#### 1. Absence Lookup

Current: Linear scan of all absences for each person × block combination

```python
for absence in absences:
    if absence.person_id == person.id and ...:
```

**Improvement:** Index absences by person_id

#### 2. Resident Filtering

Each block iteration re-filters residents for availability.

**Improvement:** Pre-compute availability sets per block

---

## OR-Tools/CP-SAT Overview

### What is CP-SAT?

CP-SAT is Google's state-of-the-art constraint programming solver. It:
- Handles complex constraint combinations
- Proves optimality or provides bounds
- Supports multi-objective optimization
- Scales to large problems via parallel solving

### Why CP-SAT for Residency Scheduling?

| Requirement | Greedy | CP-SAT |
|-------------|--------|--------|
| ACGME compliance (80-hour weeks) | Validate after | Enforce during |
| Minimum rest periods | Not enforced | Hard constraint |
| Resident preferences | Not supported | Soft constraint |
| Fair workload distribution | Heuristic only | Optimized |
| Guaranteed coverage | Best effort | Maximized |
| Explain infeasibility | No | Yes |

### CP-SAT vs. Greedy Trade-offs

| Factor | Greedy | CP-SAT |
|--------|--------|--------|
| Speed | Fast (ms) | Moderate (seconds-minutes) |
| Solution quality | Acceptable | Optimal/near-optimal |
| Extensibility | Requires rewrite | Add constraints declaratively |
| Debugging | Easy | Requires solver knowledge |
| Determinism | Deterministic | Deterministic with seed |

---

## Proposed Optimization Strategy

### Hybrid Approach

We recommend a **hybrid strategy** that uses:
1. **Greedy** for initial draft schedules (fast feedback)
2. **CP-SAT** for optimized schedules (production quality)

### User-Facing Options

```
Algorithm Selection:
┌─────────────────────────────────────────────────────────┐
│  ○ Quick Draft (Greedy)         ~1 second              │
│     Fast initial schedule, may have coverage gaps       │
│                                                         │
│  ● Optimized (CP-SAT)           ~30 seconds            │
│     Best possible schedule, enforces all constraints    │
│                                                         │
│  ○ Repair Existing              ~10 seconds            │
│     Fix violations in current schedule                  │
└─────────────────────────────────────────────────────────┘
```

### Phased Implementation

**Phase 1: Parallel Implementation**
- Implement CP-SAT solver alongside existing greedy
- Both algorithms available, user chooses
- Greedy remains default for quick iterations

**Phase 2: CP-SAT Enhancement**
- Add preference handling
- Add constraint explanation
- Add incremental scheduling (modify existing schedules)

**Phase 3: CP-SAT Default**
- Make CP-SAT the default for final schedules
- Greedy only for quick drafts
- Add real-time constraint checking during manual edits

---

## CP-SAT Implementation Design

### Decision Variables

```python
from ortools.sat.python import cp_model

class CPSATScheduler:
    def __init__(self, db: Session, start_date: date, end_date: date):
        self.model = cp_model.CpModel()
        self.solver = cp_model.CpSolver()

        # Assignment variables: resident r assigned to block b
        # shifts[(r, b)] = BoolVar
        self.shifts: dict[tuple[UUID, UUID], cp_model.IntVar] = {}

        # Supervision variables: faculty f supervises block b
        # supervision[(f, b)] = BoolVar
        self.supervision: dict[tuple[UUID, UUID], cp_model.IntVar] = {}
```

### Hard Constraints

#### 1. Availability (Absences)

```python
def add_availability_constraints(self):
    """Residents cannot work during approved absences."""
    for (resident_id, block_id), var in self.shifts.items():
        if not self.is_available(resident_id, block_id):
            self.model.Add(var == 0)
```

#### 2. Single Assignment Per Block Per Person

```python
def add_single_assignment_constraints(self):
    """Each person works at most one shift per half-day block."""
    for block_id in self.block_ids:
        for resident_id in self.resident_ids:
            # Already boolean - just one shift type per block
            pass  # Implicit in variable structure
```

#### 3. ACGME 80-Hour Week Limit

```python
def add_duty_hour_constraints(self):
    """Maximum 80 hours per week (ACGME requirement)."""
    HOURS_PER_BLOCK = 4  # Half-day = 4 hours
    MAX_WEEKLY_HOURS = 80
    MAX_BLOCKS_PER_WEEK = MAX_WEEKLY_HOURS // HOURS_PER_BLOCK  # 20 blocks

    for resident_id in self.resident_ids:
        for week_start in self.week_starts:
            week_blocks = self.get_blocks_in_week(week_start)
            self.model.Add(
                sum(self.shifts[(resident_id, b)] for b in week_blocks)
                <= MAX_BLOCKS_PER_WEEK
            )
```

#### 4. Minimum Rest Between Shifts

```python
def add_rest_constraints(self):
    """Minimum 8 hours between shifts (no back-to-back PM→AM)."""
    for resident_id in self.resident_ids:
        for day in self.days:
            pm_block = self.get_block(day, "PM")
            next_am_block = self.get_block(day + 1, "AM")

            if pm_block and next_am_block:
                # Can't work PM and next day AM
                self.model.Add(
                    self.shifts[(resident_id, pm_block)]
                    + self.shifts[(resident_id, next_am_block)]
                    <= 1
                )
```

#### 5. Supervision Ratios

```python
def add_supervision_constraints(self):
    """Enforce ACGME supervision ratios."""
    for block_id in self.block_ids:
        # Count PGY-1 residents assigned to this block
        pgy1_count = sum(
            self.shifts[(r, block_id)]
            for r in self.pgy1_residents
        )
        # Count other residents
        other_count = sum(
            self.shifts[(r, block_id)]
            for r in self.other_residents
        )

        # Required faculty: 1:2 for PGY-1, 1:4 for others
        # faculty_needed >= ceil(pgy1/2) + ceil(others/4)
        faculty_assigned = sum(
            self.supervision[(f, block_id)]
            for f in self.faculty_ids
        )

        # Linear approximation of ceiling
        self.model.Add(2 * faculty_assigned >= pgy1_count)
        self.model.Add(4 * faculty_assigned >= other_count)
```

### Soft Constraints (Optimization Objectives)

```python
def build_objective(self):
    """Multi-objective optimization."""
    objective_terms = []

    # 1. Maximize coverage (weight: 1000)
    for block_id in self.block_ids:
        coverage = sum(
            self.shifts[(r, block_id)]
            for r in self.resident_ids
        )
        objective_terms.append(1000 * coverage)

    # 2. Minimize workload variance (weight: 10)
    # Penalize deviation from average
    avg_shifts = len(self.block_ids) // len(self.resident_ids)
    for resident_id in self.resident_ids:
        total_shifts = sum(
            self.shifts[(resident_id, b)]
            for b in self.block_ids
        )
        deviation = self.model.NewIntVar(-100, 100, f'dev_{resident_id}')
        self.model.Add(deviation == total_shifts - avg_shifts)
        abs_deviation = self.model.NewIntVar(0, 100, f'abs_dev_{resident_id}')
        self.model.AddAbsEquality(abs_deviation, deviation)
        objective_terms.append(-10 * abs_deviation)

    # 3. Satisfy preferences (weight: 1)
    for (resident_id, block_id), preference in self.preferences.items():
        objective_terms.append(preference * self.shifts[(resident_id, block_id)])

    self.model.Maximize(sum(objective_terms))
```

### Solver Configuration

```python
def solve(self, time_limit_seconds: int = 30) -> dict:
    """Run the solver with time limit."""
    self.solver.parameters.max_time_in_seconds = time_limit_seconds
    self.solver.parameters.num_search_workers = 8  # Parallel solving
    self.solver.parameters.log_search_progress = True

    status = self.solver.Solve(self.model)

    if status == cp_model.OPTIMAL:
        return self._extract_solution("optimal")
    elif status == cp_model.FEASIBLE:
        return self._extract_solution("feasible")
    elif status == cp_model.INFEASIBLE:
        return self._handle_infeasible()
    else:
        return {"status": "failed", "message": "No solution found"}
```

---

## Migration Path

### Step 1: Refactor Data Loading

Extract data loading from algorithm:

```python
# Before: Everything in SchedulingEngine
# After: Separate concerns

class ScheduleData:
    """Loaded data for scheduling algorithms."""
    blocks: list[Block]
    residents: list[Person]
    faculty: list[Person]
    templates: list[RotationTemplate]
    availability: dict[tuple[UUID, UUID], bool]

class GreedyScheduler:
    def generate(self, data: ScheduleData) -> list[Assignment]:
        ...

class CPSATScheduler:
    def generate(self, data: ScheduleData) -> list[Assignment]:
        ...
```

### Step 2: Add Algorithm Selection

```python
# backend/app/scheduling/engine.py

class SchedulingEngine:
    ALGORITHMS = {
        "greedy": GreedyScheduler,
        "cp_sat": CPSATScheduler,
    }

    def generate(self, algorithm: str = "greedy", ...) -> dict:
        data = self._load_data()
        scheduler = self.ALGORITHMS[algorithm]()
        assignments = scheduler.generate(data)
        return self._save_and_validate(assignments)
```

### Step 3: Install Dependencies

```bash
pip install ortools>=9.8
```

Add to `requirements.txt`:
```
ortools>=9.8
```

### Step 4: Implement CP-SAT Scheduler

Create `backend/app/scheduling/cpsat_scheduler.py` with the implementation above.

### Step 5: Add API Support

```python
# backend/app/api/routes/schedule.py

@router.post("/generate")
def generate_schedule(
    request: ScheduleGenerateRequest,
    algorithm: str = Query("greedy", enum=["greedy", "cp_sat"]),
    ...
):
    engine = SchedulingEngine(db, request.start_date, request.end_date)
    return engine.generate(algorithm=algorithm, ...)
```

---

## Performance Expectations

### Benchmark Estimates

Based on similar healthcare scheduling problems:

| Problem Size | Greedy | CP-SAT (30s limit) |
|--------------|--------|-------------------|
| 1 week, 10 residents | <100ms | 1-2s |
| 1 month, 30 residents | <500ms | 5-15s |
| 3 months, 30 residents | <1s | 20-60s |
| 1 year, 30 residents | <2s | 2-5 min |

### Quality Comparison (Expected)

| Metric | Greedy | CP-SAT |
|--------|--------|--------|
| Coverage rate | 85-95% | 98-100% |
| Workload variance (std dev) | 15-20% | 5-10% |
| ACGME violations | 5-15 | 0 |
| Preference satisfaction | N/A | 70-90% |

### Recommended Time Limits

| Use Case | Time Limit | Algorithm |
|----------|------------|-----------|
| Quick preview | 1s | Greedy |
| Draft schedule | 10s | CP-SAT |
| Final schedule | 60s | CP-SAT |
| Batch generation | 5 min | CP-SAT |

---

## Next Steps

1. **Immediate:** Refactor data loading into `ScheduleData` class
2. **Week 1:** Implement basic CP-SAT scheduler with hard constraints
3. **Week 2:** Add soft constraints and objective function
4. **Week 3:** Integration testing and performance tuning
5. **Week 4:** UI for algorithm selection, progress feedback

---

## References

- [OR-Tools Documentation](https://developers.google.com/optimization)
- [CP-SAT Primer](https://github.com/d-krupke/cpsat-primer)
- [Employee Scheduling with OR-Tools](https://developers.google.com/optimization/scheduling/employee_scheduling)
- [ACGME Duty Hour Requirements](https://www.acgme.org/what-we-do/accreditation/common-program-requirements/)

---

*End of Scheduling Optimization Document*
