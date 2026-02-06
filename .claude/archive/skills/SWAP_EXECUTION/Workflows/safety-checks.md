# Safety Checks Workflow

Phase 2 of swap execution: Validate swap doesn't break rules or degrade system health.

## Purpose

Prevent swaps that would:
- Violate ACGME compliance rules
- Create scheduling conflicts
- Degrade resilience metrics
- Cause fairness issues

## Three-Tier Validation

Safety checks are organized in **three tiers** with escalating strictness:

```
Tier 1: Hard Constraints (MUST PASS)
   ↓
Tier 2: Soft Constraints (WARN but may proceed)
   ↓
Tier 3: Resilience Impact (MONITOR but allow)
```

### Decision Logic

```python
def evaluate_swap_safety(request: StructuredSwapRequest) -> Decision:
    """
    Evaluate swap request against all safety tiers.

    Returns:
        Decision: REJECT | FLAG | PROCEED
    """
    tier1_result = check_tier1_hard_constraints(request)
    if tier1_result.has_violations:
        return Decision.REJECT  # Hard stop

    tier2_result = check_tier2_soft_constraints(request)
    if tier2_result.has_critical_warnings:
        return Decision.FLAG  # Escalate for approval

    tier3_result = check_tier3_resilience_impact(request)
    if tier3_result.degradation > 0.15:  # >15% degradation
        return Decision.FLAG  # Escalate for approval

    return Decision.PROCEED  # Execute immediately
```

---

## Tier 1: Hard Constraints (MUST PASS)

These are **ACGME compliance rules** that cannot be violated. Any failure = instant rejection.

### 1.1 80-Hour Work Week Rule

**Rule:** Maximum 80 hours per week, averaged over rolling 4-week period

```python
from app.services.work_hour_calculator import WorkHourCalculator

calculator = WorkHourCalculator(db)

# Calculate impact for BOTH parties
source_hours_before = calculator.get_4week_average(
    person_id=request.source_faculty.id,
    week_ending=request.source_week
)
source_hours_after = calculator.get_4week_average_after_swap(
    person_id=request.source_faculty.id,
    week_ending=request.source_week,
    swap_delta=-FMIT_WEEK_HOURS  # Giving away week
)

target_hours_before = calculator.get_4week_average(
    person_id=request.target_faculty.id,
    week_ending=request.source_week
)
target_hours_after = calculator.get_4week_average_after_swap(
    person_id=request.target_faculty.id,
    week_ending=request.source_week,
    swap_delta=+FMIT_WEEK_HOURS  # Taking on week
)

# Check violations
MAX_HOURS = 80.0
WARN_THRESHOLD = 75.0

if target_hours_after > MAX_HOURS:
    return ValidationError(
        code="80_HOUR_VIOLATION",
        severity="error",
        message=f"{request.target_faculty.name} would exceed 80-hour limit "
                f"({target_hours_after:.1f} hours after swap)"
    )

if target_hours_after > WARN_THRESHOLD:
    warnings.append(
        ValidationError(
            code="APPROACHING_80_HOUR_LIMIT",
            severity="warning",
            message=f"{request.target_faculty.name} would be at "
                    f"{target_hours_after:.1f}/80 hours (>{WARN_THRESHOLD}h threshold)"
        )
    )
```

### 1.2 1-in-7 Day Off Rule

**Rule:** One 24-hour period off every 7 days

```python
from app.services.day_off_validator import DayOffValidator

validator = DayOffValidator(db)

# Check if target faculty loses their day off
target_days_off = validator.count_days_off_in_period(
    person_id=request.target_faculty.id,
    start_date=request.source_week,
    end_date=request.source_week + timedelta(days=6)
)

if target_days_off < 1:
    return ValidationError(
        code="1_IN_7_VIOLATION",
        severity="error",
        message=f"{request.target_faculty.name} would have no days off "
                f"in week {request.source_week} after taking this FMIT week"
    )
```

### 1.3 Supervision Ratios

**Rule:** PGY-1: 2:1 max, PGY-2/3: 4:1 max faculty-to-resident ratio

```python
from app.services.supervision_validator import SupervisionValidator

validator = SupervisionValidator(db)

# Calculate supervision ratios for the affected week
ratio_before = validator.get_supervision_ratio(
    date=request.source_week,
    rotation="inpatient"
)

# Simulate ratio after swap (source faculty removed, target added)
ratio_after = validator.get_supervision_ratio_after_swap(
    date=request.source_week,
    rotation="inpatient",
    remove_faculty=request.source_faculty.id,
    add_faculty=request.target_faculty.id
)

if ratio_after.pgy1_ratio > 2.0:
    return ValidationError(
        code="SUPERVISION_RATIO_VIOLATION",
        severity="error",
        message=f"PGY-1 supervision ratio would be {ratio_after.pgy1_ratio:.1f}:1 "
                f"(max 2:1) if {request.source_faculty.name} swaps out"
    )
```

### 1.4 Past Date Check

**Rule:** Cannot swap dates in the past

```python
from datetime import date

today = date.today()

if request.source_week < today:
    return ValidationError(
        code="PAST_DATE",
        severity="error",
        message=f"Cannot swap past week {request.source_week} (today is {today})"
    )

if request.target_week and request.target_week < today:
    return ValidationError(
        code="PAST_DATE",
        severity="error",
        message=f"Cannot swap into past week {request.target_week}"
    )
```

---

## Tier 2: Soft Constraints (WARN but may proceed)

These are **fairness and quality** rules. Violations trigger warnings and may require approval.

### 2.1 Back-to-Back FMIT Weeks

**Rule:** Avoid consecutive FMIT weeks (burnout risk)

```python
from app.services.xlsx_import import has_back_to_back_conflict

# Get target's existing FMIT weeks
existing_weeks = get_faculty_fmit_weeks(request.target_faculty.id)

# Check if adding source week creates back-to-back
new_weeks = sorted(existing_weeks + [request.source_week])

if has_back_to_back_conflict(new_weeks):
    # Find which weeks are adjacent
    adjacent_weeks = find_adjacent_weeks(new_weeks)

    return ValidationError(
        code="BACK_TO_BACK_FMIT",
        severity="warning",
        message=f"{request.target_faculty.name} would have back-to-back FMIT "
                f"weeks: {adjacent_weeks[0]} and {adjacent_weeks[1]} (burnout risk)"
    )
```

### 2.2 External Conflicts (Absences, TDY, Leave)

**Rule:** Cannot schedule during approved absences

```python
from app.models.absence import Absence

# Check target faculty absences during source week
week_end = request.source_week + timedelta(days=6)

conflict = db.query(Absence).filter(
    Absence.person_id == request.target_faculty.id,
    Absence.start_date <= week_end,
    Absence.end_date >= request.source_week,
    Absence.is_blocking == True  # Only blocking absences
).first()

if conflict:
    return ValidationError(
        code="EXTERNAL_CONFLICT",
        severity="error",
        message=f"{request.target_faculty.name} has {conflict.absence_type} "
                f"from {conflict.start_date} to {conflict.end_date}, "
                f"overlapping with requested week {request.source_week}"
    )
```

### 2.3 Coverage Gaps

**Rule:** Ensure FMIT coverage isn't dropped entirely

```python
from app.services.coverage_validator import CoverageValidator

validator = CoverageValidator(db)

# Check if source week has backup coverage
source_coverage = validator.get_week_coverage(
    week=request.source_week,
    rotation="FMIT"
)

if source_coverage.faculty_count == 1 and request.swap_type == SwapType.ABSORB:
    # Source is only person covering, and they're giving it away
    return ValidationError(
        code="COVERAGE_GAP",
        severity="error",
        message=f"Week {request.source_week} would have no FMIT coverage "
                f"if {request.source_faculty.name} absorbs out. "
                f"Find replacement before approving."
    )
```

### 2.4 Same-Day Conflicts (Call Cascade)

**Rule:** Friday/Saturday call assignments cascade with FMIT weeks

```python
from app.services.call_cascade_validator import CallCascadeValidator

validator = CallCascadeValidator(db)

# Check if source week contains Fri/Sat call
has_weekend_call = validator.has_weekend_call_in_week(request.source_week)

if has_weekend_call:
    # Get current call assignments for that weekend
    current_calls = validator.get_weekend_calls(request.source_week)

    warnings.append(
        ValidationError(
            code="CALL_CASCADE_AFFECTED",
            severity="warning",
            message=f"Week {request.source_week} includes weekend call "
                    f"({current_calls}). Call assignments will transfer to "
                    f"{request.target_faculty.name}."
        )
    )
```

### 2.5 Imminent Swap Warning

**Rule:** Warn if swap is within 2 weeks (short notice)

```python
from datetime import date, timedelta

NOTICE_WARNING_DAYS = 14

days_until_swap = (request.source_week - date.today()).days

if days_until_swap < NOTICE_WARNING_DAYS:
    warnings.append(
        ValidationError(
            code="IMMINENT_SWAP",
            severity="warning",
            message=f"Week {request.source_week} is only {days_until_swap} days away. "
                    f"Short notice may impact coverage planning."
        )
    )
```

---

## Tier 3: Resilience Impact Assessment

Measure how swap affects **system-wide resilience metrics**.

### 3.1 Utilization Impact

**Rule:** Monitor if swap pushes utilization > 80% threshold

```python
from app.resilience.utilization_calculator import calculate_utilization_impact

# Calculate current utilization
current_utilization = calculate_utilization(
    date_range=(request.source_week, request.source_week + timedelta(days=6))
)

# Simulate utilization after swap
simulated_utilization = calculate_utilization_after_swap(
    date_range=(request.source_week, request.source_week + timedelta(days=6)),
    remove_faculty=request.source_faculty.id,
    add_faculty=request.target_faculty.id
)

UTILIZATION_THRESHOLD = 0.80
UTILIZATION_DANGER = 0.85

if simulated_utilization > UTILIZATION_DANGER:
    return ValidationError(
        code="UTILIZATION_CRITICAL",
        severity="error",
        message=f"Swap would push utilization to {simulated_utilization:.1%} "
                f"(danger threshold: {UTILIZATION_DANGER:.1%}). Reject to "
                f"prevent cascade failure risk."
    )

if simulated_utilization > UTILIZATION_THRESHOLD:
    warnings.append(
        ValidationError(
            code="UTILIZATION_HIGH",
            severity="warning",
            message=f"Swap would increase utilization from {current_utilization:.1%} "
                    f"to {simulated_utilization:.1%} (threshold: {UTILIZATION_THRESHOLD:.1%})"
        )
    )
```

### 3.2 N-1 Contingency Check

**Rule:** Ensure schedule can still function if one person drops

```python
from app.resilience.n_minus_analysis import run_n_minus_1_check

# Run N-1 analysis for affected week
n1_result = run_n_minus_1_check(
    week=request.source_week,
    simulate_swap={
        "remove": request.source_faculty.id,
        "add": request.target_faculty.id
    }
)

if n1_result.critical_failures > 0:
    return ValidationError(
        code="N_MINUS_1_FAILURE",
        severity="error",
        message=f"Swap would create {n1_result.critical_failures} critical "
                f"coverage gaps if any one person becomes unavailable. "
                f"Affected dates: {n1_result.failure_dates}"
    )
```

### 3.3 Blast Radius Assessment

**Rule:** Limit cascading impact of swap on other schedules

```python
from app.resilience.blast_radius import calculate_blast_radius

blast_radius = calculate_blast_radius(
    swap_request=request,
    max_depth=3  # Check 3 levels of dependencies
)

if blast_radius.affected_assignments > 10:
    warnings.append(
        ValidationError(
            code="LARGE_BLAST_RADIUS",
            severity="warning",
            message=f"Swap affects {blast_radius.affected_assignments} other "
                    f"assignments due to dependency cascade. Review carefully."
        )
    )
```

---

## Decision Tree

Combine all tier results into final decision:

```python
@dataclass
class SafetyCheckResult:
    """Aggregated safety check result."""

    tier1_violations: list[ValidationError]
    tier2_warnings: list[ValidationError]
    tier3_metrics: dict[str, float]
    decision: Decision  # REJECT | FLAG | PROCEED

    @property
    def is_safe(self) -> bool:
        return self.decision == Decision.PROCEED

    @property
    def needs_approval(self) -> bool:
        return self.decision == Decision.FLAG

    @property
    def is_rejected(self) -> bool:
        return self.decision == Decision.REJECT


def make_safety_decision(
    tier1: list[ValidationError],
    tier2: list[ValidationError],
    tier3: dict[str, float]
) -> Decision:
    """
    Decision logic based on tier results.

    Rules:
    1. Any Tier 1 violation → REJECT
    2. Tier 2 critical warning → FLAG for approval
    3. Tier 3 degradation > 15% → FLAG for approval
    4. Otherwise → PROCEED

    Returns:
        Decision: REJECT | FLAG | PROCEED
    """
    # Tier 1: Hard stop on violations
    if any(e.severity == "error" for e in tier1):
        return Decision.REJECT

    # Tier 2: Escalate critical warnings
    critical_tier2 = [
        "BACK_TO_BACK_FMIT",
        "COVERAGE_GAP",
        "EXTERNAL_CONFLICT"
    ]
    if any(e.code in critical_tier2 for e in tier2):
        return Decision.FLAG

    # Tier 3: Escalate significant degradation
    if tier3.get("utilization_delta", 0) > 0.15:  # >15% increase
        return Decision.FLAG

    if tier3.get("n1_failures", 0) > 0:
        return Decision.FLAG

    # All checks passed
    return Decision.PROCEED
```

---

## Output Format

Safety check results are returned as:

```python
{
    "decision": "PROCEED",  # or "REJECT" or "FLAG"
    "tier1_hard_constraints": {
        "80_hour_rule": "PASS",
        "1_in_7_rule": "PASS",
        "supervision_ratios": "PASS",
        "past_date_check": "PASS"
    },
    "tier2_soft_constraints": {
        "back_to_back": "WARN - would create consecutive weeks",
        "external_conflicts": "PASS",
        "coverage_gaps": "PASS",
        "call_cascade": "WARN - weekend call transfers"
    },
    "tier3_resilience": {
        "utilization_before": 0.72,
        "utilization_after": 0.75,
        "utilization_delta": 0.03,
        "n1_contingency": "PASS",
        "blast_radius": 3
    },
    "warnings": [
        {
            "code": "BACK_TO_BACK_FMIT",
            "severity": "warning",
            "message": "Dr. Smith would have back-to-back FMIT weeks: 2025-02-03 and 2025-02-10"
        },
        {
            "code": "IMMINENT_SWAP",
            "severity": "warning",
            "message": "Week 2025-02-03 is only 10 days away"
        }
    ],
    "rationale": "All hard constraints satisfied. Two warnings flagged but non-critical."
}
```

---

## Next Phase

Based on decision:

- **REJECT** → Return to requestor with detailed error message
- **FLAG** → Route to **[escalation-matrix.md](../Reference/escalation-matrix.md)** for approval
- **PROCEED** → Continue to **[audit-trail.md](audit-trail.md)** for execution

---

## Quick Reference

### Key Validators

| Validator | Purpose | Location |
|-----------|---------|----------|
| `SwapValidationService` | Main orchestrator | `app/services/swap_validation.py` |
| `WorkHourCalculator` | 80-hour rule | `app/services/work_hour_calculator.py` |
| `SupervisionValidator` | Ratio checks | `app/services/supervision_validator.py` |
| `CoverageValidator` | Gap detection | `app/services/coverage_validator.py` |

### Constraint Weights

```python
TIER_1_VIOLATIONS = [
    "80_HOUR_VIOLATION",
    "1_IN_7_VIOLATION",
    "SUPERVISION_RATIO_VIOLATION",
    "PAST_DATE",
    "EXTERNAL_CONFLICT"
]

TIER_2_CRITICAL = [
    "BACK_TO_BACK_FMIT",
    "COVERAGE_GAP"
]

TIER_3_THRESHOLDS = {
    "utilization_delta": 0.15,  # 15% increase
    "n1_failures": 0,           # Zero tolerance
    "blast_radius": 10          # Max 10 affected assignments
}
```
