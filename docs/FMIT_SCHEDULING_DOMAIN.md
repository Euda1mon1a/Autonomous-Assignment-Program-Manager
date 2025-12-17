# FMIT Faculty Scheduling Domain Model

This document captures the complete domain knowledge for Family Medicine Inpatient Teaching (FMIT) faculty scheduling, extracted from operational experience. It serves as a requirements specification for automating conflict detection and swap recommendations.

## Overview

FMIT scheduling assigns faculty members to weekly inpatient teaching rotations across an academic year (13 blocks, ~4 weeks each, starting July 1). The process involves:

1. Initial annual schedule creation (typically done in spring for next AY)
2. Ongoing conflict resolution as constraints emerge (leave, conferences, departures)
3. Swap coordination between faculty members

## Terminology

| Term | Definition |
|------|------------|
| **Block** | A ~4-week scheduling period. 13 blocks per academic year (Jul 1 - Jun 30) |
| **Rotation/Template** | A type of assignment (e.g., Sports Medicine, FMIT, Procedures). Independent of time. |
| **FMIT** | Family Medicine Inpatient Teaching - the weekly faculty rotation being scheduled |
| **Week** | 4 weeks per block (Wk 1-4). FMIT assignments are weekly. |
| **Call** | On-call duty. Two types: Sun-Thurs (overnight) and Fri-Sat (weekend, tied to FMIT) |
| **PCAT** | Post-Call Attending - automatic half-day clinic duty after Sun-Thurs call |
| **DO** | Direct Observation - automatic half-day after Sun-Thurs call |

## Hard Constraints (Must Not Violate)

### 1. No Back-to-Back FMIT Weeks

**Rule**: A faculty member cannot have FMIT in consecutive weeks.

**Rationale**: FMIT weeks include mandatory Fri PM + Sat PM call, creating continuous duty from Friday AM through Sunday PM. Back-to-back weeks would create 14+ consecutive days with embedded 24-hour shifts - a patient safety issue.

**Implementation**:
```python
def has_back_to_back_conflict(faculty_weeks: List[date]) -> bool:
    """Check if any two FMIT weeks are consecutive."""
    sorted_weeks = sorted(faculty_weeks)
    for i in range(len(sorted_weeks) - 1):
        if (sorted_weeks[i+1] - sorted_weeks[i]).days <= 7:
            return True
    return False
```

### 2. Call Cascade Rules

**FMIT Week Call Assignment**:
- Fri PM call: **Locked** to FMIT faculty (mandatory)
- Sat PM call: **Locked** to FMIT faculty (mandatory)
- Sun-Thurs call: **Unavailable** (on FMIT duty)

**Non-FMIT Week Call Assignment**:
- Fri PM call: Available for assignment
- Sat PM call: Available for assignment
- Sun-Thurs call: **Available** for assignment

**Implementation Note**: When swapping FMIT weeks, call assignments must cascade:
```python
@dataclass
class FMITWeekAssignment:
    faculty: str
    week_start: date
    fri_pm_call: bool = True   # Always true for FMIT week
    sat_pm_call: bool = True   # Always true for FMIT week
    sun_thurs_available: bool = False  # Always false during FMIT
```

### 3. PCAT/DO Cascade

**Rule**: Sun-Thurs call triggers automatic half-day clinic duties the following morning.

**Activities**:
- **PCAT** (Post-Call Attending): Morning clinic precepting after overnight call
- **DO** (Direct Observation): Morning resident observation after overnight call

**Implementation Note**: These are downstream effects. When assigning Sun-Thurs call, verify the faculty member doesn't have conflicting morning commitments.

### 4. Specialty Provider Bottlenecks

**Rule**: Some clinic services have a single qualified provider. When that provider is on FMIT, the service cannot operate.

**Example**: If Faculty_SM is the only Sports Medicine provider:
- Faculty_SM on FMIT Week X → Sports Medicine clinic dark Week X
- This may be acceptable or may require locum coverage

**Implementation**:
```python
specialty_providers: Dict[str, List[str]] = {
    "Sports Medicine": ["Faculty_SM"],
    "Procedures": ["Faculty_P1", "Faculty_P2"],  # Multiple = no bottleneck
}

def get_specialty_gaps(fmit_schedule: Dict[str, List[date]]) -> List[SpecialtyGap]:
    """Identify weeks where specialty clinics cannot operate."""
    gaps = []
    for specialty, providers in specialty_providers.items():
        if len(providers) == 1:
            provider = providers[0]
            for week in fmit_schedule.get(provider, []):
                gaps.append(SpecialtyGap(specialty, provider, week))
    return gaps
```

## Soft Constraints (Should Minimize)

### 5. Target Week Distribution

**Rule**: Each faculty member should have ~6 FMIT weeks per academic year.

**Exceptions**:
- Department Chief: Reduced load (1-2 weeks)
- Program Director: Flexible (may have no clinic, used sparingly)
- Adjunct faculty: Cannot be relied upon for coverage

**Implementation**:
```python
@dataclass
class FacultyTarget:
    name: str
    target_weeks: int = 6
    role: str = "faculty"  # "chief", "pd", "adjunct"

    @property
    def flexibility(self) -> str:
        if self.role == "chief":
            return "low"  # Already at minimum
        elif self.role == "pd":
            return "emergency_only"  # Secret weapon
        elif self.role == "adjunct":
            return "unreliable"
        elif self.target_weeks < 6:
            return "high"  # Under target, should take more
        else:
            return "medium"  # At target, can swap 1:1
```

### 6. Alternating Week Pattern Limits

**Rule**: Week-on/week-off alternating is required (see Hard Constraint #1), but too many consecutive alternating cycles creates family hardship.

**Example Problem**:
```
Block 8 Wk 2: Faculty_A (FMIT)
Block 8 Wk 3: [off]
Block 8 Wk 4: Faculty_A (FMIT)
Block 9 Wk 1: [off]
Block 9 Wk 2: Faculty_A (FMIT)
Block 9 Wk 3: [off]
Block 9 Wk 4: Faculty_A (FMIT)
```
This is 4 alternating weeks in 8 weeks - technically legal but burdensome.

**Recommendation**: Flag patterns with 3+ alternating cycles and suggest consolidation swaps.

**Implementation**:
```python
def count_alternating_cycles(weeks: List[date]) -> int:
    """Count consecutive week-on/week-off patterns."""
    sorted_weeks = sorted(weeks)
    cycles = 0
    for i in range(len(sorted_weeks) - 1):
        gap = (sorted_weeks[i+1] - sorted_weeks[i]).days
        if 7 < gap <= 21:  # 2-3 week gap = alternating
            cycles += 1
    return cycles

def has_excessive_alternating(weeks: List[date], threshold: int = 3) -> bool:
    return count_alternating_cycles(weeks) >= threshold
```

## Contextual Constraints (External Data Required)

### 7. Leave and Conference Conflicts

**Rule**: Faculty cannot be assigned FMIT during approved leave or conference attendance.

**Common Conflicts**:
- Personal leave (LV)
- Military TDY
- Conferences (e.g., USAFP - typically March)
- Training requirements

**Implementation Note**: These constraints are not in the FMIT schedule itself. They must be cross-referenced with:
- Leave management system
- Conference registration
- Military orders database

```python
@dataclass
class ExternalConflict:
    faculty: str
    start_date: date
    end_date: date
    type: str  # "leave", "conference", "tdy", "training"
    source: str  # Where this data came from

def check_external_conflicts(
    faculty: str,
    week: date,
    conflicts: List[ExternalConflict]
) -> Optional[ExternalConflict]:
    """Check if faculty has external conflict during week."""
    week_end = week + timedelta(days=6)
    for conflict in conflicts:
        if conflict.faculty == faculty:
            if conflict.start_date <= week_end and conflict.end_date >= week:
                return conflict
    return None
```

### 8. Clinic Schedule Lock Dates

**Rule**: Clinic schedules are released to patients in advance. Changes after release require patient notification.

**Typical Pattern**:
- Clinic schedules released ~3 months ahead
- Changes within release window = high friction
- Changes beyond release window = low friction

**Implementation**:
```python
def get_schedule_flexibility(target_date: date, release_horizon_days: int = 90) -> str:
    """Determine how easy it is to change a date."""
    days_until = (target_date - date.today()).days
    if days_until < 0:
        return "impossible"  # Past
    elif days_until < 14:
        return "very_hard"  # Imminent
    elif days_until < release_horizon_days:
        return "hard"  # Already released to patients
    else:
        return "easy"  # Not yet released
```

## Swap Operations

### 9. Direct Swap (Net Zero)

**Operation**: Faculty_A and Faculty_B exchange weeks.

**Requirements**:
- Neither faculty has back-to-back conflict with new week
- Neither faculty has external conflict with new week
- Both faculty agree

**Implementation**:
```python
def validate_swap(
    faculty_a: str,
    faculty_b: str,
    week_a: date,  # A's current week, B will take
    week_b: date,  # B's current week, A will take
    all_schedules: Dict[str, List[date]],
    external_conflicts: List[ExternalConflict]
) -> SwapValidation:
    """Validate a proposed 1:1 swap."""
    errors = []
    warnings = []

    # Get current schedules
    a_weeks = [w for w in all_schedules[faculty_a] if w != week_a]
    b_weeks = [w for w in all_schedules[faculty_b] if w != week_b]

    # Check back-to-back for A taking week_b
    a_new = sorted(a_weeks + [week_b])
    if has_back_to_back_conflict(a_new):
        errors.append(f"{faculty_a} would have back-to-back conflict with {week_b}")

    # Check back-to-back for B taking week_a
    b_new = sorted(b_weeks + [week_a])
    if has_back_to_back_conflict(b_new):
        errors.append(f"{faculty_b} would have back-to-back conflict with {week_a}")

    # Check external conflicts
    if conflict := check_external_conflicts(faculty_a, week_b, external_conflicts):
        errors.append(f"{faculty_a} has {conflict.type} conflict with {week_b}")
    if conflict := check_external_conflicts(faculty_b, week_a, external_conflicts):
        errors.append(f"{faculty_b} has {conflict.type} conflict with {week_a}")

    # Check schedule flexibility
    flex_a = get_schedule_flexibility(week_a)
    flex_b = get_schedule_flexibility(week_b)
    if flex_a in ["very_hard", "hard"]:
        warnings.append(f"{week_a} is within clinic release window")
    if flex_b in ["very_hard", "hard"]:
        warnings.append(f"{week_b} is within clinic release window")

    return SwapValidation(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings
    )
```

### 10. Coverage Swap (Absorb Week)

**Operation**: Faculty_B takes Faculty_A's week without reciprocal exchange.

**Use Case**: Faculty_A is leaving/unavailable, their weeks must be distributed.

**Requirements**:
- Faculty_B doesn't have back-to-back conflict
- Faculty_B doesn't have external conflict
- Faculty_B is willing to exceed target (or is under target)

## Recommended Libraries and Tools

### Constraint Satisfaction

| Library | Use Case | Notes |
|---------|----------|-------|
| **OR-Tools CP-SAT** | Hard constraint satisfaction | Already in stack. Good for initial schedule generation. |
| **PuLP** | Linear optimization | Already in stack. Good for coverage maximization. |
| **python-constraint** | Simple CSP | Lighter weight for swap validation |

### Date/Time Handling

| Library | Use Case |
|---------|----------|
| **python-dateutil** | Week calculations, relative deltas |
| **pandas** | Schedule DataFrame operations, date range generation |
| **workalendar** | Federal holiday awareness |

### Conflict Detection Enhancements

```python
# Recommended additions to xlsx_import.py

from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from datetime import date, timedelta

@dataclass
class SwapCandidate:
    """A potential swap partner for a target week."""
    faculty: str
    can_take_week: date
    gives_week: Optional[date]  # None if absorbing, date if 1:1 swap
    back_to_back_ok: bool
    external_conflict: Optional[str]
    flexibility: str  # "easy", "hard", "very_hard"

@dataclass
class SwapRecommendation:
    """A recommended swap to resolve a conflict."""
    target_faculty: str
    target_week: date
    reason: str  # "excessive_alternating", "departure", "conflict"
    candidates: List[SwapCandidate]
    priority: str  # "high", "medium", "low"

def find_swap_candidates(
    target_faculty: str,
    target_week: date,
    all_schedules: Dict[str, List[date]],
    faculty_metadata: Dict[str, FacultyTarget],
    external_conflicts: List[ExternalConflict],
    schedule_release_date: date,
) -> List[SwapCandidate]:
    """Find all faculty who could take a given week."""
    candidates = []

    for faculty, weeks in all_schedules.items():
        if faculty == target_faculty:
            continue

        meta = faculty_metadata.get(faculty, FacultyTarget(faculty))

        # Skip unreliable faculty
        if meta.flexibility == "unreliable":
            continue

        # Check back-to-back
        test_weeks = sorted(weeks + [target_week])
        back_to_back_ok = not has_back_to_back_conflict(test_weeks)

        # Check external conflicts
        ext_conflict = check_external_conflicts(faculty, target_week, external_conflicts)

        # Find potential give-back weeks (for 1:1 swap)
        give_weeks = []
        for w in weeks:
            if w > schedule_release_date:  # Only flexible weeks
                # Check if target can take this week
                target_test = sorted([
                    tw for tw in all_schedules[target_faculty]
                    if tw != target_week
                ] + [w])
                if not has_back_to_back_conflict(target_test):
                    if not check_external_conflicts(target_faculty, w, external_conflicts):
                        give_weeks.append(w)

        candidates.append(SwapCandidate(
            faculty=faculty,
            can_take_week=target_week,
            gives_week=give_weeks[0] if give_weeks else None,
            back_to_back_ok=back_to_back_ok,
            external_conflict=ext_conflict.type if ext_conflict else None,
            flexibility=get_schedule_flexibility(target_week),
        ))

    # Sort by viability
    return sorted(candidates, key=lambda c: (
        not c.back_to_back_ok,  # Back-to-back issues first (worst)
        c.external_conflict is not None,  # External conflicts second
        c.gives_week is None,  # Absorb-only third (prefer 1:1)
    ))
```

## What Remains for Human/LLM Judgment

Even with full automation of constraint checking, these decisions require human input:

1. **Prioritization**: When multiple valid swaps exist, which faculty to approach first (relationships, fairness perception, availability for conversation)

2. **External constraint discovery**: Leave plans, conference attendance, and personal circumstances that aren't in any system

3. **Negotiation**: Convincing faculty to accept swaps, especially when going above target weeks

4. **Exception approval**: Overriding soft constraints when necessary (e.g., accepting 7 weeks for one faculty due to departures)

5. **Cascade effects**: Understanding downstream impacts on clinic operations, resident evaluations, and teaching schedules

## Future Enhancements

### Phase 1: Automated Conflict Detection
- [ ] Parse FMIT schedule from Excel
- [ ] Detect back-to-back violations
- [ ] Detect excessive alternating patterns
- [ ] Identify specialty bottlenecks
- [ ] Cross-reference with leave system

### Phase 2: Swap Recommendation Engine
- [ ] Generate valid swap candidates for any week
- [ ] Rank candidates by viability
- [ ] Generate human-readable swap proposals
- [ ] Track swap history for fairness

### Phase 3: LLM Integration
- [ ] Natural language conflict queries ("Who can take Week 8?")
- [ ] Explain why swaps are/aren't valid
- [ ] Draft swap request communications
- [ ] Handle "what-if" scenarios

### Phase 4: Full Automation
- [ ] Integrate with leave management system
- [ ] Integrate with conference registration
- [ ] Automated swap proposal generation
- [ ] Faculty self-service swap portal

---

*Document generated from operational analysis session, December 2024*
*Constraints extracted through iterative dialogue with domain expert*
