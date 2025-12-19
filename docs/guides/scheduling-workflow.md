# Scheduling Workflow Guide

> **Complete end-to-end workflows for residency scheduling**
> **Last Updated:** 2025-12-19
> **Audience:** Program coordinators, administrators, developers

---

## Table of Contents

1. [Schedule Creation](#1-schedule-creation)
2. [Schedule Generation](#2-schedule-generation)
3. [Validation](#3-validation)
4. [Conflict Resolution](#4-conflict-resolution)
5. [Swap Workflow](#5-swap-workflow)
6. [Emergency Coverage](#6-emergency-coverage)
7. [Common Scenarios](#7-common-scenarios)

---

## 1. Schedule Creation

### Overview

Schedule creation establishes the foundation for the academic year: defining rotation templates, setting constraints, and configuring the scheduling environment.

### 1.1 Setting Academic Year Dates

**Steps:**

1. Navigate to **Settings** → **Academic Year**
2. Define year boundaries:
   - **Start Date**: First day of academic year (typically July 1)
   - **End Date**: Last day of academic year (typically June 30)
3. Configure block structure:
   - **Block Duration**: 28-day rotations (standard for residency programs)
   - **Half-Day Blocks**: AM/PM sessions (6 hours each)
4. Mark special dates:
   - Holidays
   - Conference dates
   - Program closure dates
5. **Save Configuration**

**Data Model:**
- Each day is split into 2 blocks (AM/PM)
- 365 days × 2 = 730 blocks per academic year
- Blocks are numbered sequentially by 28-day periods

---

### 1.2 Defining Rotation Templates

Rotation templates are reusable activity patterns that define the types of work residents perform.

**Common Templates:**

| Template Name | Activity Type | Max Residents | Supervision Required | Leave Eligible |
|---------------|---------------|---------------|----------------------|----------------|
| PGY-1 Clinic | clinic | 4 | Yes (1:2 ratio) | Yes |
| PGY-2 Clinic | clinic | 6 | Yes (1:4 ratio) | Yes |
| FMIT Inpatient | inpatient | 2 | Yes (1:2 ratio) | No |
| Procedures | procedure | 2 | Yes | Yes |
| Conference | conference | All | No | Yes |
| Sports Medicine | clinic | 2 | Yes (specialty) | Yes |

**Template Configuration:**

```
Template: "PGY-1 Clinic"
├── Activity Type: clinic
├── Max Residents: 4 (physical space constraint)
├── Clinic Location: "Main Clinic"
├── Supervision Required: Yes
├── Supervision Ratio: 1:2 (1 faculty per 2 PGY-1 residents)
├── Leave Eligible: Yes (scheduled leave allowed)
└── Requires Specialty: None
```

**Steps to Create Template:**

1. Navigate to **Settings** → **Rotation Templates** → **New Template**
2. Enter template details:
   - **Name**: Descriptive name (e.g., "PGY-1 Clinic")
   - **Activity Type**: clinic, inpatient, procedure, conference
   - **Abbreviation**: Short code for calendar display (e.g., "C", "FMIT")
3. Set constraints:
   - **Max Residents**: Physical capacity limit
   - **Supervision Ratio**: ACGME-compliant ratios
   - **Leave Eligible**: Can residents take scheduled leave on this rotation?
   - **Requires Specialty**: Does this need a specialist faculty member?
4. Configure ACGME settings:
   - **Supervision Required**: Yes/No
   - **Max Supervision Ratio**: 1:2 for PGY-1, 1:4 for PGY-2/3
5. **Save Template**

---

### 1.3 Configuring Constraints

Constraints ensure the schedule meets regulatory, educational, and operational requirements.

**Constraint Categories:**

#### ACGME Compliance Constraints (Hard)

| Constraint | Description | Priority |
|------------|-------------|----------|
| 80-Hour Rule | Max 80 hours/week averaged over 4 weeks | CRITICAL |
| 1-in-7 Rule | One 24-hour period off every 7 days | CRITICAL |
| Supervision Ratios | PGY-1: 1:2, PGY-2/3: 1:4 | CRITICAL |
| Availability | No assignments during blocking absences | CRITICAL |

#### Educational Constraints (Soft)

| Constraint | Description | Weight |
|------------|-------------|--------|
| Rotation Diversity | Ensure variety of experiences | Medium |
| Skill Progression | PGY-1 → PGY-2 → PGY-3 complexity | High |
| Preference Alignment | Match faculty/resident preferences | Low |

#### Operational Constraints (Soft)

| Constraint | Description | Weight |
|------------|-------------|--------|
| Workload Balance | Distribute assignments equitably | High |
| Hub Protection | Avoid over-assigning critical faculty | High |
| N-1 Vulnerability | Ensure schedule survives one faculty loss | Medium |
| Zone Boundaries | Isolate failure zones | Medium |

**Constraint Configuration:**

```
Navigate to: Settings → Constraints

ACGME Constraints (Always Enabled):
  ☑ 80-Hour Rule (CRITICAL)
  ☑ 1-in-7 Rule (CRITICAL)
  ☑ Supervision Ratios (CRITICAL)
  ☑ Availability (CRITICAL)

Resilience Constraints (Optional):
  ☐ Hub Protection (Weight: 0.3)
  ☐ Utilization Buffer (Target: 80%, Weight: 0.2)
  ☐ N-1 Vulnerability (Weight: 0.2)
  ☐ Zone Boundary (Weight: 0.1)

Preference Constraints (Optional):
  ☐ Preference Trail (Weight: 0.1)
  ☐ Workload Balance (Weight: 0.2)
```

---

## 2. Schedule Generation

### Overview

Schedule generation uses constraint-based algorithms to create compliant, optimized schedules automatically.

### 2.1 Generation Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                    Schedule Generation Flow                  │
└─────────────────────────────────────────────────────────────┘

    START
      │
      ▼
┌──────────────────────┐
│ Configure Generation │
│ - Date Range         │
│ - PGY Levels         │
│ - Algorithm          │
│ - Constraints        │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Pre-Generation Check │
│ - Validate templates │
│ - Check residents    │
│ - Resilience health  │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Create Blocks        │
│ (365 days × 2)       │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Load Absences        │
│ Build Availability   │
│ Matrix               │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Run Solver Algorithm │
│ - Greedy             │
│ - CP-SAT             │
│ - PuLP               │
│ - Hybrid             │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Assign Faculty       │
│ Supervision          │
│ (Post-processing)    │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Validate ACGME       │
│ Compliance           │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Post-Generation      │
│ Resilience Check     │
└──────────┬───────────┘
           │
           ▼
     ┌────┴────┐
     │ Success?│
     └────┬────┘
          │
    ┌─────┴─────┐
    │           │
   YES          NO
    │           │
    ▼           ▼
 ┌─────┐   ┌─────────┐
 │Commit│   │Rollback │
 │Save │   │Try Again│
 └─────┘   └─────────┘
```

---

### 2.2 Algorithm Selection

**Available Algorithms:**

#### Greedy (Fast, Good Quality)

```
Speed:      ████████░░ 8/10
Quality:    ██████░░░░ 6/10
Optimality: ████░░░░░░ 4/10

Best For:
  - Initial drafts
  - Quick iterations
  - Small schedules (<50 residents)
  - Testing configurations

Runtime: 5-30 seconds
```

**How it Works:**
1. Sort blocks by difficulty (hardest first)
2. For each block, assign least-loaded resident who satisfies constraints
3. Greedy choice: optimize locally, not globally

**Pros:**
- Very fast
- Always produces a feasible solution (if one exists)
- Good for rapid prototyping

**Cons:**
- Not optimal
- May miss better solutions
- Can create uneven workload distribution

---

#### CP-SAT (Slow, Optimal Quality)

```
Speed:      ███░░░░░░░ 3/10
Quality:    ██████████ 10/10
Optimality: ██████████ 10/10

Best For:
  - Final production schedules
  - Complex constraint scenarios
  - Proving feasibility/infeasibility
  - Critical schedules requiring optimization

Runtime: 2-10 minutes (with timeout)
```

**How it Works:**
1. Model scheduling as constraint satisfaction problem (CSP)
2. Use Google OR-Tools CP-SAT solver
3. Find provably optimal solution or prove none exists

**Pros:**
- Guarantees optimal solution (if found)
- Handles complex constraints elegantly
- Proven to satisfy all hard constraints

**Cons:**
- Slow for large problems
- May timeout without solution
- Requires more computational resources

---

#### PuLP (Medium Speed, Good Quality)

```
Speed:      ██████░░░░ 6/10
Quality:    ████████░░ 8/10
Optimality: ████████░░ 8/10

Best For:
  - Large-scale schedules (>100 residents)
  - Linear optimization objectives
  - Continuous variables (workload balancing)

Runtime: 30 seconds - 3 minutes
```

**How it Works:**
1. Model as linear programming (LP) problem
2. Use PuLP solver with CBC backend
3. Optimize linear objective function

**Pros:**
- Scales better than CP-SAT for large problems
- Good at workload balancing
- Efficient for continuous optimization

**Cons:**
- Some constraint types harder to express
- May need integer relaxation
- Not as flexible as CP-SAT for logic constraints

---

#### Hybrid (Best of Both Worlds)

```
Speed:      █████░░░░░ 5/10
Quality:    █████████░ 9/10
Optimality: █████████░ 9/10

Best For:
  - Production schedules
  - Balanced performance
  - Default recommended choice

Runtime: 1-5 minutes
```

**How it Works:**
1. Phase 1: Use Greedy for quick initial solution
2. Phase 2: Use CP-SAT to optimize hard constraints
3. Phase 3: Use PuLP for workload balancing
4. Return best solution found

**Pros:**
- Best balance of speed and quality
- Leverages strengths of each algorithm
- Fallback to Greedy if advanced solvers fail

**Cons:**
- More complex implementation
- Slightly longer runtime than Greedy

---

### 2.3 Step-by-Step Generation

**Navigate to:** Schedule → Generate

**Step 1: Configure Parameters**

```
┌──────────────────────────────────────────┐
│     Schedule Generation Configuration    │
├──────────────────────────────────────────┤
│                                          │
│ Date Range:                              │
│   Start: [2025-07-01] 📅                │
│   End:   [2026-06-30] 📅                │
│                                          │
│ Resident Filter:                         │
│   ☑ PGY-1                                │
│   ☑ PGY-2                                │
│   ☑ PGY-3                                │
│   ☐ All Levels                           │
│                                          │
│ Algorithm:                               │
│   ○ Greedy (Fast)                        │
│   ○ CP-SAT (Optimal)                     │
│   ○ PuLP (Balanced)                      │
│   ● Hybrid (Recommended)                 │
│                                          │
│ Advanced Options:                        │
│   Timeout: [300] seconds                 │
│   ☑ Check Resilience                     │
│   ☑ Enable Hub Protection                │
│   ☐ Prefer Greedy Fallback               │
│                                          │
│         [Cancel]  [Generate Schedule]    │
└──────────────────────────────────────────┘
```

**Step 2: Monitor Progress**

```
Generating Schedule...

[████████████████████░░░░░░░░] 60%

Phase: Assigning Faculty Supervision
Blocks Created: 730
Residents Processed: 24
Assignments Created: 1,842
Current Validation: Checking ACGME compliance...

Estimated Time Remaining: 45 seconds
```

**Step 3: Review Results**

```
┌──────────────────────────────────────────┐
│       Schedule Generation Complete       │
├──────────────────────────────────────────┤
│                                          │
│ Status: ✓ Success                        │
│                                          │
│ Summary:                                 │
│   Total Blocks: 730                      │
│   Assignments Created: 2,156             │
│   Coverage Rate: 98.5%                   │
│   Runtime: 2m 34s                        │
│                                          │
│ ACGME Compliance:                        │
│   80-Hour Rule: ✓ Pass                   │
│   1-in-7 Rule: ✓ Pass                    │
│   Supervision: ✓ Pass                    │
│   Total Violations: 0                    │
│                                          │
│ Resilience Metrics:                      │
│   Utilization: 78.3% (Target: 80%)       │
│   N-1 Compliant: ✓ Yes                   │
│   N-2 Compliant: ✓ Yes                   │
│   Phase Transition Risk: Low             │
│                                          │
│    [View Schedule]  [Review Details]     │
└──────────────────────────────────────────┘
```

---

### 2.4 Understanding the Availability Matrix

The availability matrix is a critical pre-processing step that enables fast constraint evaluation.

**Structure:**

```python
availability_matrix = {
    person_id (UUID): {
        block_id (UUID): {
            'available': bool,          # Can assign?
            'replacement': str,         # Absence reason (if any)
            'partial_absence': bool     # Non-blocking absence?
        }
    }
}
```

**Absence Classification:**

```
┌──────────────────────────────────────────────┐
│          Absence Decision Tree               │
└──────────────────────────────────────────────┘

                    Absence
                       │
           ┌───────────┴───────────┐
           │                       │
    Blocking Type?           Non-Blocking Type?
           │                       │
    ┌──────┴──────┐         ┌─────┴─────┐
    │             │         │           │
 Deployment     TDY     Vacation    Conference
 Medical Leave          Appointment
    │             │         │           │
    ▼             ▼         ▼           ▼
available=FALSE       available=TRUE
replacement="TDY"     partial_absence=TRUE
                      replacement="Vacation"

BLOCKING: Person CANNOT work
  - Deployment orders
  - TDY (temporary duty)
  - Extended medical leave
  - Family emergency

NON-BLOCKING: Person CAN work partial day
  - Scheduled vacation
  - Conference attendance
  - Medical appointment
  - Education hours
```

**Example:**

```
Resident: Dr. Smith
Block: 2025-07-15 AM

Scenario 1: Military Deployment
  availability_matrix[smith_id][block_id] = {
      'available': False,
      'replacement': 'Military Deployment',
      'partial_absence': False
  }
  → CANNOT assign Dr. Smith to this block

Scenario 2: Conference Attendance
  availability_matrix[smith_id][block_id] = {
      'available': True,
      'replacement': 'Annual Conference',
      'partial_absence': True
  }
  → CAN assign Dr. Smith (partial day work possible)
  → Calendar shows "Conference" but assignment allowed
```

---

## 3. Validation

### Overview

Validation ensures schedules meet ACGME compliance requirements, supervision standards, and coverage needs.

### 3.1 ACGME Compliance Checks

#### 80-Hour Rule Validation

**Rule:** Maximum 80 hours per week, averaged over rolling 4-week periods

**Calculation:**
```
Hours per block = 6 hours (half-day)
Max blocks per 4-week window = (80 hours/week × 4 weeks) / 6 hours/block = 53 blocks

For each resident:
  For each 28-day window:
    Total hours = Count(blocks) × 6
    Average weekly = Total hours / 4

    If Average weekly > 80:
      → VIOLATION
```

**Validation Flowchart:**

```
For Each Resident:
    │
    ▼
  Get all assignments
    │
    ▼
  Group by date
    │
    ▼
  For each 28-day window:
    │
    ├─→ Count blocks in window
    │
    ├─→ Calculate total hours (blocks × 6)
    │
    ├─→ Calculate average weekly (hours / 4)
    │
    ├─→ Is average > 80?
    │     │
    │     ├─→ YES: Record violation
    │     │
    │     └─→ NO: Continue
    │
    ▼
  Report violations
```

**Example Violation:**

```
VIOLATION: 80-Hour Rule
Person: Dr. Jane Doe (PGY-2)
Window: 2025-07-01 to 2025-07-28
Total Hours: 336 hours
Average Weekly: 84 hours/week
Limit: 80 hours/week
Severity: CRITICAL

Action Required:
  - Reduce assignments in this window by 2 blocks
  - Redistribute to other residents
  - Re-run validation
```

---

#### 1-in-7 Rule Validation

**Rule:** At least one 24-hour period off every 7 days (simplified: max 6 consecutive work days)

**Validation Logic:**

```
For Each Resident:
    │
    ▼
  Get unique dates with assignments
    │
    ▼
  Sort dates chronologically
    │
    ▼
  Initialize:
    consecutive = 1
    max_consecutive = 1
    │
    ▼
  For i = 1 to N-1:
    │
    ├─→ If date[i] - date[i-1] == 1 day:
    │     │
    │     ├─→ consecutive++
    │     └─→ max_consecutive = max(max_consecutive, consecutive)
    │
    └─→ Else:
          consecutive = 1
    │
    ▼
  If max_consecutive > 6:
    │
    └─→ VIOLATION
```

**Example:**

```
Resident Work Days:
  Mon Tue Wed Thu Fri Sat Sun [Mon] Tue Wed Thu
   ✓   ✓   ✓   ✓   ✓   ✓   ✓   OFF  ✓   ✓   ✓

Consecutive count: 7 days
Max allowed: 6 days
→ VIOLATION

Required Action:
  - Remove assignment on either Saturday or Sunday
  - Ensure at least one full day off per week
```

---

#### Supervision Ratio Validation

**Rules:**
- **PGY-1**: 1 faculty : 2 residents (1:2 ratio)
- **PGY-2/3**: 1 faculty : 4 residents (1:4 ratio)

**Calculation:**

```python
required_faculty = ceil(pgy1_count / 2) + ceil(other_count / 4)

# Example 1:
# 2 PGY-1, 4 PGY-2
required = ceil(2/2) + ceil(4/4) = 1 + 1 = 2 faculty needed

# Example 2:
# 3 PGY-1, 5 PGY-2
required = ceil(3/2) + ceil(5/4) = 2 + 2 = 4 faculty needed
```

**Validation Flowchart:**

```
For Each Block:
    │
    ▼
  Count residents by PGY level
    │
    ├─→ PGY-1 count: X
    └─→ Other count: Y
    │
    ▼
  Calculate required faculty:
    Required = ⌈X/2⌉ + ⌈Y/4⌉
    │
    ▼
  Count actual faculty assigned
    │
    ▼
  Actual < Required?
    │
    ├─→ YES: VIOLATION
    │
    └─→ NO: Pass
```

**Example Violation:**

```
VIOLATION: Supervision Ratio
Block: 2025-07-15 AM - PGY-1 Clinic
Residents: 4 PGY-1
Faculty Assigned: 1
Faculty Required: 2 (⌈4/2⌉ = 2)
Severity: CRITICAL

Action Required:
  - Assign 1 additional faculty to this block
  - OR reduce resident count to 2
```

---

### 3.2 Coverage Validation

**Coverage Rate Calculation:**

```
Coverage Rate = (Assigned Blocks / Total Available Blocks) × 100%

Total Available Blocks = Weekday blocks (excluding holidays)
Assigned Blocks = Blocks with at least one assignment

Target: ≥ 95% coverage
```

**Coverage Gap Detection:**

```
For Each Block:
    │
    ▼
  Is block a weekday?
    │
    ├─→ NO: Skip (weekend)
    │
    └─→ YES: Check assignments
        │
        ▼
      Count residents assigned
        │
        ├─→ Count = 0: Coverage Gap
        │
        ├─→ Count < Expected: Understaffed
        │
        └─→ Count ≥ Expected: OK
```

**Gap Report Example:**

```
Coverage Gap Report
Date Range: 2025-07-01 to 2025-07-31

Total Blocks: 62 (31 weekdays × 2 sessions)
Assigned: 58
Gaps: 4 (6.5% gap rate)

Gap Details:
  1. 2025-07-04 AM - Holiday (Independence Day)
  2. 2025-07-15 PM - No residents available
  3. 2025-07-22 AM - Understaffed (1/4 residents)
  4. 2025-07-29 PM - No faculty supervision
```

---

## 4. Conflict Resolution

### Overview

Conflicts arise when schedule changes, absences, or swaps create ACGME violations or coverage gaps. The system provides tools to identify and resolve these issues.

### 4.1 Conflict Types

```
┌──────────────────────────────────────────┐
│          Conflict Classification          │
└──────────────────────────────────────────┘

CRITICAL (Must Fix Immediately):
  ├─→ ACGME 80-hour violation
  ├─→ Missing supervision
  ├─→ Assignment during blocking absence
  └─→ Critical service uncovered

HIGH (Fix Soon):
  ├─→ 1-in-7 violation
  ├─→ Understaffed block
  └─→ Back-to-back FMIT weeks

MEDIUM (Address When Possible):
  ├─→ Workload imbalance
  ├─→ Preference conflicts
  └─→ Suboptimal rotation sequence

LOW (Informational):
  ├─→ Minor coverage gaps
  └─→ Non-critical service conflicts
```

---

### 4.2 Conflict Detection Workflow

```
┌─────────────────────────────────────────────────────────┐
│              Conflict Detection Flow                    │
└─────────────────────────────────────────────────────────┘

    Trigger Event:
      │
      ├─→ Schedule Generated
      ├─→ Assignment Modified
      ├─→ Absence Added
      ├─→ Swap Executed
      └─→ Manual Change
      │
      ▼
┌──────────────────────┐
│ Run Validation       │
│ - 80-hour check      │
│ - 1-in-7 check       │
│ - Supervision check  │
│ - Availability check │
└──────────┬───────────┘
           │
           ▼
     ┌────┴────┐
     │Conflicts?│
     └────┬────┘
          │
    ┌─────┴─────┐
    │           │
   YES          NO
    │           │
    ▼           ▼
┌─────────┐  ┌──────┐
│Classify │  │ Done │
│Severity │  └──────┘
└────┬────┘
     │
     ▼
┌─────────────┐
│Generate     │
│Notifications│
└─────┬───────┘
      │
      ▼
┌─────────────┐
│Present      │
│Resolution   │
│Options      │
└─────────────┘
```

---

### 4.3 Auto-Resolution Options

The system can automatically resolve certain conflict types.

#### Option 1: Redistribute Assignments

**Use Case:** Resident exceeds 80-hour limit in a window

**Algorithm:**
```
1. Identify violating resident (R) and window (W)
2. Find assignments in W that can be moved
3. For each movable assignment:
   a. Find alternative residents with capacity
   b. Check if reassignment maintains compliance
   c. If valid, reassign
4. Re-validate
5. If still violated, escalate to manual resolution
```

**Example:**

```
Before Auto-Resolution:
  Dr. Smith: 84 hours/week (VIOLATION)
  Dr. Jones: 72 hours/week (OK)

System Action:
  1. Find Dr. Smith's lowest-priority assignments
  2. Check Dr. Jones can take on 2 more blocks
  3. Reassign 2 blocks from Smith → Jones
  4. Re-validate

After Auto-Resolution:
  Dr. Smith: 78 hours/week (OK)
  Dr. Jones: 78 hours/week (OK)
```

---

#### Option 2: Add Faculty Supervision

**Use Case:** Block lacks sufficient faculty

**Algorithm:**
```
1. Calculate faculty deficit
2. Query available faculty for this block
3. Sort by:
   a. Current workload (ascending)
   b. Specialty match
   c. Hub score (prefer non-hub faculty)
4. Assign least-loaded available faculty
5. Update supervision assignments
```

---

#### Option 3: Remove Non-Critical Assignments

**Use Case:** Coverage conflict during emergency absence

**Priority:**
```
1. Preserve critical services (inpatient, call)
2. Preserve clinic sessions (can be rescheduled)
3. Cancel educational activities (lowest priority)
```

**Algorithm:**
```
1. Classify each assignment by criticality
2. For non-critical conflicts:
   a. Remove assignment
   b. Mark for rescheduling
   c. Notify affected parties
3. For critical conflicts:
   a. Find emergency replacement
   b. Escalate if no replacement available
```

---

### 4.4 Manual Resolution

When auto-resolution fails or manual intervention is preferred:

**Resolution Interface:**

```
┌──────────────────────────────────────────┐
│        Conflict Resolution Tool          │
├──────────────────────────────────────────┤
│                                          │
│ Conflict: 80-Hour Violation              │
│ Resident: Dr. Jane Doe (PGY-2)           │
│ Window: 2025-07-01 to 2025-07-28        │
│ Current Hours: 84 hours/week             │
│ Required Reduction: 2 blocks             │
│                                          │
│ Suggested Actions:                       │
│                                          │
│ 1. ○ Redistribute to Dr. Smith           │
│       (Current: 72 hrs → After: 78 hrs)  │
│                                          │
│ 2. ○ Redistribute to Dr. Jones           │
│       (Current: 70 hrs → After: 76 hrs)  │
│                                          │
│ 3. ○ Manual reassignment                 │
│                                          │
│ Affected Assignments (select 2):         │
│   ☐ 2025-07-10 AM - Clinic               │
│   ☐ 2025-07-10 PM - Clinic               │
│   ☐ 2025-07-17 AM - Procedures           │
│   ☐ 2025-07-24 PM - Conference           │
│                                          │
│    [Cancel]  [Apply Resolution]          │
└──────────────────────────────────────────┘
```

---

## 5. Swap Workflow

### Overview

The swap system allows faculty to trade scheduled weeks while maintaining ACGME compliance and coverage requirements.

### 5.1 Swap Types

```
┌─────────────────────────────────────────┐
│           Swap Types                     │
└─────────────────────────────────────────┘

1. ONE-TO-ONE SWAP
   Faculty A: Week X → Faculty B
   Faculty B: Week Y → Faculty A

   [Week X]  →  [Week Y]
       ↓            ↓
   Faculty B    Faculty A

2. ABSORB (Give Away)
   Faculty A: Week X → Faculty B
   (No reciprocal week)

   [Week X]  →  [Absorb]
       ↓
   Faculty B
```

---

### 5.2 Complete Swap Workflow

```
┌─────────────────────────────────────────────────────────┐
│                 Swap Request Lifecycle                   │
└─────────────────────────────────────────────────────────┘

START: Faculty wants to swap
    │
    ▼
┌──────────────────────┐
│ 1. Submit Request    │
│ - Source week        │
│ - Target faculty     │
│ - Swap type          │
│ - Reason (optional)  │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ 2. Validation        │
│ - Check conflicts    │
│ - ACGME compliance   │
│ - Back-to-back check │
│ - Availability check │
└──────────┬───────────┘
           │
           ▼
     ┌────┴────┐
     │ Valid?  │
     └────┬────┘
          │
    ┌─────┴─────┐
    │           │
   NO          YES
    │           │
    ▼           ▼
┌───────┐  ┌───────────────┐
│Reject │  │ 3. Auto-Match │
│Request│  │ Find Compatible│
└───────┘  │ Partners       │
           └───────┬────────┘
                   │
                   ▼
           ┌──────────────┐
           │ 4. Notify    │
           │ Both Parties │
           └──────┬───────┘
                  │
                  ▼
         ┌────────────────┐
         │ 5. Approval    │
         │ Process        │
         │ - Source: Wait │
         │ - Target: Wait │
         └────────┬───────┘
                  │
                  ▼
            ┌─────┴──────┐
            │Both Approve?│
            └─────┬──────┘
                  │
          ┌───────┴───────┐
          │               │
         NO              YES
          │               │
          ▼               ▼
    ┌─────────┐   ┌──────────────┐
    │ Cancel  │   │ 6. Execute   │
    │ Request │   │ - Update DB  │
    └─────────┘   │ - Swap weeks │
                  │ - Call cascade│
                  └──────┬───────┘
                         │
                         ▼
                  ┌──────────────┐
                  │ 7. Rollback  │
                  │ Window (24hr)│
                  └──────┬───────┘
                         │
                         ▼
                       COMPLETE
```

---

### 5.3 Request Submission

**Navigate to:** Schedule → Request Swap

**Submission Form:**

```
┌──────────────────────────────────────────┐
│         Submit Swap Request              │
├──────────────────────────────────────────┤
│                                          │
│ My Week (Source):                        │
│   Date: [2025-08-11] 📅 (Week of Aug 11)│
│   Current: FMIT Inpatient                │
│                                          │
│ Swap Type:                               │
│   ● One-to-One Swap                      │
│   ○ Absorb (Give Away)                   │
│                                          │
│ Swap With:                               │
│   Faculty: [Dr. Johnson ▼]               │
│                                          │
│ Their Week (if one-to-one):              │
│   Date: [2025-09-15] 📅                 │
│   Their Assignment: Clinic               │
│                                          │
│ Reason (optional):                       │
│   [Family commitment that week]          │
│                                          │
│ ☑ I have checked for conflicts           │
│ ☑ I will notify my residents             │
│                                          │
│         [Cancel]  [Submit Request]       │
└──────────────────────────────────────────┘
```

---

### 5.4 Auto-Matching Process

If no specific target faculty is selected, the system auto-matches compatible partners.

**Matching Algorithm:**

```python
For each pending request R:
    candidates = find_compatible_requests(R)

    for each candidate C:
        score = calculate_compatibility(R, C)

        score components:
          - Date proximity: 0.0-1.0
          - Preference alignment: 0.0-1.0
          - Workload balance: 0.0-1.0
          - Swap history: 0.0-1.0
          - Availability: 0.0-1.0

        total_score = weighted_sum(components)

    return top_k_matches
```

**Scoring Factors:**

| Factor | Weight | Description |
|--------|--------|-------------|
| Date Proximity | 0.30 | Closer dates preferred |
| Preference Alignment | 0.25 | Both get preferred dates |
| Workload Balance | 0.20 | Maintains fairness |
| Swap History | 0.15 | Successful past swaps |
| Availability | 0.10 | No blocked weeks |

**Auto-Match Results:**

```
┌──────────────────────────────────────────┐
│      Auto-Match Results for Request      │
├──────────────────────────────────────────┤
│ Your Request: Week of Aug 11             │
│                                          │
│ Top Matches:                             │
│                                          │
│ 1. ⭐⭐⭐⭐⭐ Dr. Johnson (Score: 0.92)    │
│    Their Week: Sep 15                    │
│    Reason: Perfect preference alignment  │
│    Action: [Request Swap]                │
│                                          │
│ 2. ⭐⭐⭐⭐ Dr. Williams (Score: 0.85)     │
│    Their Week: Aug 25                    │
│    Reason: Good date proximity           │
│    Action: [Request Swap]                │
│                                          │
│ 3. ⭐⭐⭐ Dr. Davis (Score: 0.71)         │
│    Their Week: Oct 6                     │
│    Reason: Compatible availability       │
│    Warning: Dates far apart (56 days)    │
│    Action: [Request Swap]                │
│                                          │
│         [View All Matches]               │
└──────────────────────────────────────────┘
```

---

### 5.5 Validation Checks

Before a swap is approved, the system validates:

```
┌──────────────────────────────────────────┐
│        Swap Validation Checks            │
└──────────────────────────────────────────┘

1. Back-to-Back Check:
   ┌────────────────────┐
   │ Week  │ Faculty    │
   ├────────────────────┤
   │ Aug 4 │ Dr. Smith  │  ← Existing
   │ Aug 11│ Dr. Smith  │  ← Proposed swap
   └────────────────────┘
   → VIOLATION: Back-to-back FMIT weeks

2. External Conflict Check:
   Check if faculty has blocking absence:
   - Deployment
   - TDY
   - Medical leave
   - Pre-blocked vacation

3. ACGME Compliance:
   - Would swap cause 80-hour violation?
   - Would swap create 1-in-7 violation?

4. Coverage Requirements:
   - Is substitute faculty qualified?
   - Does it maintain supervision ratios?

5. Past Date Check:
   - Can't swap weeks in the past
   - Warning if week is < 2 weeks away
```

**Validation Result:**

```
┌──────────────────────────────────────────┐
│       Swap Validation Result             │
├──────────────────────────────────────────┤
│                                          │
│ Status: ⚠ Valid with Warnings            │
│                                          │
│ ✓ No back-to-back conflicts              │
│ ✓ No external conflicts                  │
│ ✓ ACGME compliant                        │
│ ✓ Coverage maintained                    │
│ ✓ Date is valid                          │
│                                          │
│ Warnings:                                │
│ ⚠ Week is only 10 days away - act fast  │
│ ⚠ Call cascade will be affected         │
│                                          │
│ Impact:                                  │
│ - Friday call: Dr. Smith → Dr. Johnson   │
│ - Saturday call: Dr. Smith → Dr. Johnson │
│                                          │
│      [Cancel]  [Proceed Anyway]          │
└──────────────────────────────────────────┘
```

---

### 5.6 Approval Process

**Two-Party Approval Required:**

```
Swap Request #1234
Source: Dr. Smith (Week of Aug 11)
Target: Dr. Johnson (Week of Sep 15)

Approval Status:
┌─────────────────────────────────┐
│ Dr. Smith (Requester)           │
│ Status: ✓ Approved              │
│ Date: 2025-07-01 10:30 AM       │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│ Dr. Johnson (Target)            │
│ Status: ⏳ Pending Response     │
│ Notified: 2025-07-01 10:31 AM   │
│ Reminder Sent: 2025-07-03       │
└─────────────────────────────────┘

Actions for Dr. Johnson:
  [✓ Approve]  [✗ Reject]  [? Need Info]
```

**Approval Notification:**

```
┌──────────────────────────────────────────┐
│           Email Notification             │
├──────────────────────────────────────────┤
│ To: Dr. Johnson                          │
│ Subject: Swap Request from Dr. Smith     │
│                                          │
│ Dr. Smith has requested to swap:         │
│                                          │
│ Give You:  Week of Aug 11 (FMIT)        │
│ Take From: Week of Sep 15 (Clinic)      │
│                                          │
│ Reason: "Family commitment that week"    │
│                                          │
│ This swap is mutually beneficial:        │
│ - You prefer Aug 11 (marked preferred)   │
│ - Dr. Smith prefers Sep 15               │
│ - Compatibility Score: 92%               │
│                                          │
│ Please review and respond within 48hrs:  │
│ [Approve Swap] [Reject] [View Details]   │
└──────────────────────────────────────────┘
```

---

### 5.7 Execution

Once both parties approve, the swap is executed:

```
Execution Steps:

1. Update Schedule Assignments:
   ┌─────────────────────────────────┐
   │ Week of Aug 11                  │
   ├─────────────────────────────────┤
   │ Before: Dr. Smith (FMIT)        │
   │ After:  Dr. Johnson (FMIT)      │
   └─────────────────────────────────┘

   ┌─────────────────────────────────┐
   │ Week of Sep 15                  │
   ├─────────────────────────────────┤
   │ Before: Dr. Johnson (Clinic)    │
   │ After:  Dr. Smith (Clinic)      │
   └─────────────────────────────────┘

2. Update Call Cascade:
   Fri/Sat call assignments automatically
   transfer to the new faculty

3. Record Swap History:
   - Swap ID
   - Executed timestamp
   - Executed by
   - Status: EXECUTED

4. Notify Affected Parties:
   - Both faculty
   - Program coordinator
   - Residents on those services
   - Nursing staff

5. Enable 24-Hour Rollback Window
```

---

### 5.8 Rollback Process

Swaps can be reversed within 24 hours of execution.

**Rollback Workflow:**

```
┌──────────────────────────────────────────┐
│          Rollback Swap Request           │
├──────────────────────────────────────────┤
│                                          │
│ Swap ID: #1234                           │
│ Executed: 2025-07-01 2:30 PM             │
│ Time Remaining: 18 hours 15 minutes      │
│                                          │
│ Original Swap:                           │
│ Dr. Smith: Aug 11 → Dr. Johnson          │
│ Dr. Johnson: Sep 15 → Dr. Smith          │
│                                          │
│ Reason for Rollback:                     │
│ ○ Made in error                          │
│ ○ Circumstances changed                  │
│ ● Conflict discovered                    │
│ ○ Other: [________________]             │
│                                          │
│ Notes:                                   │
│ [Patient load too high that week]        │
│                                          │
│ ⚠ WARNING: This will reverse all changes│
│   and notify all affected parties.       │
│                                          │
│       [Cancel]  [Confirm Rollback]       │
└──────────────────────────────────────────┘
```

**Rollback Execution:**

```
1. Verify rollback eligibility:
   - Within 24-hour window? ✓
   - Status = EXECUTED? ✓
   - Not already rolled back? ✓

2. Reverse assignments:
   Week Aug 11: Dr. Johnson → Dr. Smith
   Week Sep 15: Dr. Smith → Dr. Johnson

3. Reverse call cascade:
   Restore original call assignments

4. Update swap record:
   Status: ROLLED_BACK
   Rollback reason: "Conflict discovered"
   Rolled back at: 2025-07-02 8:45 AM

5. Notify parties:
   ✉ Dr. Smith
   ✉ Dr. Johnson
   ✉ Program Coordinator
```

---

## 6. Emergency Coverage

### Overview

Emergency coverage handles unexpected absences requiring immediate schedule changes: military deployments, medical emergencies, family emergencies, and TDY assignments.

### 6.1 Emergency Types

```
┌──────────────────────────────────────────┐
│        Emergency Coverage Types          │
└──────────────────────────────────────────┘

CRITICAL (Immediate Action):
  ├─→ Military Deployment
  │   - Deployment orders received
  │   - Leave date: 24-72 hours
  │   - Duration: 90+ days
  │
  ├─→ Medical Emergency
  │   - Sudden illness/injury
  │   - Hospitalization
  │   - Recovery time unknown
  │
  └─→ Family Emergency
      - Immediate family crisis
      - Bereavement leave
      - Duration: Variable

URGENT (48-Hour Notice):
  ├─→ TDY (Temporary Duty)
  │   - Military training orders
  │   - Duration: 1-4 weeks
  │
  └─→ Short-Term Medical Leave
      - Scheduled surgery
      - Medical appointments

NON-URGENT (1-Week Notice):
  └─→ Last-Minute Leave
      - Personal emergencies
      - Approved time off
```

---

### 6.2 Emergency Coverage Workflow

```
┌─────────────────────────────────────────────────────────┐
│           Emergency Coverage Workflow                    │
└─────────────────────────────────────────────────────────┘

    EMERGENCY OCCURS
        │
        ▼
┌──────────────────────┐
│ 1. Record Absence    │
│ - Person affected    │
│ - Start/End dates    │
│ - Emergency type     │
│ - Deployment orders? │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ 2. Find Affected     │
│    Assignments       │
│ - Query by person    │
│ - Query by date range│
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ 3. Classify Services │
│ - CRITICAL: Must cover│
│ - MEDIUM: Should cover│
│ - LOW: Can cancel    │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ 4. Find Replacements │
│ - Match qualifications│
│ - Check availability │
│ - Prioritize by load │
└──────────┬───────────┘
           │
           ▼
     ┌────┴────┐
     │Coverage │
     │ Found?  │
     └────┬────┘
          │
    ┌─────┴─────┐
    │           │
   YES          NO
    │           │
    ▼           ▼
┌─────────┐  ┌──────────┐
│ 5a.     │  │ 5b.      │
│ Assign  │  │ Escalate │
│ Replace-│  │ - Critical│
│ ment    │  │ - Manual │
└────┬────┘  │ - Alert  │
     │       └─────┬────┘
     │             │
     └──────┬──────┘
            │
            ▼
    ┌──────────────┐
    │ 6. Notify    │
    │ - Replacement│
    │ - Coordinator│
    │ - Residents  │
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │ 7. Monitor   │
    │ - Track gaps │
    │ - Update as  │
    │   available  │
    └──────────────┘
```

---

### 6.3 Service Prioritization

**Priority Matrix:**

```
┌───────────────────────────────────────────────────┐
│            Service Priority Matrix                 │
├───────────────────────────────────────────────────┤
│ Priority │ Service Type        │ Action           │
├──────────┼─────────────────────┼──────────────────┤
│ CRITICAL │ Inpatient Coverage  │ MUST find replace│
│          │ Emergency Call      │ Escalate if none │
│          │ Critical Procedures │                  │
├──────────┼─────────────────────┼──────────────────┤
│ HIGH     │ Outpatient Clinic   │ Find replacement │
│          │ Scheduled Procedures│ OR reschedule    │
│          │ Urgent Consults     │                  │
├──────────┼─────────────────────┼──────────────────┤
│ MEDIUM   │ Elective Clinic     │ Reschedule OK    │
│          │ Non-urgent Procedures│                 │
│          │ Admin Time          │                  │
├──────────┼─────────────────────┼──────────────────┤
│ LOW      │ Education/Conference│ Cancel OK        │
│          │ Research Time       │                  │
│          │ CME Activities      │                  │
└──────────┴─────────────────────┴──────────────────┘
```

---

### 6.4 Replacement Selection Algorithm

```python
def find_replacement(assignment):
    """
    Find best replacement for emergency absence.

    Priority:
    1. Same qualifications (PGY level, specialty)
    2. Available (no absences, no conflicts)
    3. Lowest current workload
    4. Not already on this service
    """

    # Step 1: Get candidates
    candidates = get_people_of_same_type(assignment.person)

    # Step 2: Filter unavailable
    candidates = [c for c in candidates
                  if is_available(c, assignment.block)]

    # Step 3: Filter already assigned
    candidates = [c for c in candidates
                  if not already_assigned(c, assignment.block)]

    # Step 4: Score candidates
    for candidate in candidates:
        score = 0

        # Prefer same PGY level
        if candidate.pgy_level == assignment.person.pgy_level:
            score += 10

        # Prefer lower workload
        workload = get_workload(candidate)
        score += (100 - workload)  # Invert so lower is better

        # Prefer specialty match if needed
        if assignment.requires_specialty:
            if candidate.has_specialty(assignment.specialty):
                score += 20

        candidate.score = score

    # Step 5: Return best match
    candidates.sort(key=lambda c: c.score, reverse=True)
    return candidates[0] if candidates else None
```

---

### 6.5 Emergency Coverage Example

**Scenario: Military Deployment**

```
┌──────────────────────────────────────────┐
│      Emergency Coverage Request          │
├──────────────────────────────────────────┤
│                                          │
│ Type: Military Deployment                │
│ Faculty: Dr. James Rodriguez             │
│ Start Date: 2025-07-10                   │
│ End Date: 2025-10-10 (90 days)          │
│ Deployment Orders: ✓ Verified            │
│                                          │
│ Affected Assignments: 54 blocks          │
│                                          │
│ Service Breakdown:                       │
│ - FMIT Inpatient: 20 blocks (CRITICAL)  │
│ - Clinic: 28 blocks (HIGH)               │
│ - Conference: 6 blocks (LOW)             │
│                                          │
│    [Cancel]  [Find Coverage]             │
└──────────────────────────────────────────┘
```

**Coverage Results:**

```
┌──────────────────────────────────────────┐
│      Emergency Coverage Results          │
├──────────────────────────────────────────┤
│                                          │
│ Status: ⚠ Partial Coverage               │
│                                          │
│ Summary:                                 │
│ ✓ Replacements Found: 48 blocks          │
│ ⚠ Coverage Gaps: 6 blocks                │
│ ✗ Cancelled: 6 blocks (conference)       │
│                                          │
│ Critical Services:                       │
│ ✓ All FMIT covered (20/20)               │
│                                          │
│ Clinic Coverage:                         │
│ ✓ Covered: 22 blocks                     │
│ ⚠ Gaps: 6 blocks (need manual review)   │
│                                          │
│ Coverage Gaps Requiring Attention:       │
│                                          │
│ 1. 2025-07-15 PM - Clinic                │
│    ⚠ No available replacement            │
│    Action: [Find Manually] [Cancel]      │
│                                          │
│ 2. 2025-07-22 AM - Clinic                │
│    ⚠ Only PGY-1 available (needs PGY-2)  │
│    Action: [Override] [Cancel]           │
│                                          │
│ 3. 2025-08-05 PM - Procedures            │
│    ⚠ No credentialed faculty available   │
│    Action: [Escalate] [Reschedule]       │
│                                          │
│ Replacement Details:                     │
│ - Dr. Smith: +12 blocks                  │
│ - Dr. Johnson: +10 blocks                │
│ - Dr. Williams: +8 blocks                │
│ - Dr. Davis: +6 blocks                   │
│ - Dr. Martinez: +12 blocks               │
│                                          │
│ Notifications Sent:                      │
│ ✓ Replacement faculty (5)                │
│ ✓ Program coordinator                    │
│ ✓ Residents on affected services         │
│ ✓ Nursing staff                          │
│                                          │
│    [Review Gaps]  [Confirm Coverage]     │
└──────────────────────────────────────────┘
```

---

### 6.6 Manual Gap Resolution

For coverage gaps that auto-matching cannot fill:

```
┌──────────────────────────────────────────┐
│        Manual Gap Resolution             │
├──────────────────────────────────────────┤
│ Gap: 2025-07-15 PM - Clinic              │
│ Original: Dr. Rodriguez                  │
│ Status: ⚠ UNCOVERED - CRITICAL           │
│                                          │
│ Candidates:                              │
│                                          │
│ ○ Dr. Smith (PGY-2)                      │
│   Current Load: 78 hrs/week              │
│   Available: ✓                           │
│   Qualified: ✓                           │
│   Impact: +6 hrs (84 hrs/week) ⚠         │
│                                          │
│ ○ Dr. Taylor (PGY-3)                     │
│   Current Load: 72 hrs/week              │
│   Available: Partial (has AM only)       │
│   Qualified: ✓                           │
│   Impact: +6 hrs (78 hrs/week) ✓         │
│                                          │
│ ○ Cancel Clinic Session                  │
│   Impact: Reschedule 12 patients         │
│   Notify: Patients + Front desk          │
│                                          │
│ ○ Use Locum Faculty                      │
│   Cost: $800 for half-day                │
│   Availability: Must verify              │
│                                          │
│ Recommended: Dr. Taylor (best fit)       │
│                                          │
│    [Cancel]  [Assign Selected]           │
└──────────────────────────────────────────┘
```

---

## 7. Common Scenarios

### Scenario 1: New Academic Year Setup

**Task:** Set up scheduling for July 1, 2025 - June 30, 2026

**Steps:**

```
1. Configure Academic Year
   → Settings → Academic Year
   → Start: 2025-07-01, End: 2026-06-30
   → Save

2. Create/Update Rotation Templates
   → Settings → Rotation Templates
   → Verify templates exist:
      ✓ PGY-1 Clinic (1:2 supervision)
      ✓ PGY-2 Clinic (1:4 supervision)
      ✓ FMIT Inpatient (leave_eligible=false)
      ✓ Procedures
      ✓ Conference

3. Import Resident List
   → People → Import
   → Upload CSV with:
      - Name
      - PGY Level
      - Start Date
      - Specialty (if any)

4. Import Faculty List
   → People → Import
   → Include faculty specialties/credentials

5. Add Known Absences
   → Absences → Bulk Import
   → Include:
      - Scheduled vacations
      - Conference dates
      - Known deployments

6. Generate Initial Schedule
   → Schedule → Generate
   → Algorithm: Hybrid
   → Check: All constraints enabled
   → Generate

7. Review and Refine
   → Check ACGME compliance
   → Review coverage gaps
   → Manual adjustments as needed

8. Publish Schedule
   → Mark as active
   → Notify all faculty/residents
```

---

### Scenario 2: Mid-Year Resident Addition

**Task:** Add new PGY-2 resident starting January 1, 2026

**Steps:**

```
1. Add Person Record
   → People → Add Person
   → Name: Dr. Sarah Chen
   → Type: Resident
   → PGY Level: 2
   → Start Date: 2026-01-01

2. Determine Rotation Needs
   → Calculate required rotations for PGY-2
   → Identify open slots in existing schedule

3. Partial Schedule Generation
   → Schedule → Generate
   → Date Range: 2026-01-01 to 2026-06-30
   → PGY Filter: PGY-2 only
   → Algorithm: CP-SAT (to optimize fit)

4. Validation
   → Check no conflicts with existing assignments
   → Verify ACGME compliance
   → Check supervision ratios

5. Faculty Adjustment
   → Blocks with Dr. Chen may need +1 faculty
   → Auto-assign or manual assignment

6. Notify
   → Email Dr. Chen with schedule
   → Notify program coordinator
   → Update resident roster
```

---

### Scenario 3: Emergency Deployment

**Task:** Handle sudden military deployment with 48-hour notice

**Steps:**

```
1. Record Deployment
   → Absences → Emergency Absence
   → Person: Dr. Martinez
   → Type: Military Deployment
   → Start: 2025-08-01
   → End: 2025-11-01 (90 days)
   → Upload: Deployment orders

2. System Auto-Coverage
   → Emergency Coverage → Find Replacements
   → System searches for coverage
   → Results:
      - 42/48 blocks covered
      - 6 gaps identified

3. Manual Gap Resolution
   → Review 6 uncovered blocks
   → Options for each:
      a. Assign to specific faculty
      b. Cancel non-critical services
      c. Use locum coverage
      d. Reschedule patients

4. ACGME Re-Validation
   → Check replacement faculty don't exceed 80-hour
   → Verify supervision ratios maintained
   → Fix any violations

5. Notification Cascade
   → Dr. Martinez: Confirmation
   → Replacement faculty: New assignments
   → Residents: Service changes
   → Clinic staff: Schedule updates
   → Patients: Rescheduling (if needed)

6. Monitor
   → Track workload on replacement faculty
   → Watch for burnout indicators
   → Plan for return (Nov 1)
```

---

### Scenario 4: Faculty Swap Request

**Task:** Two faculty want to swap their FMIT weeks

**Steps:**

```
1. Faculty A Submits Request
   → Schedule → Request Swap
   → My Week: Aug 11 (FMIT)
   → Swap With: Dr. Johnson
   → Type: One-to-One
   → Their Week: Sep 15 (FMIT)
   → Reason: "Wedding anniversary"

2. System Validation
   → Check Dr. Johnson available Aug 11: ✓
   → Check Dr. Smith available Sep 15: ✓
   → Back-to-back check: ✓ No conflict
   → ACGME compliance: ✓ OK
   → Call cascade impact: ⚠ Friday call affected

3. Auto-Match Score
   → Compatibility: 92%
   → Factors:
      - Date proximity: High (35 days apart)
      - Both weeks preferred: Yes
      - Workload balanced: Yes
      - No past rejections

4. Notify Dr. Johnson
   → Email sent with swap details
   → 48-hour response window
   → Auto-reminder at 24 hours

5. Dr. Johnson Approves
   → Clicks "Approve" in email
   → System records approval

6. Execute Swap
   → Week Aug 11: Smith → Johnson
   → Week Sep 15: Johnson → Smith
   → Update call schedule:
      - Aug 11 Friday: Smith → Johnson
      - Sep 15 Friday: Johnson → Smith
   → Record swap in database

7. 24-Hour Rollback Window
   → Either party can reverse within 24 hrs
   → After 24 hrs: Permanent

8. Notifications
   → Both faculty: Confirmation
   → Residents: Service change notice
   → Coordinator: Log entry
```

---

### Scenario 5: ACGME Violation Detected

**Task:** Resident exceeds 80-hour rule after schedule change

**Detection:**

```
ALERT: ACGME Violation Detected

Resident: Dr. Emily Carter (PGY-1)
Violation Type: 80-Hour Rule
Window: 2025-07-01 to 2025-07-28
Current Hours: 86 hours/week
Limit: 80 hours/week
Excess: 6 hours/week (1 block)

Trigger: Swap execution added extra shift
```

**Resolution Workflow:**

```
1. Immediate Alert
   → Email to program coordinator
   → Dashboard warning
   → Block further schedule changes

2. Auto-Resolution Attempt
   → Find 1 assignment to redistribute
   → Candidates:
      a. 2025-07-22 PM - Clinic (elective)
      b. 2025-07-24 AM - Conference (low priority)

   → Find replacement residents with capacity:
      - Dr. James: 72 hrs/week (can take +6)
      - Dr. Lisa: 74 hrs/week (can take +6)

   → Propose: Move 2025-07-24 AM to Dr. James

3. Coordinator Review
   → Option A: Accept auto-resolution
   → Option B: Manual reassignment
   → Option C: Cancel assignment

4. Execute Resolution
   → Move conference assignment
   → Dr. Carter: 86 → 80 hrs/week ✓
   → Dr. James: 72 → 78 hrs/week ✓

5. Re-Validate
   → Run full ACGME check
   → Confirm: No violations
   → Clear alert

6. Document
   → Log violation + resolution
   → Update audit trail
   → Notify Dr. Carter of change
```

---

### Scenario 6: Quarterly Schedule Review

**Task:** Program coordinator reviews schedule health

**Review Dashboard:**

```
┌──────────────────────────────────────────┐
│      Quarterly Schedule Health Check     │
├──────────────────────────────────────────┤
│ Period: Q1 2025 (Jul-Sep)                │
│                                          │
│ ACGME Compliance:        ✓ PASS          │
│ ├─ 80-Hour Rule:         0 violations    │
│ ├─ 1-in-7 Rule:          0 violations    │
│ └─ Supervision Ratios:   0 violations    │
│                                          │
│ Coverage Metrics:                        │
│ ├─ Coverage Rate:        97.2%           │
│ ├─ Critical Gaps:        0               │
│ └─ Understaffed Blocks:  4 (minor)       │
│                                          │
│ Workload Distribution:                   │
│ ├─ Mean: 76 hrs/week                     │
│ ├─ Std Dev: 4.2 hrs                      │
│ ├─ Max: 80 hrs (Dr. Smith)               │
│ └─ Min: 68 hrs (Dr. Taylor)              │
│                                          │
│ Resilience Metrics:                      │
│ ├─ Utilization: 79.1% ✓                  │
│ ├─ N-1 Compliant: ✓ Yes                  │
│ ├─ N-2 Compliant: ✓ Yes                  │
│ ├─ Hub Protection: Active                │
│ └─ Phase Risk: Low                       │
│                                          │
│ Swap Activity:                           │
│ ├─ Requests: 12                          │
│ ├─ Executed: 10                          │
│ ├─ Rejected: 2                           │
│ └─ Rollbacks: 0                          │
│                                          │
│ Emergency Coverage:                      │
│ ├─ Deployments: 1 (Dr. Rodriguez)        │
│ ├─ Medical: 2                            │
│ └─ Coverage Rate: 94% (6 manual gaps)    │
│                                          │
│ Recommendations:                         │
│ ⚠ Consider rebalancing Dr. Smith's load  │
│ ⚠ 4 understaffed blocks in Sep - review  │
│ ✓ Overall: Schedule is healthy           │
│                                          │
│    [Export Report]  [View Details]       │
└──────────────────────────────────────────┘
```

---

## Appendices

### Appendix A: Constraint Weights

Default constraint weights for the Hybrid algorithm:

```python
CONSTRAINT_WEIGHTS = {
    # ACGME (Hard - Must Satisfy)
    "80_hour_rule": CRITICAL,
    "1_in_7_rule": CRITICAL,
    "supervision_ratio": CRITICAL,
    "availability": CRITICAL,

    # Resilience (Soft - Optimize)
    "hub_protection": 0.30,
    "utilization_buffer": 0.20,
    "n1_vulnerability": 0.20,
    "zone_boundary": 0.10,

    # Educational (Soft)
    "rotation_diversity": 0.15,
    "skill_progression": 0.10,

    # Operational (Soft)
    "workload_balance": 0.25,
    "preference_alignment": 0.10,
}
```

---

### Appendix B: API Endpoints

Key API endpoints for scheduling operations:

```
POST   /api/schedule/generate
  - Generate a new schedule
  - Body: { start_date, end_date, algorithm, pgy_levels }

GET    /api/schedule/validate/{start_date}/{end_date}
  - Validate existing schedule
  - Returns: ValidationResult

POST   /api/swaps/request
  - Submit swap request
  - Body: { source_week, target_faculty, swap_type }

GET    /api/swaps/matches/{request_id}
  - Get auto-match suggestions

POST   /api/swaps/approve/{swap_id}
  - Approve a swap request

POST   /api/swaps/rollback/{swap_id}
  - Rollback an executed swap

POST   /api/emergency/coverage
  - Handle emergency absence
  - Body: { person_id, start_date, end_date, reason }

GET    /api/resilience/health
  - Get resilience health report
```

---

### Appendix C: Troubleshooting

Common issues and solutions:

**Issue:** Schedule generation times out

```
Causes:
  - Too many residents (>100)
  - Too many constraints enabled
  - Complex rotation requirements

Solutions:
  1. Use Greedy algorithm for initial draft
  2. Generate by PGY level separately
  3. Increase timeout to 600 seconds
  4. Disable non-critical soft constraints
```

**Issue:** No valid schedule found

```
Causes:
  - Over-constrained problem
  - Insufficient faculty
  - Too many absences

Solutions:
  1. Review constraint conflicts
  2. Check if absences block too many residents
  3. Add more faculty or reduce resident count
  4. Relax soft constraints
  5. Use CP-SAT to prove infeasibility
```

**Issue:** Swap validation fails

```
Causes:
  - Back-to-back FMIT weeks
  - External conflicts (absences)
  - ACGME violations

Solutions:
  1. Choose different target week
  2. Check faculty absence calendar
  3. Use auto-matcher to find valid partners
```

---

## Summary

This guide covers the complete scheduling workflows:

1. **Schedule Creation**: Set up academic year, templates, and constraints
2. **Schedule Generation**: Run algorithms to create compliant schedules
3. **Validation**: Check ACGME compliance and coverage requirements
4. **Conflict Resolution**: Identify and fix scheduling issues
5. **Swap Workflow**: Enable faculty to trade weeks with validation
6. **Emergency Coverage**: Handle unexpected absences with automated replacement

**Key Principles:**

- **ACGME Compliance First**: All schedules must meet duty hour and supervision requirements
- **Automation with Oversight**: Use algorithms for speed, humans for judgment
- **Resilience by Design**: Build schedules that can survive unexpected changes
- **Transparency**: Clear workflows, validation results, and audit trails

**For Support:**

- Technical issues: Check logs in `/var/log/scheduler/`
- ACGME questions: Consult program director
- System errors: Contact IT administrator

---

*Last Updated: 2025-12-19*
*Version: 1.0*
*Maintainer: Residency Program Coordinator*
