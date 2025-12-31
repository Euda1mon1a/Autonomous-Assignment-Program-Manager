# SCHEDULER Agent - Comprehensive Enhanced Specification

> **G2_RECON SEARCH_PARTY Operation**
> **Status**: Comprehensive Documentation
> **Version**: 2.0 Enhanced
> **Last Updated**: 2025-12-30
> **Purpose**: Complete agent specification with constraint catalog, algorithm patterns, and operational guidance

---

## Table of Contents

1. [Overview & Mission](#overview--mission)
2. [Core Competencies](#core-competencies)
3. [Complete Constraint Catalog](#complete-constraint-catalog)
4. [Algorithm Deep Dive](#algorithm-deep-dive)
5. [Solver Patterns & Selection](#solver-patterns--selection)
6. [Constraint Implementation Patterns](#constraint-implementation-patterns)
7. [Infeasibility Detection & Recovery](#infeasibility-detection--recovery)
8. [Scheduling Philosophy](#scheduling-philosophy)
9. [Advanced Capabilities](#advanced-capabilities)
10. [Integration Patterns](#integration-patterns)
11. [Best Practices & Pitfalls](#best-practices--pitfalls)
12. [Operational Playbooks](#operational-playbooks)

---

## Overview & Mission

### The SCHEDULER Agent Role

**SCHEDULER** is the operational agent responsible for generating, optimizing, and maintaining ACGME-compliant resident schedules while balancing clinical coverage, educational value, and individual preferences. This agent is a **constraint satisfaction specialist** with deep domain knowledge in medical scheduling, residency program operations, and regulatory compliance.

### Core Mission Statement

"Generate fair, compliant, and operationally sound medical residency schedules through constraint-based optimization, while maintaining human-centered design principles that respect both institutional needs and resident wellbeing."

### Why This Agent Exists

Medical residency scheduling is a **complex constraint satisfaction problem** that requires:

1. **Regulatory Compliance**: ACGME rules are non-negotiable (80-hour limits, 1-in-7 days off, supervision ratios)
2. **Fairness Optimization**: Balance workload across cohorts to prevent burnout
3. **Coverage Guarantees**: Ensure all clinical services are adequately staffed
4. **Educational Goals**: Provide rotation diversity for competency development
5. **Resilience Engineering**: Design schedules that can absorb personnel losses
6. **Transparency**: Explain scheduling decisions in human terms

---

## Core Competencies

### Competency 1: Constraint Modeling & Composition

**Mastery Level**: Expert

The SCHEDULER agent understands that **all scheduling rules are constraints** that can be:

- **Hard constraints**: Must be satisfied (ACGME compliance, availability)
- **Soft constraints**: Optimized within hard constraint bounds (fairness, preferences)

**Key Skill**: Composing diverse constraint sets into unified satisfaction problems

```
Example: Block 10 Schedule
├─ Hard Constraints (must satisfy all):
│  ├─ ACGME: 80-hour rule, 1-in-7 rule
│  ├─ Availability: Respect leaves, deployments
│  ├─ Supervision: 1:2 PGY-1, 1:4 PGY-2/3
│  ├─ Capacity: ≤1 rotation per block per resident
│  ├─ Call Coverage: Exactly 1 faculty overnight each night
│  └─ Credential Requirements: Slot-type invariants
│
└─ Soft Constraints (optimize within hard bounds):
   ├─ Equity: Fair call distribution
   ├─ Continuity: Prefer consecutive blocks
   ├─ Coverage: Maximize blocks assigned
   ├─ Preferences: Honored when possible (60%+ target)
   └─ Resilience: Protect critical faculty, N-1 viable
```

### Competency 2: Multi-Solver Strategy

**Mastery Level**: Expert

The agent selects the **right solver for the right problem**:

| Scenario | Solver | Rationale |
|----------|--------|-----------|
| Demo/explanation needed | Greedy | Fast, transparent, human-explainable |
| Small Block (< 500 blocks) | CP-SAT | Optimal solution in seconds |
| Medium schedule (500-2000 blocks) | CP-SAT with timeout | Best quality with reliability |
| Large/complex problem | Hybrid | CP-SAT → fallback to PuLP |
| Performance critical | PuLP | Fast linear programming |
| Quality optimization | CP-SAT (60s+) | Wait for optimal or near-optimal |

**Key Skill**: Complexity estimation → solver selection → execution → fallback handling

### Competency 3: ACGME Compliance Expertise

**Mastery Level**: Master (regulatory domain expert)

The agent has **internalized ACGME rules** and can:

- Translate regulations into constraint equations
- Detect compliance violations in O(n) time
- Explain violations in clinician-friendly terms
- Propose compliant alternatives when violations detected
- Audit schedules for edge cases (NF→PC transitions, Sunday call patterns)

**Key Rules Mastered**:

1. **80-Hour Rule**: Max 80 hours/week averaged over rolling 28-day windows
   - Implementation: ≤53 blocks per 28-day window (6 hrs/block × 53 = 318 hrs ≈ 75 hrs/week)
   - Edge case: Boundary shifts (check all possible 28-day windows, not just calendar weeks)

2. **1-in-7 Rule**: One 24-hour period off every 7 days
   - Implementation: Max 6 consecutive assigned days
   - Edge case: Off-day can be partial (conference during workday doesn't break continuity)

3. **Supervision Ratios**:
   - PGY-1: 1 faculty per 2 residents (≤2:1)
   - PGY-2/3: 1 faculty per 4 residents (≤4:1)
   - Edge case: Faculty count changes per block (inpatient vs. clinic)

4. **Availability**: Respect absences (blocking vs. partial)
   - Blocking: Deployment, TDY, extended medical leave → no assignment
   - Partial: Vacation, conference → assignment possible but flagged

### Competency 4: Resilience Integration

**Mastery Level**: Proficient (Tier 1 & 2)

The agent integrates **cross-disciplinary resilience principles**:

- **Hub Protection**: Avoid over-assigning critical faculty (network centrality analysis)
- **Utilization Buffering**: Keep system < 80% utilized (queuing theory - prevent cascade failures)
- **N-1 Contingency**: Schedule must be viable if any faculty becomes unavailable
- **Preference Trails (Stigmergy)**: Track historical preferences to guide future assignments
- **Zone-Based Blast Radius**: Contain failures to isolated regions (defense in depth)

**Integration Pattern**:

```python
# Pre-generation: Check resilience health
health_score = resilience_service.get_health()
assert health_score >= 0.7, "System not healthy for schedule generation"

# During generation: Apply resilience constraints
constraint_manager.add(HubProtectionConstraint(max_utilization=0.8))
constraint_manager.add(UtilizationBufferConstraint(target_utilization=0.70))
constraint_manager.add(N1VulnerabilityConstraint())

# Post-generation: Validate N-1 compliance
n1_analysis = resilience_service.analyze_n1_contingency(generated_schedule)
assert n1_analysis.compliant, "Schedule not resilient to single faculty loss"
```

### Competency 5: Swap Management

**Mastery Level**: Expert

The agent processes **faculty-requested schedule swaps** with full validation:

1. **Request Validation**: Both parties exist, authorized, shifts match
2. **ACGME Pre-Check**: Simulate swap, verify neither party violates 80-hour or 1-in-7
3. **Credential Verification**: Ensure both meet slot requirements
4. **Cascade Detection**: Identify dependent swaps and domino effects
5. **Coverage Impact**: Ensure minimum staffing maintained
6. **Execution**: Atomic transaction with row-level locking
7. **Rollback Window**: 24-hour reversal capability

**Key Pattern**: Never assume a swap is safe until simulated and validated

### Competency 6: Emergency Coverage

**Mastery Level**: Expert

The agent responds to **sudden resident unavailability** (TDY, medical emergency):

```
Immediate Response (< 15 min):
  1. Identify affected shifts (next 7 days)
  2. Calculate coverage gaps
  3. Alert faculty

Find Coverage (< 60 min):
  1. Query eligible replacements:
     - Same PGY level preferred
     - Under 80-hour weekly limit
     - Meets credential requirements
  2. Auto-match if single candidate
  3. Present options if multiple matches

Execute Replacement:
  1. Get faculty approval (if < 24hr notice)
  2. Execute swap atomically
  3. Triple-check ACGME compliance
  4. Send urgent notifications

Long-Term Adjustment:
  1. If absence > 2 weeks: trigger full schedule regeneration
  2. Rebalance workload across team
  3. Document accommodation in audit log
```

---

## Complete Constraint Catalog

### Hard Constraints (MUST Satisfy All)

#### 1. Availability Constraint (CRITICAL)

**File**: `backend/app/scheduling/constraints/acgme.py`

**Purpose**: Enforce absence tracking. Residents cannot be assigned during blocking absences.

**Implementation**:

```python
def add_to_cpsat(self, model, variables, context):
    """For each (resident, block) where unavailable, add: x[r, b] == 0"""
    for resident in context.residents:
        for block in context.blocks:
            if not context.availability[resident.id].get(block.id, {}).get('available'):
                model.Add(x[resident_idx, block_idx] == 0)
```

**Edge Cases**:
- **Partial absences** (vacation, conference): Resident can be assigned but it's suboptimal
- **Blocking absences** (deployment, TDY, medical): Resident cannot be assigned
- **Absence transitions**: Day of absence vs. day after (when do hour calculations include it?)

**Performance Impact**: O(n_residents × n_blocks) constraints added

#### 2. 80-Hour Rule Constraint (CRITICAL)

**File**: `backend/app/scheduling/constraints/acgme.py`

**Purpose**: Enforce maximum 80 hours/week averaged over rolling 28-day windows.

**Calculation**:
- 1 block = 6 hours
- Max blocks per 28 days = 53 (gives 318 total hours = 75 avg hrs/week)
- Checks ALL possible 28-day windows, not just calendar weeks

**Implementation**:

```python
def add_to_cpsat(self, model, variables, context):
    """For each 28-day rolling window, ensure <= 53 blocks assigned"""
    for start_date in all_possible_start_dates:
        window_end = start_date + timedelta(days=27)  # 28 days inclusive
        blocks_in_window = [b for b in context.blocks
                           if start_date <= b.date <= window_end]

        for resident in context.residents:
            assignments_in_window = sum(
                x[resident_idx, block_idx] for block_idx in blocks_in_window
            )
            model.Add(assignments_in_window <= 53)
```

**Edge Cases**:
- **Boundary windows**: Check starting on every possible day, not just Sundays
- **Leap year handling**: Use 365/366 days appropriately
- **Off-day partial counting**: How much of a day off counts toward the limit?

**Performance Impact**: O(n_windows × n_residents) constraints (expensive but critical)

#### 3. One-in-Seven Rule Constraint (CRITICAL)

**File**: `backend/app/scheduling/constraints/acgme.py`

**Purpose**: Ensure at least one 24-hour period off every 7 days.

**Implementation**:

```python
def add_to_cpsat(self, model, variables, context):
    """For each 7-day rolling window, ensure >= 1 day off"""
    for start_date in all_seven_day_windows:
        blocks_in_window = [b for b in context.blocks
                           if start_date <= b.date <= start_date + timedelta(days=6)]

        for resident in context.residents:
            # Max consecutive assigned days = 6
            # (leaves at least 1 day off in 7-day period)
            assignments = sum(
                x[resident_idx, block_idx] for block_idx in blocks_in_window
            )
            model.Add(assignments <= 6)
```

**Edge Cases**:
- **Off-day definition**: Is 1 AM → 11:59 PM consecutive? What about midnight shifts?
- **Boundary crossings**: Off-day spanning multiple calendar days
- **Partial off-days**: Conference day (works morning, off afternoon) - counts as off?

**Performance Impact**: O(n_windows × n_residents) constraints

#### 4. Supervision Ratio Constraint (CRITICAL)

**File**: `backend/app/scheduling/constraints/acgme.py`

**Purpose**: Enforce faculty-to-resident supervision ratios per ACGME requirements.

**Implementation**:

```python
def add_to_cpsat(self, model, variables, context):
    """For each block, ensure faculty count meets ratios"""
    for block in context.blocks:
        pgy1_residents = [r for r in context.residents if r.pgy_level == 1]
        pgy23_residents = [r for r in context.residents if r.pgy_level in [2, 3]]

        # Count faculty assignments
        faculty_count = sum(
            x[faculty_idx, block_idx] for faculty in context.faculty
        )

        # Count residents
        pgy1_count = sum(
            x[resident_idx, block_idx] for resident in pgy1_residents
        )
        pgy23_count = sum(
            x[resident_idx, block_idx] for resident in pgy23_residents
        )

        # PGY-1: 1 faculty per 2 residents
        model.Add(faculty_count >= (pgy1_count + 1) // 2)

        # PGY-2/3: 1 faculty per 4 residents
        model.Add(faculty_count >= (pgy23_count + 3) // 4)
```

**Edge Cases**:
- **Mixed cohorts**: PGY-1 and PGY-2/3 in same block - which ratio applies?
- **Partial faculty**: Teaching fellow, adjunct - count as full faculty?
- **Block-by-block vs. daily**: Do ratios apply to AM and PM separately?

**Performance Impact**: O(n_blocks × n_faculty) constraints

#### 5. Capacity Constraint (CRITICAL)

**File**: `backend/app/scheduling/constraints/capacity.py`

**Purpose**: Ensure at most 1 rotation per block per resident.

**Implementation** (Most Basic Constraint):

```python
def add_to_cpsat(self, model, variables, context):
    """For each (resident, block), ensure <= 1 rotation"""
    for resident in context.residents:
        for block in context.blocks:
            assignments_for_rb = sum(
                x[resident_idx, block_idx, template_idx]
                for template in context.templates
            )
            model.Add(assignments_for_rb <= 1)
```

**Edge Cases**:
- **Multi-template blocks**: Can a block have multiple rotation types? (usually no)
- **Partial assignments**: Morning clinic + afternoon procedures on same day?

**Performance Impact**: O(n_residents × n_blocks) constraints

#### 6. Overnight Call Generation Constraint (HIGH)

**File**: `backend/app/scheduling/constraints/overnight_call.py`

**Purpose**: Ensure exactly one faculty is assigned overnight call each night (Sun-Thurs).

**Implementation**:

```python
def add_to_cpsat(self, model, variables, context):
    """For each night, ensure exactly 1 faculty on call"""
    for block in sunday_thursday_blocks:
        faculty_on_call = sum(
            x[faculty_idx, block_idx, "call_template"]
            for faculty in context.faculty
        )
        model.Add(faculty_on_call == 1)  # Exactly 1
```

**Edge Cases**:
- **Friday night coverage**: Sometimes needed (Friday→Saturday transition)
- **Holiday nights**: Special staffing rules
- **Faculty call capability**: Some faculty not eligible for overnight call

**Performance Impact**: O(n_nights) constraints

#### 7. FMIT Constraints (HIGH)

**Files**: `backend/app/scheduling/constraints/fmit.py`

**Purpose**: Family Medicine Inpatient Track (FMIT) has special scheduling rules.

**Constraints**:

1. **FMIT Blocking**: FMIT faculty cannot do overnight call (Sun-Thurs) during FMIT week
2. **FMIT Continuity**: FMIT faculty stay same rotation for entire FMIT block
3. **Post-FMIT Recovery**: Reduced call load for 1 week post-FMIT
4. **Staffing Floor**: Minimum X FMIT faculty scheduled per block

**Implementation Example** (FMIT Blocking):

```python
def add_to_cpsat(self, model, variables, context):
    """Block FMIT faculty from overnight call during FMIT week"""
    fmit_faculty = [f for f in context.faculty if "FMIT" in f.roles]
    fmit_blocks = [b for b in context.blocks if is_fmit_week(b.date)]

    for faculty in fmit_faculty:
        for block in fmit_blocks:
            if is_overnight_call_block(block):
                model.Add(x[faculty_idx, block_idx, "call"] == 0)
```

**Edge Cases**:
- **FMIT faculty eligibility**: Who counts as FMIT faculty?
- **Post-FMIT window**: Exactly 7 days? Or until next FMIT?
- **Multiple FMIT rotations**: Faculty with both clinic AND inpatient duties?

#### 8. Post-Call Constraints (HIGH)

**File**: `backend/app/scheduling/constraints/post_call.py`

**Purpose**: Manage post-call scheduling (residents shouldn't work heavy duties after overnight call).

**Constraints**:

1. **Post-Call Day Off**: After overnight call, resident gets lighter duty or full day off
2. **Post-Call Auto-Assignment**: Auto-assign post-call duty to minimize conflicts
3. **Night Float → Post-Call Transition**: Audit and enforce NF→PC transitions

**Edge Cases**:
- **Definition of "post-call"**: Exact 24-hour window? Or calendar day?
- **Continuity of care**: Can't always give full day off after call
- **NF→PC audit**: Night Float to Post-Call transitions must be compliant

### Soft Constraints (Optimize Within Hard Bounds)

#### 1. Equity Constraint

**File**: `backend/app/scheduling/constraints/equity.py`

**Purpose**: Balance workload across residents to prevent burnout.

**Implementation**:

```python
def get_soft_penalty(assignments, context):
    """Calculate equity penalty (squared deviation from mean)"""
    blocks_per_resident = [
        sum(assignments for r, b in assignments if r == resident)
        for resident in context.residents
    ]
    mean_blocks = sum(blocks_per_resident) / len(context.residents)
    variance = sum((b - mean_blocks)**2 for b in blocks_per_resident)
    return variance  # Penalty: lower variance is better
```

**Weight**: 10 (high priority - fairness is critical for morale)

**Target**: Call distribution variance ≤ 1σ (most residents within ±1 call of median)

#### 2. Continuity Constraint

**File**: `backend/app/scheduling/constraints/equity.py`

**Purpose**: Prefer consecutive rotation assignments (minimize mid-week rotation changes).

**Implementation**:

```python
def get_soft_penalty(assignments, context):
    """Penalize fragmented assignments"""
    penalty = 0
    for resident in context.residents:
        # Find all rotation sequences for resident
        for sequence in get_assignment_sequences(resident):
            # Count "breaks" in sequence (switches to different rotation)
            breaks = count_rotation_changes(sequence)
            penalty += breaks  # Higher penalty for more fragmentation
    return penalty
```

**Weight**: 5 (medium priority - nice to have but not critical)

#### 3. Coverage Constraint

**File**: `backend/app/scheduling/constraints/capacity.py`

**Purpose**: Maximize blocks assigned (coverage completeness).

**Implementation**:

```python
def get_soft_objective(assignments, context):
    """Maximize number of blocks assigned"""
    return sum(assignments)  # Primary objective: maximize coverage
```

**Weight**: 1000 (highest - coverage is primary goal)

**Target**: 100% block assignment (all blocks covered)

#### 4. Call Equity Constraints

**File**: `backend/app/scheduling/constraints/call_equity.py`

**Constraints**:

1. **Sunday Call Equity**: Balance Sunday call burden across faculty
2. **Weekday Call Equity**: Balance Mon-Thurs call across faculty
3. **Call Spacing**: Prevent back-to-back overnight calls (min 3-day spacing)

**Implementation** (Sunday Call Equity):

```python
def get_soft_penalty(assignments, context):
    """Penalize unequal Sunday call distribution"""
    sunday_calls_per_faculty = {}
    for faculty in context.faculty:
        sunday_calls = sum(
            x[faculty_idx, block_idx, "call"]
            for block in sunday_blocks
        )
        sunday_calls_per_faculty[faculty.id] = sunday_calls

    # Penalize variance
    mean_calls = sum(sunday_calls_per_faculty.values()) / len(context.faculty)
    variance = sum(
        (calls - mean_calls)**2
        for calls in sunday_calls_per_faculty.values()
    )
    return variance
```

**Weight**: 10 (high - critical for faculty morale)

#### 5. Preference Trail Constraint (Stigmergy)

**File**: `backend/app/scheduling/constraints/resilience.py`

**Purpose**: Track historical preferences and guide future assignments (self-organizing system).

**Implementation**:

```python
def get_soft_penalty(assignments, context):
    """Track preferences, use to guide future assignments"""
    penalty = 0
    for resident in context.residents:
        pref_trail = context.preference_trails.get(resident.id, {})

        # Residents prefer rotations they've done before
        # Penalize unfamiliar rotations
        for assignment in assignments_for_resident:
            if assignment.template_id not in pref_trail:
                penalty += 1  # Unfamiliar rotation
            else:
                penalty -= 0.5  # Familiar rotation preferred

    return penalty
```

**Weight**: 2 (low - only matters when hard constraints satisfied)

#### 6. Resilience Soft Constraints

**File**: `backend/app/scheduling/constraints/resilience.py`

**Constraints**:

1. **Hub Protection**: Don't over-assign critical faculty (network centrality)
2. **Utilization Buffer**: Keep system < 80% utilized (prevent cascade failures)

**Implementation** (Hub Protection):

```python
def get_soft_penalty(assignments, context):
    """Penalize over-assignment of critical faculty"""
    penalty = 0
    for faculty in context.faculty:
        hub_score = context.hub_scores.get(faculty.id, 0.0)  # 0.0-1.0
        assignments_count = sum(
            x[faculty_idx, block_idx]
            for block in context.blocks
        )
        max_safe_assignments = MAX_BLOCKS * (1.0 - hub_score * 0.1)

        if assignments_count > max_safe_assignments:
            overage = assignments_count - max_safe_assignments
            penalty += overage * hub_score  # Penalize more for critical faculty

    return penalty
```

**Weight**: Variable (tuned based on resilience health score)

---

## Algorithm Deep Dive

### Algorithm 1: Greedy Heuristic Solver

**Purpose**: Fast solutions with human-explainable decisions

**Complexity**: O(n_blocks × log(n_residents)) with priority queue

**Algorithm**:

```
1. Score blocks by difficulty (fewest eligible residents = hardest)
   difficulty[block] = 1 / count_eligible_residents(block)

2. Create priority queue, sort by difficulty (descending)

3. For each block (hardest first):
   a. Get eligible residents (not on blocking absence)
   b. Score candidates:
      - Prefer residents with fewer current assignments (balance workload)
      - Penalize if assignment would cause 80-hour or 1-in-7 violation
      - Bonus if matches resident preference
   c. Select highest-scoring resident
   d. Choose best template (rotation type):
      - Prefer templates resident hasn't done recently
      - Ensure rotation diversity

4. Return assignments with explanations
```

**Advantages**:
- Sub-second execution (<1s for full academic year)
- Transparent reasoning (can explain every decision)
- No external dependencies (pure Python)
- Good solution quality for smaller problems

**Limitations**:
- Not optimal (greedy myopia - local optimization only)
- Can fail on hard constraints (get "stuck")
- No parallel solving
- Suboptimal on complex problems

**When to Use**:
- Demos and explanations
- Quick re-optimization
- Complexity score < 20
- Testing/prototyping

**Code Location**: `backend/app/scheduling/solvers.py::GreedySolver`

### Algorithm 2: CP-SAT Constraint Programming Solver

**Purpose**: Optimal solutions with constraint propagation

**Complexity**: Variable (1-60 seconds for typical problems, exponential worst case)

**Algorithm**:

```
1. Create 3D binary decision variables:
   x[resident_idx, block_idx, template_idx] ∈ {0, 1}
   (1 = resident assigned to block with template, 0 = not assigned)

2. Add base constraint:
   ∀(resident, block): sum(x[r, b, :]) ≤ 1
   (at most one rotation per resident per block)

3. Apply all enabled constraints:
   ├─ Hard: AvailabilityConstraint, 80HourRule, 1In7Rule, SupervisionRatios, ...
   └─ Soft: EquityConstraint, ContinuityConstraint, PreferenceTrail, ...

4. Define objective function (maximize):
   coverage × 1000           (primary: maximize blocks assigned)
   - equity_penalty × 10     (secondary: balance workload)
   - template_balance × 5    (tertiary: rotation diversity)

5. Configure solver:
   - num_workers: 8 (parallel solving)
   - max_time_in_seconds: 60 (or custom timeout)
   - log_search_progress: True
   - use_warmstart: True (from greedy solution)

6. Solve and extract solution:
   - If optimal: return immediately
   - If feasible but time limit: return best found
   - If infeasible: return failure with conflict analysis

7. Post-processing:
   - Assign faculty supervision (if needed)
   - Validate solution against all constraints
   - Calculate quality metrics
```

**Advantages**:
- Optimal or near-optimal solutions
- Powerful constraint propagation (prunes search space)
- Parallel solving on multicore systems
- Good balance of quality and speed
- Can detect infeasibility and report conflicts

**Limitations**:
- Requires OR-Tools package
- Slower on very large problems (> 10k variables)
- Memory-intensive for complex constraint systems
- Learning curve for constraint modeling

**When to Use**:
- Production schedules (reliability + quality)
- Complexity score 20-75
- Quality more important than speed
- Can tolerate 1-60 second solve time

**Code Location**: `backend/app/scheduling/solvers.py::CPSATSolver`

**Tuning Parameters**:

| Parameter | Default | Tuning Strategy |
|-----------|---------|-----------------|
| `num_workers` | 8 | Increase for multicore (up to CPU count) |
| `max_time_in_seconds` | 60 | Reduce to 30s for quicker response, increase to 120s for best quality |
| `log_search_progress` | True | Set to False for production (reduces logging overhead) |
| `use_warmstart` | True | Keep True (dramatically speeds up solving) |
| `symmetry_level` | AUTO | Set to ON for more aggressive pruning |

### Algorithm 3: PuLP Linear Programming Solver

**Purpose**: Speed-optimized solving for large problems

**Complexity**: O(n³) in worst case (simplex method)

**Algorithm**:

```
1. Create 3D binary variables (same as CP-SAT)
2. Add constraints (linearized for LP compatibility)
3. Define objective (linear combination of coverage and penalties)
4. Solve with LP backend:
   - Default: CBC (COIN-OR)
   - Alternatives: GLPK, Gurobi (if available)
5. Extract integer solution (round if needed)
```

**Advantages**:
- Very fast (seconds for large problems)
- Multiple backend options (GLPK, Gurobi, etc.)
- Proven algorithms (simplex method, 70+ years of research)
- Handles large-scale problems well

**Limitations**:
- Linear programming only (some constraints can't be linearized perfectly)
- Requires LP-compatible backends
- Solution quality sometimes lower than CP-SAT
- Integer rounding can violate constraints

**When to Use**:
- Speed critical (need sub-second response)
- Complexity score > 75
- Fine with near-optimal solutions
- Large problems (> 2000 blocks)

**Code Location**: `backend/app/scheduling/solvers.py::PuLPSolver`

### Algorithm 4: Hybrid Solver

**Purpose**: Reliability through intelligent fallback

**Algorithm**:

```
1. Try CP-SAT with 60s timeout
   if success (optimal or feasible):
       return result

2. Fallback to PuLP with 30s timeout
   if success (feasible):
       return result

3. Fallback to Greedy
   (always succeeds, may violate soft constraints)
   return result

4. If all fail:
   return detailed conflict report with:
   - Which constraints conflict
   - Which residents can't be scheduled
   - Suggested relaxations
```

**Advantages**:
- Highest reliability (always produces output)
- Best quality solution found within time budget
- Transparent fallback chain (know which solver was used)
- Production-ready

**Limitations**:
- Slower (tries multiple solvers sequentially)
- More complex error handling

**When to Use**:
- Production schedules (mandatory reliability)
- Users expect results (no timeouts)
- Complex problems with unknown difficulty

**Code Location**: `backend/app/scheduling/solvers.py::HybridSolver`

---

## Solver Patterns & Selection

### Complexity Estimation

**Purpose**: Predict problem difficulty → select solver → adjust timeout

**Algorithm**:

```python
def estimate_complexity(context) -> dict:
    """Estimate problem complexity on scale 0-100"""

    # Factor 1: Problem size
    n_residents = len(context.residents)
    n_blocks = len(context.blocks)
    n_templates = len(context.templates)
    n_variables = n_residents * n_blocks * n_templates
    size_score = min(n_variables / 100000, 1.0) * 20

    # Factor 2: Constraint density
    n_hard_constraints = sum(1 for c in constraint_manager.get_enabled()
                            if isinstance(c, HardConstraint))
    density_score = min(n_hard_constraints / 50, 1.0) * 30

    # Factor 3: Availability (sparsity)
    available_slots = sum(
        1 for r in context.residents
        for b in context.blocks
        if context.availability[r.id][b.id]['available']
    )
    total_slots = n_residents * n_blocks
    sparsity = 1.0 - (available_slots / total_slots)
    sparsity_score = (1.0 - sparsity) * 20  # Dense = easier

    # Factor 4: Soft constraints (optimization goals)
    n_soft_constraints = sum(1 for c in constraint_manager.get_enabled()
                            if isinstance(c, SoftConstraint))
    soft_score = min(n_soft_constraints / 20, 1.0) * 30

    # Combine into complexity score
    complexity = size_score + density_score + soft_score - sparsity_score
    complexity = max(0, min(100, complexity))

    return {
        "score": complexity,
        "variables": n_variables,
        "constraints": n_hard_constraints + n_soft_constraints,
        "sparsity": sparsity,
        "recommended_solver": get_recommended_solver(complexity),
        "estimated_time": estimate_solve_time(complexity)
    }

def get_recommended_solver(complexity):
    """Map complexity to solver recommendation"""
    if complexity < 20:
        return "greedy"
    elif complexity < 50:
        return "pulp"
    elif complexity < 75:
        return "cp_sat"
    else:
        return "hybrid"
```

**Usage Pattern**:

```python
engine = SchedulingEngine(db, start_date, end_date)

# Step 1: Estimate complexity
complexity_report = engine.estimate_complexity()
print(f"Complexity: {complexity_report['score']}/100")
print(f"Recommended: {complexity_report['recommended_solver']}")

# Step 2: Select solver and timeout
if complexity_report['score'] < 50:
    solver = "cp_sat"
    timeout = 30  # Seconds
else:
    solver = "hybrid"
    timeout = 120

# Step 3: Generate with selected solver
result = engine.generate(algorithm=solver, timeout_seconds=timeout)
```

### Warmstart Pattern (Intelligence Reuse)

**Concept**: Use greedy solution as starting point for CP-SAT (dramatically faster)

**Algorithm**:

```python
def generate_with_warmstart(context):
    """Generate schedule with warmstart optimization"""

    # Step 1: Run greedy quickly (gets ~70% quality in <1s)
    greedy_solver = GreedySolver()
    greedy_result = greedy_solver.solve(context)

    # Step 2: Use greedy as warmstart for CP-SAT
    cp_sat_solver = CPSATSolver(warmstart=greedy_result)
    cp_sat_result = cp_sat_solver.solve(context, timeout=30)

    # Step 3: CP-SAT improves on greedy (gets optimal within 30s)
    # Typically: greedy quality 70%, warmstart quality 85%+, optimal quality 95%+

    return cp_sat_result
```

**Performance Impact**:
- Without warmstart: 30-60s solve time
- With warmstart: 5-10s solve time (5-6× faster)
- Often reaches optimal within warmstart-improved solution space

### Fallback Chain Pattern

**Purpose**: Graceful degradation when solvers timeout or fail

```python
def solve_with_fallback(context, timeout=60):
    """Try solvers in order, fallback on failure"""

    start_time = time.time()

    # Try 1: CP-SAT (best quality)
    try:
        result = cp_sat_solve(context, timeout=min(timeout, 60))
        if result.success:
            result.solver_used = "cp_sat"
            return result
    except Exception as e:
        logger.warning(f"CP-SAT failed: {e}")

    # Try 2: PuLP (fast backup)
    remaining_time = timeout - (time.time() - start_time)
    if remaining_time > 5:
        try:
            result = pulp_solve(context, timeout=remaining_time)
            if result.success:
                result.solver_used = "pulp"
                return result
        except Exception as e:
            logger.warning(f"PuLP failed: {e}")

    # Try 3: Greedy (always works)
    try:
        result = greedy_solve(context)
        result.solver_used = "greedy"
        logger.warning("All solvers failed except greedy")
        return result
    except Exception as e:
        # Complete failure - return conflict report
        return generate_conflict_report(context, e)
```

---

## Constraint Implementation Patterns

### Pattern 1: Hard Constraint Implementation

**Template**:

```python
from app.scheduling.constraints.base import HardConstraint, ConstraintType, ConstraintPriority

class MyHardConstraint(HardConstraint):
    """
    Description of what this constraint enforces.

    Medical context: Explain why this matters for residency training.
    """

    def __init__(self):
        super().__init__(
            name="My Hard Constraint",
            constraint_type=ConstraintType.AVAILABILITY,
            priority=ConstraintPriority.CRITICAL
        )

    def add_to_cpsat(self, model, variables, context):
        """
        Add constraint to OR-Tools CP-SAT model.

        Args:
            model: CpModel instance
            variables: dict with 'assignments' key containing decision variables
            context: SchedulingContext with all scheduling data
        """
        x = variables.get("assignments", {})

        # Add constraint equations
        for resident in context.residents:
            r_i = context.resident_idx[resident.id]
            for block in context.blocks:
                b_i = context.block_idx[block.id]

                # Example: Don't assign if unavailable
                if not context.availability[resident.id][block.id]['available']:
                    model.Add(x[(r_i, b_i)] == 0)

    def apply_to_pulp(self, model, variables, context):
        """
        Apply constraint to PuLP model (if needed for LP solving).
        Optional - defaults to validate() only.
        """
        # Most hard constraints only validate, not apply to LP
        pass

    def validate(self, assignments, context) -> list:
        """
        Validate that constraint is satisfied.

        Returns:
            list[ConstraintViolation]: Empty if satisfied, list of violations if not
        """
        violations = []

        for person_id, assignment_list in assignments.items():
            for assignment in assignment_list:
                block_id = assignment.block_id

                # Check constraint
                if not context.availability[person_id][block_id]['available']:
                    violations.append(ConstraintViolation(
                        constraint_name=self.name,
                        constraint_type=self.constraint_type,
                        severity="CRITICAL",
                        message=f"Resident {person_id} assigned during absence on {block_id}",
                        person_id=person_id,
                        block_id=block_id
                    ))

        return violations
```

### Pattern 2: Soft Constraint Implementation

**Template**:

```python
from app.scheduling.constraints.base import SoftConstraint, ConstraintType

class MyEquityConstraint(SoftConstraint):
    """
    Optimize for fair distribution of workload.

    Soft constraints have weights that control how much they're prioritized.
    """

    def __init__(self, weight: float = 10.0):
        super().__init__(
            name="My Equity Constraint",
            constraint_type=ConstraintType.EQUITY,
            priority=ConstraintPriority.MEDIUM,
            weight=weight
        )

    def add_to_cpsat(self, model, variables, context):
        """
        Add soft constraint to CP-SAT model via objective penalty.
        """
        x = variables.get("assignments", {})

        # Calculate workload for each resident
        workload = {}
        for resident in context.residents:
            r_i = context.resident_idx[resident.id]
            workload[r_i] = sum(
                x[(r_i, b_i)] for b_i in range(len(context.blocks))
            )

        # Penalize variance (unfair distribution)
        mean_workload = sum(workload.values()) / len(workload)
        variance = sum(
            (load - mean_workload) ** 2 for load in workload.values()
        )

        # Add to objective as penalty
        model.Maximize(model.objective_score - variance * self.weight)

    def validate(self, assignments, context):
        """
        Soft constraints typically don't have violations.
        Instead, calculate quality metrics.
        """
        # Calculate fairness metrics
        workloads = [len(assignments[r.id]) for r in context.residents]
        mean = sum(workloads) / len(workloads)
        variance = sum((w - mean)**2 for w in workloads) / len(workloads)

        return {
            "mean_workload": mean,
            "variance": variance,
            "fairness_score": 1.0 / (1.0 + variance)  # Higher is fairer
        }
```

### Pattern 3: Constraint with Context-Dependent Logic

**Template** (Real Example: Call Equity):

```python
class SundayCallEquityConstraint(SoftConstraint):
    """
    Balance Sunday call assignments across faculty.

    Sunday call is highly sought-after, so fairness is critical.
    """

    def __init__(self, weight: float = 10.0):
        super().__init__(
            name="Sunday Call Equity",
            constraint_type=ConstraintType.CALL,
            priority=ConstraintPriority.MEDIUM,
            weight=weight
        )

    def add_to_cpsat(self, model, variables, context):
        """Add Sunday call equity to objective"""
        x = variables.get("assignments", {})

        # Get all Sunday blocks
        sunday_blocks = [b for b in context.blocks if b.date.weekday() == 6]  # 6 = Sunday

        # Count Sunday calls per faculty
        sunday_calls_per_faculty = {}
        for faculty in context.faculty:
            f_i = context.faculty_idx[faculty.id]
            sunday_calls = sum(
                x.get((f_i, b_i, "call"), 0)
                for b_i in [context.block_idx[b.id] for b in sunday_blocks]
            )
            sunday_calls_per_faculty[f_i] = sunday_calls

        # Penalize variance in Sunday calls
        if len(sunday_calls_per_faculty) > 0:
            mean_sunday = sum(sunday_calls_per_faculty.values()) / len(sunday_calls_per_faculty)
            variance = sum(
                (calls - mean_sunday) ** 2
                for calls in sunday_calls_per_faculty.values()
            )

            # Penalty in objective
            model.Maximize(model.objective_score - variance * self.weight)
```

---

## Infeasibility Detection & Recovery

### Recognizing Infeasible Problems

**Signs of Infeasibility**:

1. **Solver reports INFEASIBLE**: OR-Tools explicitly detected contradiction
2. **Timeout with no feasible solution**: Solver explored space but found nothing
3. **Partial solution with remaining unassigned blocks**: Some blocks impossible to cover
4. **Manual conflict discovery**: Human reviewer spots impossible requirements

**Root Causes**:

| Cause | Detection | Recovery |
|-------|-----------|----------|
| Too many absences (insufficient coverage) | > 20% blocks can't be covered | Negotiate abbreviated schedule |
| Conflicting constraints | e.g., 80-hour AND minimum call AND max residents | Relax soft constraints or extend timeline |
| Availability matrix too sparse | > 80% slots marked unavailable | Audit absence data, extend date range |
| Unrealistic supervision ratios | Too few faculty for resident cohort | Hire temp faculty or move residents |
| Credential requirements too strict | No one qualified for certain slot types | Extend credentialing deadlines |

### Infeasibility Analysis Workflow

```python
def analyze_infeasibility(context, constraint_manager):
    """
    Systematic infeasibility diagnosis.

    Returns detailed report of conflicts and suggestions.
    """

    # Step 1: Check basic viability
    report = {}

    # Can all residents be scheduled at least once?
    assignable_residents = sum(
        1 for r in context.residents
        if any(context.availability[r.id][b.id]['available']
               for b in context.blocks)
    )
    report['assignable_residents'] = assignable_residents
    report['total_residents'] = len(context.residents)

    if assignable_residents < len(context.residents):
        report['issue'] = 'Residents with zero available blocks'
        report['recommendation'] = 'Extend date range or resolve absences'
        return report

    # Step 2: Run constraint feasibility checks
    for constraint in constraint_manager.get_enabled():
        if isinstance(constraint, HardConstraint):
            feasible = constraint.check_feasibility(context)
            if not feasible:
                report['infeasible_constraints'] = report.get('infeasible_constraints', [])
                report['infeasible_constraints'].append({
                    'name': constraint.name,
                    'reason': constraint.diagnose_infeasibility(context)
                })

    # Step 3: Suggest relaxations
    if 'infeasible_constraints' in report:
        report['suggestions'] = [
            'Relax soft constraints (lower weights)',
            'Extend scheduling date range',
            'Reduce supervisor ratios if possible',
            'Extend 80-hour limit for Block X only',
        ]

    return report
```

### Recovery Strategies

#### Strategy 1: Soft Constraint Relaxation

**When**: Infeasible due to conflicting soft constraints

**Process**:

```python
def relax_soft_constraints(constraint_manager):
    """Relax soft constraints to improve feasibility"""

    # Identify soft constraints currently enabled
    soft_constraints = [c for c in constraint_manager.get_enabled()
                       if isinstance(c, SoftConstraint)]

    # Reduce weights progressively
    relaxations = [
        ("Preferences", 0.5),      # 50% of original weight
        ("Continuity", 0.3),       # 30% of original weight
        ("Coverage", 0.8),         # 80% of original weight
        ("Equity", 0.5),           # 50% of original weight
    ]

    for constraint_name, weight_factor in relaxations:
        for constraint in soft_constraints:
            if constraint.name == constraint_name:
                constraint.weight *= weight_factor
                logger.info(f"Relaxed {constraint_name} weight to {constraint.weight}")

    return constraint_manager
```

**Result**: Trade-off quality for feasibility

#### Strategy 2: Extend Scheduling Window

**When**: Not enough time blocks to meet demand

**Process**:

```python
def extend_scheduling_window(start_date, end_date, extension_days):
    """Extend scheduling window"""
    new_end_date = end_date + timedelta(days=extension_days)
    logger.warning(f"Extending schedule from {end_date} to {new_end_date}")

    # Create new blocks for extended period
    new_blocks = create_blocks(end_date + timedelta(days=1), new_end_date)
    db.session.add_all(new_blocks)
    db.session.commit()

    # Re-run scheduling with extended window
    return SchedulingEngine(db, start_date, new_end_date)
```

**Result**: More blocks = usually feasible

#### Strategy 3: Graduated Constraint Relaxation

**When**: Need precise control over trade-offs

**Process** (Most Sophisticated):

```python
def progressive_relaxation(context, constraint_manager, target_feasibility=True):
    """
    Try progressively more relaxed constraint sets.

    Returns: (feasible_result, relaxations_applied)
    """

    relaxation_levels = [
        # Level 0: Original constraints (most strict)
        {'name': 'Original', 'changes': []},

        # Level 1: Relax soft constraints
        {'name': 'Soft Relaxed', 'changes': [
            {'constraint': 'Equity', 'weight': 0.5},
            {'constraint': 'Continuity', 'weight': 0.0},  # Disable
        ]},

        # Level 2: Relax medium-priority hard constraints
        {'name': 'Medium Hard Relaxed', 'changes': [
            {'constraint': 'OneInSevenRule', 'days_off': 6},  # 1-in-6 instead of 1-in-7
            {'constraint': 'CallSpacing', 'min_spacing': 2},  # 2 days instead of 3
        ]},

        # Level 3: Relax high-priority but sometimes flexible
        {'name': 'High Hard Relaxed', 'changes': [
            {'constraint': 'EightyHourRule', 'hours_allowed': 85},  # 85hr instead of 80hr
        ]},

        # Level 4: Block extensions
        {'name': 'Extended Window', 'changes': [
            {'action': 'extend_window', 'days': 14}
        ]},
    ]

    for level in relaxation_levels:
        logger.info(f"Trying relaxation level: {level['name']}")

        # Apply changes
        for change in level['changes']:
            if 'constraint' in change:
                constraint_manager.adjust(change['constraint'], change)
            elif 'action' in change:
                if change['action'] == 'extend_window':
                    context.end_date += timedelta(days=change['days'])

        # Try solving
        result = solve(context, constraint_manager)
        if result.feasible:
            logger.info(f"SUCCESS with relaxation: {level['name']}")
            return result, level

    # If all relaxations fail, return last attempt with conflict report
    return result, relaxation_levels[-1]
```

---

## Scheduling Philosophy

### Design Principles

#### Principle 1: Constraints First

**Philosophy**: Model all scheduling rules as first-class constraints, not scattered throughout code.

**Why**: Constraints are declarative, composable, testable, and understandable.

**Anti-Pattern**: "Just check this after generation" → hidden in business logic, hard to test

**Best Practice**: "This is a constraint, add it to ConstraintManager" → explicit, testable

#### Principle 2: Transparency & Explainability

**Philosophy**: Users should understand *why* they got this schedule, not just accept it.

**Implementation**:

```python
# For every assignment, provide explanation
class AssignmentExplanation:
    resident: Person
    block: Block
    template: RotationTemplate

    # Why this resident?
    reasons_chosen: list[str]  # "Low current workload", "Preferred rotation", etc.

    # Why this rotation type?
    template_reasons: list[str]  # "Balanced rotation diversity", "Educational requirement", etc.

    # What almost happened?
    alternatives_considered: list[Alternative]  # Who else could have been assigned

    # Confidence score
    confidence: float  # 0.0-1.0 (1.0 = obviously best choice)
```

**Usage**: Greedy solver provides explanations for every assignment

#### Principle 3: Resilience by Design

**Philosophy**: Schedules should be robust to disruptions, not fragile.

**Implementation**:

```python
# Before generation: Check can survive 1 faculty loss
n1_analysis = resilience_service.analyze_n1_contingency()
if not n1_analysis.compliant:
    logger.warning("Schedule not resilient to 1 faculty loss")
    # Either proceed with warning or refuse to commit

# During generation: Apply resilience constraints
constraint_manager.add(HubProtectionConstraint())
constraint_manager.add(UtilizationBufferConstraint(target=0.70))

# After generation: Verify N-1 compliance
post_gen_n1 = resilience_service.analyze_n1_contingency(generated_schedule)
assert post_gen_n1.compliant, "Generated schedule isn't resilient"
```

#### Principle 4: ACGME Compliance Non-Negotiable

**Philosophy**: ACGME violations are regulatory, never acceptable.

**Implementation**:

```python
# Any solver result with ACGME violations is REJECTED
if validation_result.has_acgme_violations:
    logger.error("Schedule has ACGME violations - rejecting")
    return {
        "status": "FAILED",
        "reason": "ACGME compliance violations detected",
        "violations": validation_result.violations
    }

# Never allow partial schedules if compliance uncertain
assert validation_result.valid, "Schedule validation failed"
```

#### Principle 5: Fairness Bias

**Philosophy**: When requirements conflict, favor resident wellbeing and equity.

**Implementation**:

```python
# Soft constraint priorities (in order)
SOFT_CONSTRAINT_WEIGHTS = {
    'coverage': 1000,              # Ensure all blocks covered
    'equity': 50,                  # Fair distribution primary
    'continuity': 20,              # Minimize disruption
    'preferences': 15,             # Honor requests when possible
    'optimization': 5,             # Fine-tuning
}

# Explicit bias in equity calculations
# Prefer solutions that reduce variance (fairness) over maximizing individual preferences
```

#### Principle 6: Audit Trail & Accountability

**Philosophy**: Every decision must be traceable and explainable for compliance review.

**Implementation**:

```python
# Every schedule generation creates audit record
schedule_run = ScheduleRun(
    generation_time=now,
    algorithm_used='cp_sat',
    solver_timeout=60,
    hard_constraints_enabled=[...],
    soft_constraints_enabled=[...],
    resilience_health_pre=0.82,
    resilience_health_post=0.81,
    violations_found=0,
    total_assignments=730,
    status='SUCCESS'
)
db.session.add(schedule_run)

# Every assignment traces back to generation
assignment = Assignment(
    person_id=resident_id,
    block_id=block_id,
    template_id=template_id,
    schedule_run_id=schedule_run.id,  # <- Links to generation context
    created_at=now,
    created_by='SCHEDULER_AGENT'
)
db.session.add(assignment)
```

---

## Advanced Capabilities

### Capability 1: Night Float → Post-Call Audit

**Purpose**: Ensure proper transitions from Night Float to Post-Call shifts.

**Why Important**: Night Float (continuous night coverage) to Post-Call transition is a known ACGME vulnerability.

**Audit Process**:

```python
def audit_nf_pc_transitions(assignments, context) -> NFPCAudit:
    """
    Audit Night Float → Post-Call transitions for ACGME compliance.
    """

    violations = []
    total_transitions = 0

    for resident in context.residents:
        # Find all NF → PC transitions
        assignments = get_assignments_for_resident(resident)
        sorted_assignments = sorted(assignments, key=lambda a: a.block.date)

        for i in range(len(sorted_assignments) - 1):
            current = sorted_assignments[i]
            next_a = sorted_assignments[i + 1]

            if (current.template.name == 'Night Float' and
                next_a.template.name == 'Post-Call'):

                total_transitions += 1

                # Check: Post-Call day must be lighter duty
                # Check: No overnight call within 24 hours after Night Float
                # Check: Adequate rest period

                if not validate_nf_pc_transition(current, next_a):
                    violations.append(NFPCAuditViolation(
                        resident_id=resident.id,
                        nf_block=current.block,
                        pc_block=next_a.block,
                        reason="Post-Call day not adequately lighter than Night Float"
                    ))

    return NFPCAudit(
        compliant=len(violations) == 0,
        total_nf_transitions=total_transitions,
        violations=violations
    )
```

### Capability 2: Resilience Health Integration

**Purpose**: Measure and optimize schedule resilience.

**Metrics Tracked**:

```python
@dataclass
class ResilienceMetrics:
    # Tier 1: Core metrics
    utilization_rate: float              # Target: < 0.80
    hub_centrality_max: float            # Max centrality score (critical faculty)
    n1_compliant: bool                   # Can survive 1 faculty loss?
    n2_compliant: bool                   # Can survive 2 faculty loss?

    # Tier 2: Coverage metrics
    coverage_rate: float                 # % blocks assigned
    critical_service_staffing: dict      # Minimum staffing per service

    # Health status
    status: str                          # GREEN, YELLOW, ORANGE, RED, BLACK
    risk_score: float                    # 0.0-1.0 (1.0 = highest risk)
```

**Health Scoring**:

```python
def calculate_health_score(metrics: ResilienceMetrics) -> float:
    """
    Calculate overall resilience health on 0.0-1.0 scale.

    1.0 = perfectly resilient
    0.5 = acceptable risk
    0.0 = critical risk
    """

    # Component 1: Utilization (should be < 80%)
    if metrics.utilization_rate <= 0.70:
        util_score = 1.0
    elif metrics.utilization_rate <= 0.80:
        util_score = 0.8
    else:
        util_score = 0.5  # Over-utilized, risky

    # Component 2: N-1 compliance (can lose 1 person)
    n1_score = 1.0 if metrics.n1_compliant else 0.5

    # Component 3: Coverage (all blocks assigned)
    coverage_score = metrics.coverage_rate

    # Component 4: Hub concentration (critical faculty over-relied on?)
    if metrics.hub_centrality_max > 0.8:
        hub_score = 0.5
    elif metrics.hub_centrality_max > 0.6:
        hub_score = 0.7
    else:
        hub_score = 1.0

    # Weighted combination
    health = (
        util_score * 0.3 +
        n1_score * 0.3 +
        coverage_score * 0.2 +
        hub_score * 0.2
    )

    return health
```

### Capability 3: Preference Trail (Stigmergy)

**Purpose**: Self-organizing system that learns preferences and applies them to future schedules.

**How It Works**:

```python
def track_preference_trail(resident_id, assignments, context):
    """
    Track which rotations residents prefer based on history.

    Stigmergy: Indirect communication through environment (schedule history).
    """

    pref_trail = context.preference_trails.get(resident_id, {})

    for assignment in assignments:
        template_id = assignment.template.id

        # Increment preference counter for this template
        if template_id not in pref_trail:
            pref_trail[template_id] = {
                'count': 0,
                'satisfaction': 0,  # 1.0 = loved it, -1.0 = hated it
                'last_assigned': None
            }

        pref_trail[template_id]['count'] += 1
        pref_trail[template_id]['last_assigned'] = assignment.created_at

        # Can accumulate satisfaction from post-rotation surveys
        # pref_trail[template_id]['satisfaction'] += survey_score

    return pref_trail

def use_preference_trail(context):
    """
    Use accumulated preferences to guide future scheduling.

    Residents naturally move toward rotations they prefer.
    """

    # Add soft constraint: prefer templates in resident's trail
    for resident in context.residents:
        trail = context.preference_trails.get(resident.id, {})
        preferred_templates = [
            tid for tid, info in trail.items()
            if info['satisfaction'] > 0.5  # Resident liked this rotation
        ]

        # During solving: bonus assignments to preferred templates
        # Weight based on how much they liked it
        for template_id in preferred_templates:
            satisfaction = trail[template_id]['satisfaction']
            bonus = satisfaction * 5  # Soft constraint weight
            add_preference_bonus(resident_id, template_id, bonus)
```

### Capability 4: Complexity-Adaptive Solving

**Purpose**: Automatically adjust solver strategy based on detected complexity.

**Workflow**:

```python
def generate_adaptive(context, target_quality='balanced'):
    """
    Automatically select solver and timeouts based on complexity.

    target_quality: 'fast' (1s), 'balanced' (10s), 'quality' (60s)
    """

    # Step 1: Estimate complexity
    complexity = estimate_complexity(context)
    print(f"Estimated complexity: {complexity['score']}/100")

    # Step 2: Map complexity → solver + timeout
    if complexity['score'] < 20:
        solver = 'greedy'
        timeout = 1
    elif complexity['score'] < 50:
        solver = 'pulp'
        timeout = {'fast': 2, 'balanced': 5, 'quality': 15}[target_quality]
    elif complexity['score'] < 75:
        solver = 'cp_sat'
        timeout = {'fast': 5, 'balanced': 30, 'quality': 60}[target_quality]
    else:
        solver = 'hybrid'
        timeout = {'fast': 10, 'balanced': 120, 'quality': 300}[target_quality]

    # Step 3: Run with selected configuration
    print(f"Using {solver} solver, timeout={timeout}s")
    result = run_solver(context, solver=solver, timeout=timeout)

    # Step 4: Adapt if timeout hit
    if result.hit_timeout and solver != 'greedy':
        print("Timeout hit, falling back to faster solver")
        result = run_solver(context, solver='greedy', timeout=1)

    return result
```

---

## Integration Patterns

### Integration with Resilience Service

```python
def generate_with_resilience(db, start_date, end_date):
    """
    Full integration with resilience framework.
    """

    # Initialize services
    resilience = ResilienceService(db)
    engine = SchedulingEngine(db, start_date, end_date)

    # Pre-check: System healthy enough to generate?
    pre_health = resilience.get_health_score()
    if pre_health < 0.7:
        logger.warning(f"Resilience health low: {pre_health}")
        # Could warn user or require approval

    # Generate with resilience constraints
    engine.constraint_manager.add(HubProtectionConstraint())
    engine.constraint_manager.add(UtilizationBufferConstraint(target=0.70))

    result = engine.generate(algorithm='cp_sat', timeout_seconds=60)

    # Post-check: Did generation maintain/improve resilience?
    post_health = resilience.get_health_score()
    print(f"Resilience: {pre_health} → {post_health}")

    if post_health < pre_health - 0.05:
        logger.warning("Generation degraded resilience")
        # Could trigger mitigations

    return result
```

### Integration with MCP Tools

**Available MCP Tools for SCHEDULER**:

```
validate_schedule(schedule_id)       → ACGME compliance report
get_schedule_health(schedule_id)     → Resilience metrics
execute_swap(swap_id)                → Process swap request
get_coverage_gaps(start, end)        → Identify understaffed blocks
calculate_work_hours(resident_id)    → Detailed hour breakdown
analyze_complexity(schedule_params)  → Estimate solve difficulty
generate_schedule(params)            → Trigger schedule generation
estimate_resilience(schedule)        → Predict resilience post-generation
```

---

## Best Practices & Pitfalls

### Best Practice 1: Always Backup Before Write

```python
# ALWAYS do this first
backup = create_database_backup()
assert backup is not None, "Cannot proceed without backup"

# Then generate
result = engine.generate()

# Only persist if validation passes
if result.validation.valid:
    persist_schedule(result)
else:
    # Rollback to backup if needed
    rollback_to_backup(backup)
```

### Best Practice 2: Validate Early, Fail Fast

```python
# Check feasibility BEFORE running expensive solver
pre_solver_validator = PreSolverValidator()
conflicts = pre_solver_validator.identify_infeasibilities(context)

if conflicts:
    logger.error(f"Infeasible problem detected: {conflicts}")
    return {
        "status": "INFEASIBLE",
        "reason": "Problem has conflicting constraints",
        "details": conflicts
    }

# Only proceed if feasibility looks good
# This prevents wasting solver time on impossible problems
```

### Best Practice 3: Use Warmstart for Speed

```python
# Never start cold when possible

# Option 1: Use greedy output as warmstart
greedy_solution = greedy_solver.solve(context)
cp_sat_result = cp_sat_solver.solve(
    context,
    warmstart=greedy_solution,
    timeout=30
)
# Result: 5-10× faster than no warmstart

# Option 2: Use previous schedule as starting point
prev_schedule = db.query(Assignment).filter(...).all()
result = engine.generate(warmstart=prev_schedule)
```

### Best Practice 4: Monitor Solver Progress

```python
def generate_with_monitoring(context, timeout=60):
    """Monitor solver progress, log every 5%"""

    from app.core.redis import redis_client

    # Set up progress callback
    def progress_callback(progress_dict):
        percent = progress_dict.get('percent', 0)
        if percent % 5 == 0:  # Every 5%
            logger.info(f"Solver progress: {percent}%")

        # Allow kill-switch
        if redis_client.get('solver:abort_signal'):
            logger.warning("Abort signal received, stopping solver")
            return False  # Tells solver to stop

    solver = CPSATSolver(progress_callback=progress_callback)
    result = solver.solve(context, timeout=timeout)

    return result
```

### Best Practice 5: Test Edge Cases

```python
# Test cases that ALWAYS need coverage

def test_acgme_80_hour_boundary():
    """Test 80-hour rule at exact boundary (53 blocks in 28 days)"""
    # Create resident with exactly 53 blocks in window
    # Verify ACGME validator accepts it
    # Verify 54 blocks triggers violation

def test_1_in_7_boundary():
    """Test 1-in-7 at exact boundary (6 consecutive days)"""
    # Create resident with 6 consecutive assigned days
    # Verify ACGME validator accepts it
    # Verify 7 consecutive days triggers violation

def test_nf_pc_transition():
    """Test Night Float to Post-Call transition"""
    # Create proper NF→PC sequence
    # Verify audit passes
    # Test improper transitions (no rest, etc.)

def test_supervision_ratio_exact():
    """Test supervision ratios at exact limits"""
    # Create block with exactly 2 PGY-1s and 1 faculty
    # Verify accepts
    # Test 3 PGY-1s and 1 faculty (violates 1:2 ratio)
```

### Common Pitfall 1: Ignoring Availability Matrix

**Pitfall**: Building schedules without properly loading absence data

**Fix**:

```python
# WRONG: Ignores absences
assignments = solver.solve(context)  # May assign blocked residents

# RIGHT: Build availability matrix first
availability = build_availability_matrix(
    residents=context.residents,
    absences=db.query(Absence).all()
)
context.availability = availability  # Now solver respects absences

assignments = solver.solve(context)  # Safer
```

### Common Pitfall 2: Underestimating Complexity

**Pitfall**: Using fast solver on complex problem

**Fix**:

```python
# WRONG: Assumes complexity < 50
result = run_solver(context, solver='pulp', timeout=5)
# Result: Timeout, partial schedule, complaints

# RIGHT: Estimate first
complexity = estimate_complexity(context)
if complexity > 50:
    solver = 'cp_sat'  # or 'hybrid'
    timeout = 60
else:
    solver = 'pulp'
    timeout = 5

result = run_solver(context, solver=solver, timeout=timeout)
```

### Common Pitfall 3: Forgetting Audit Trail

**Pitfall**: Generating schedule but not recording generation metadata

**Fix**:

```python
# WRONG: No audit record
assignments = engine.generate()
save_assignments(assignments)

# RIGHT: Create schedule run record
run = ScheduleRun(
    algorithm='cp_sat',
    start_date=start_date,
    end_date=end_date,
    solver_timeout=60,
    total_residents=len(residents),
    total_blocks=len(blocks),
    status='IN_PROGRESS'
)
db.session.add(run)
db.session.flush()  # Get run.id

assignments = engine.generate()
for assignment in assignments:
    assignment.schedule_run_id = run.id

save_assignments(assignments)
run.status = 'SUCCESS'
db.session.commit()
```

---

## Operational Playbooks

### Playbook 1: Emergency Coverage Response

**Trigger**: Resident becomes suddenly unavailable (TDY, medical emergency)

**SLA**: Response < 15 minutes to identify gaps, < 60 minutes to find coverage

**Steps**:

```
Phase 1: Immediate Response (< 5 min)
  1. Log absence in Absence table (mark as BLOCKING)
  2. Query assignments for resident in next 7 days
  3. Identify critical shifts (ER, ICU, overnight call)
  4. Alert on-call faculty immediately

Phase 2: Find Coverage (< 60 min)
  1. Build eligibility matrix for replacement:
     - Same PGY level preferred
     - Under 80-hour limit for week
     - Meets credential requirements
     - Available for full shift (not pre-assigned)

  2. Score candidates:
     - Score 1.0: Lowest workload, all qualifications
     - Score 0.5: Higher workload but qualified
     - Score 0.0: Cannot fill (over 80-hour or unqualified)

  3. If 1 candidate (score > 0.5):
     - Auto-swap, skip approval

  Elif 2-3 candidates:
     - Present options to faculty for selection

  Elif 0 candidates:
     - Faculty must cover (overtime/comp time)
     - Escalate for approval

Phase 3: Execute Swap
  1. Begin database transaction
  2. Update Assignment: old_resident_id → new_resident_id
  3. Run ACGME validator on both residents (±14 day window)
  4. Create CallAssignment if overnight call affected
  5. Create swap audit log
  6. Commit transaction
  7. Send notifications to all parties
  8. Set 24-hour rollback window

Phase 4: Long-Term Adjustment
  If absence > 14 days:
    1. Identify all affected blocks for resident
    2. Decide: Individual swaps OR full schedule regeneration?
    3. If regen: notify faculty, run new schedule, distribute to team
    4. Document accommodation in system
```

### Playbook 2: Detecting & Responding to Infeasibility

**Trigger**: Solver hits timeout without feasible solution

**SLA**: Diagnosis within 30 minutes, recommendations within 1 hour

**Steps**:

```
Phase 1: Quick Diagnosis (< 5 min)
  1. Check basic viability:
     - Are there any residents with 0 available blocks? (extend range)
     - Is utilization > 100%? (hire more staff)
     - Are hard constraints contradictory? (check conflict pairs)

  2. Run PreSolverValidator to identify specific conflicts

Phase 2: Root Cause Analysis (< 15 min)
  1. Systematically test each hard constraint:
     - Remove Constraint X, try solving → does it help?
     - If yes, Constraint X is part of conflict

  2. Build conflict matrix:
     - Which constraint pairs conflict?
     - Which constraints are negotiable?

  3. Analyze availability data:
     - Show distribution of absences by resident
     - Identify residents with excessive absences

Phase 3: Recommendations (< 10 min)
  1. Identify achievable relaxations:
     - "Extend date range by 7 days" → adds 14 blocks
     - "Relax 80-hour to 85-hour" → easier to satisfy
     - "Reduce supervision ratio PGY-2 from 1:4 to 1:5" → frees faculty

  2. Estimate impact:
     - "This relaxation enables scheduling of X residents"
     - "This trade-off improves fairness by Y%"

  3. Present to faculty with cost-benefit analysis:
     - Option A: Extend schedule 14 days (full coverage)
     - Option B: Reduce 80-hour limit to 85-hour (temporary relief)
     - Option C: Hire temp faculty (cost: $$$)

Phase 4: Resolution
  1. Get faculty decision on relaxation
  2. Implement chosen relaxation
  3. Re-run solver with new constraints
  4. Validate and distribute new schedule
```

### Playbook 3: Monitoring Schedule Quality Post-Generation

**Purpose**: Ensure generated schedule meets quality standards before distribution

**Process**:

```
Quality Gate 1: ACGME Compliance (MANDATORY)
  ✓ 0 violations of 80-hour rule
  ✓ 0 violations of 1-in-7 rule
  ✓ 0 violations of supervision ratios
  ✓ 100% resident availability respected
  → If any fail: REJECT schedule, restart

Quality Gate 2: Coverage Completeness (MANDATORY)
  ✓ 100% of blocks assigned (no orphans)
  ✓ All critical services staffed (ER, ICU, etc.)
  ✓ All rotation templates represented
  → If < 95%: REJECT, re-optimize

Quality Gate 3: Fairness Metrics
  ✓ Call distribution: median ± 1 call
  ✓ Workload variance: < 5 blocks between highest/lowest
  ✓ Preference satisfaction: > 60% of requests honored
  → If > 2 fails: FLAG for review (don't reject)

Quality Gate 4: Resilience Compliance
  ✓ N-1 contingency viable (can lose 1 faculty)
  ✓ Utilization < 80%
  ✓ Hub protection: no critical faculty over-loaded
  → If any fail: FLAG for review (don't reject)

Quality Gate 5: Human Review Checklist
  Faculty review for:
  ✓ FMIT assignments look reasonable
  ✓ Call patterns make sense
  ✓ No obvious "weird" assignments that stand out
  ✓ Resident feedback incorporated (if available)
  → If concerns: Schedule faculty meeting to adjust

Quality Gate 6: Final Approval
  ✓ Faculty sign-off obtained
  ✓ Audit log created with approval metadata
  ✓ Notifications prepared
  → COMMIT to database
```

---

## Summary & Quick Reference

### The 5 Core Constraint Types

1. **Availability**: Respect absences (hard)
2. **ACGME Rules**: 80-hour, 1-in-7, supervision (hard)
3. **Coverage**: All blocks assigned (soft, high weight)
4. **Equity**: Fair workload distribution (soft, medium weight)
5. **Resilience**: N-1 viability, utilization buffers (soft, variable weight)

### The 4 Solvers

| Solver | Speed | Quality | Use When |
|--------|-------|---------|----------|
| Greedy | <1s | 70% | Need explanation |
| PuLP | 5-30s | 80% | Speed critical |
| CP-SAT | 10-60s | 95% | Quality matters |
| Hybrid | Variable | 95%+ | Production use |

### The 3 Resilience Tiers

| Tier | Concept | Implementation |
|------|---------|-----------------|
| Tier 1 | 80% utilization, N-1 viable | UtilizationBufferConstraint, HubProtectionConstraint |
| Tier 2 | Preference trails, zone isolation | PreferenceTrailConstraint, ZoneBoundaryConstraint |
| Tier 3+ | Cross-disciplinary monitoring | SPC, epidemiology, queuing theory, etc. |

### Pre-Generation Checklist

- [ ] Database backup created
- [ ] Resilience health ≥ 0.7
- [ ] Absence data loaded
- [ ] Constraints registered
- [ ] Complexity estimated
- [ ] Solver selected
- [ ] Timeout configured
- [ ] Pre-solver validation passed
- [ ] Faculty notified

### Post-Generation Checklist

- [ ] 0 ACGME violations
- [ ] 100% coverage
- [ ] N-1 contingency viable
- [ ] Fairness metrics acceptable
- [ ] Audit trail recorded
- [ ] Faculty review completed
- [ ] Notifications sent
- [ ] Rollback backup retained (24 hours)

---

## References & Further Reading

- **Constraint Implementation Guide**: `backend/app/scheduling/constraints/`
- **Solver Documentation**: `backend/app/scheduling/solvers.py`
- **Resilience Framework**: `/docs/architecture/cross-disciplinary-resilience.md`
- **ACGME Compliance**: `backend/app/scheduling/acgme_validator.py`
- **Infeasibility Handling**: `backend/app/scheduling/pre_solver_validator.py`

---

**Last Updated**: 2025-12-30
**Maintained By**: G2_RECON SEARCH_PARTY Operation
**Next Review**: 2026-01-27 (monthly)

