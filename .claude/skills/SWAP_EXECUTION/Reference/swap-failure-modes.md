# Swap Failure Modes

Common failure patterns in swap execution with detection methods and mitigation strategies.

## Overview

Swap failures fall into **5 categories**:

1. **Work Hour Creep** - Violations of 80-hour rule
2. **Continuity Breaks** - Loss of patient care handoffs
3. **Coverage Gaps** - Insufficient staffing
4. **Moonlighting Conflicts** - External work commitments
5. **Fairness Violations** - Inequitable workload distribution

Each section below covers:
- **Symptom** - How to detect the failure
- **Root Cause** - Why it happens
- **Detection Method** - Automated checks
- **Mitigation** - How to prevent or fix

---

## 1. Work Hour Creep

### Symptom

Faculty member exceeds 80-hour weekly average after swap, violating ACGME rules.

```
Before swap:
- Dr. Smith: 72 hours/week (4-week average)

After swap (taking additional FMIT week):
- Dr. Smith: 82 hours/week (4-week average)  ❌ VIOLATION
```

### Root Cause

- **Inadequate pre-check:** Validation didn't calculate rolling 4-week average
- **Complex calculation:** FMIT weeks are ~60 hours, but overlap with other duties
- **Hidden hours:** Moonlighting, admin time, clinic hours not counted
- **Stale data:** Work hour calculation based on outdated schedule

### Detection Method

```python
from app.services.work_hour_calculator import WorkHourCalculator

def detect_work_hour_creep(swap_request: StructuredSwapRequest) -> bool:
    """
    Check if swap would cause 80-hour violation.

    Returns:
        True if violation would occur, False otherwise
    """
    calculator = WorkHourCalculator(db)

    # Calculate 4-week rolling average AFTER swap
    target_hours_after = calculator.get_4week_average_after_swap(
        person_id=swap_request.target_faculty.id,
        week_ending=swap_request.source_week,
        swap_delta=FMIT_WEEK_HOURS  # ~60 hours
    )

    MAX_HOURS = 80.0

    if target_hours_after > MAX_HOURS:
        logger.warning(
            f"Work hour creep detected: {swap_request.target_faculty.name} "
            f"would be at {target_hours_after:.1f}/80 hours after swap"
        )
        return True

    return False
```

**Alert Threshold:**
- `> 75 hours` → Warning (approaching limit)
- `> 80 hours` → Error (violation)

### Mitigation

**Prevention:**
1. Always calculate **rolling 4-week average**, not just current week
2. Include **all duty hours** (clinic, call, admin, procedures)
3. Check **both parties** (source and target)
4. Warn at 75 hours (5-hour buffer)

**Remediation:**
```python
if target_hours_after > 75:
    # Suggest alternative weeks with lower utilization
    alternative_weeks = find_low_utilization_weeks(
        faculty_id=swap_request.target_faculty.id,
        max_hours_after_swap=75.0,
        count=3
    )

    return {
        "error": "APPROACHING_80_HOUR_LIMIT",
        "message": f"{swap_request.target_faculty.name} would be at "
                   f"{target_hours_after:.1f}/80 hours. Consider these weeks instead:",
        "alternatives": alternative_weeks
    }
```

---

## 2. Continuity Breaks

### Symptom

Patient care continuity disrupted due to unexpected faculty changes.

```
Example:
- Week 1: Dr. A on FMIT (knows patient panel)
- Week 2: Dr. B swaps in (unfamiliar with patients)
- Handoff quality degrades, patient safety risk
```

### Root Cause

- **No handoff time:** Swap executed with <24 hours notice
- **Complex patients:** High-acuity panel requires familiarity
- **Weekend transitions:** Friday swap means Monday handoff
- **Documentation gaps:** Previous faculty didn't document well

### Detection Method

```python
from datetime import date, timedelta

def detect_continuity_break(swap_request: StructuredSwapRequest) -> dict:
    """
    Check if swap disrupts patient care continuity.

    Returns:
        dict with risk level and recommendations
    """
    today = date.today()
    days_until_swap = (swap_request.source_week - today).days

    # Risk factors
    risk_score = 0
    warnings = []

    # 1. Short notice (<7 days)
    if days_until_swap < 7:
        risk_score += 2
        warnings.append(f"Only {days_until_swap} days notice for handoff")

    # 2. High patient acuity week
    if is_high_acuity_week(swap_request.source_week):
        risk_score += 3
        warnings.append("High-acuity patient panel week")

    # 3. Weekend transition
    if swap_request.source_week.weekday() == 0:  # Monday
        risk_score += 1
        warnings.append("Weekend transition - limited handoff time")

    # 4. Target faculty unfamiliar with rotation
    if not has_recent_fmit_experience(swap_request.target_faculty.id):
        risk_score += 2
        warnings.append("Target faculty hasn't done FMIT in >6 months")

    return {
        "risk_level": "HIGH" if risk_score >= 5 else "MEDIUM" if risk_score >= 3 else "LOW",
        "risk_score": risk_score,
        "warnings": warnings
    }
```

**Risk Levels:**
- `LOW (0-2)` → Auto-approve
- `MEDIUM (3-4)` → Require handoff plan
- `HIGH (5+)` → Escalate to Program Director

### Mitigation

**Prevention:**
1. Enforce **minimum 7-day notice** for FMIT swaps
2. Require **handoff documentation** for all swaps
3. Check **target faculty FMIT experience** (last rotation within 6 months)
4. Block swaps during **high-acuity weeks** (identified by coordinator)

**Remediation:**
```python
if continuity_risk["risk_level"] == "HIGH":
    return {
        "decision": "FLAG",
        "message": "High continuity risk. Require Program Director approval.",
        "required_actions": [
            "Submit detailed handoff plan (patient list, active issues)",
            "Schedule in-person handoff meeting",
            "Identify backup faculty for urgent questions",
            "Document high-risk patients"
        ]
    }
```

---

## 3. Coverage Gaps

### Symptom

Swap creates insufficient staffing for rotation or shift.

```
Example:
- Monday AM Inpatient: Requires 2 faculty minimum
- Dr. A swaps out, only Dr. B remains
- Coverage gap: 1 faculty (need 2) ❌
```

### Root Cause

- **No backup check:** Validation didn't verify minimum coverage
- **Absorb swaps:** Source gives away shift, no replacement
- **Cascading swaps:** Multiple swaps same week compound shortages
- **Absence conflicts:** Other faculty on leave same week

### Detection Method

```python
from app.services.coverage_validator import CoverageValidator

def detect_coverage_gap(swap_request: StructuredSwapRequest) -> bool:
    """
    Check if swap creates understaffing.

    Returns:
        True if coverage gap would occur, False otherwise
    """
    validator = CoverageValidator(db)

    # Get coverage levels after swap
    coverage = validator.get_week_coverage_after_swap(
        week=swap_request.source_week,
        rotation="FMIT",
        remove_faculty=swap_request.source_faculty.id,
        add_faculty=swap_request.target_faculty.id if swap_request.swap_type == SwapType.ONE_TO_ONE else None
    )

    MINIMUM_FMIT_COVERAGE = 1  # At least 1 faculty must cover FMIT

    if coverage.faculty_count < MINIMUM_FMIT_COVERAGE:
        logger.warning(
            f"Coverage gap detected: Week {swap_request.source_week} would have "
            f"{coverage.faculty_count} faculty (minimum: {MINIMUM_FMIT_COVERAGE})"
        )
        return True

    return False
```

**Coverage Requirements:**
| Rotation | Minimum Faculty | Minimum Residents |
|----------|----------------|-------------------|
| FMIT | 1 | N/A (faculty-only) |
| Inpatient AM/PM | 2 | 4 (2:1 supervision) |
| Procedures | 1 | 2 |
| Clinic | 1 per 4 residents | Variable |

### Mitigation

**Prevention:**
1. **Check minimum coverage** before approving swap
2. **Block absorb swaps** if coverage would drop below minimum
3. **Suggest replacement** if coverage gap detected
4. **Lock critical weeks** (holidays, high-census weeks)

**Remediation:**
```python
if coverage_gap_detected:
    # Find replacement candidates
    replacements = find_available_faculty(
        week=swap_request.source_week,
        rotation="FMIT",
        exclude=[swap_request.source_faculty.id]
    )

    if replacements:
        return {
            "decision": "FLAG",
            "message": f"Coverage gap: {swap_request.source_faculty.name} is "
                       f"only faculty covering FMIT week {swap_request.source_week}.",
            "required_action": "Find replacement before approving absorb swap",
            "suggested_replacements": [r.name for r in replacements]
        }
    else:
        return {
            "decision": "REJECT",
            "message": "Cannot approve: No available replacement faculty for "
                       f"week {swap_request.source_week}. Coverage gap would occur."
        }
```

---

## 4. Moonlighting Conflicts

### Symptom

Faculty member has external (moonlighting) commitments that conflict with swapped week.

```
Example:
- Dr. C has moonlighting shift at civilian hospital Friday night
- Accepts swap into FMIT week with Friday call
- Double-booked: military FMIT + civilian moonlighting ❌
```

### Root Cause

- **External data not integrated:** Moonlighting schedule stored separately
- **Self-reporting gaps:** Faculty forgets to report moonlighting
- **Approval delays:** Moonlighting approved after swap executed
- **ACGME hour limits:** Moonlighting hours count toward 80-hour limit

### Detection Method

```python
from app.models.moonlighting import MoonlightingAssignment

def detect_moonlighting_conflict(swap_request: StructuredSwapRequest) -> dict | None:
    """
    Check if swap conflicts with moonlighting commitments.

    Returns:
        Conflict details if found, None otherwise
    """
    week_end = swap_request.source_week + timedelta(days=6)

    # Query moonlighting assignments for target faculty
    conflicts = db.query(MoonlightingAssignment).filter(
        MoonlightingAssignment.person_id == swap_request.target_faculty.id,
        MoonlightingAssignment.start_date <= week_end,
        MoonlightingAssignment.end_date >= swap_request.source_week,
        MoonlightingAssignment.status == "approved"
    ).all()

    if conflicts:
        conflict_dates = [c.start_date.isoformat() for c in conflicts]
        total_moonlighting_hours = sum(c.hours for c in conflicts)

        return {
            "has_conflict": True,
            "conflict_dates": conflict_dates,
            "moonlighting_hours": total_moonlighting_hours,
            "message": f"{swap_request.target_faculty.name} has {len(conflicts)} "
                       f"moonlighting assignment(s) during week {swap_request.source_week}"
        }

    return None
```

**ACGME Rule:** Moonlighting hours count toward 80-hour limit

### Mitigation

**Prevention:**
1. **Integrate moonlighting database** with swap validation
2. **Require disclosure** of moonlighting when accepting swaps
3. **Auto-check conflicts** during safety validation
4. **Include moonlighting hours** in 80-hour calculation

**Remediation:**
```python
if moonlighting_conflict:
    # Calculate total hours (military duty + moonlighting)
    military_hours = FMIT_WEEK_HOURS  # ~60 hours
    moonlighting_hours = moonlighting_conflict["moonlighting_hours"]
    total_hours = military_hours + moonlighting_hours

    if total_hours > 80:
        return {
            "decision": "REJECT",
            "error": "MOONLIGHTING_CONFLICT",
            "message": f"ACGME violation: {swap_request.target_faculty.name} would "
                       f"work {total_hours} hours (military {military_hours} + "
                       f"moonlighting {moonlighting_hours}). Exceeds 80-hour limit."
        }
    else:
        return {
            "decision": "FLAG",
            "message": f"Moonlighting conflict detected but within 80-hour limit "
                       f"({total_hours} hours total). Require faculty confirmation.",
            "required_action": "Faculty must confirm they can manage both commitments"
        }
```

---

## 5. Fairness Violations

### Symptom

Swap creates **inequitable workload distribution**, favoring some faculty over others.

```
Example Q1 2025 Swap Activity:
- Dr. A: Given away 4 FMIT weeks, taken 0 (net -4)
- Dr. B: Given away 1 week, taken 3 (net +2)
- Dr. C: Given away 0 weeks, taken 0 (net 0)

Result: Dr. A has lighter load, Dr. B heavier, unfair ❌
```

### Root Cause

- **No equity tracking:** System doesn't monitor cumulative swap balance
- **Senior privilege:** Senior faculty more likely to get swap requests approved
- **Informal agreements:** "Swap circles" among friends exclude others
- **Reason bias:** Some reasons (conference) more acceptable than others (preference)

### Detection Method

```python
from app.services.swap_equity_tracker import SwapEquityTracker

def detect_fairness_violation(swap_request: StructuredSwapRequest) -> dict:
    """
    Check if swap would create inequitable workload distribution.

    Returns:
        Equity analysis with violation flag
    """
    tracker = SwapEquityTracker(db)

    # Calculate net swap balance for each faculty (last 3 months)
    source_balance = tracker.get_swap_balance(
        person_id=swap_request.source_faculty.id,
        period_months=3
    )
    target_balance = tracker.get_swap_balance(
        person_id=swap_request.target_faculty.id,
        period_months=3
    )

    # Calculate balance after this swap
    source_balance_after = source_balance - 1  # Giving away
    target_balance_after = target_balance + 1  # Taking on

    # Calculate faculty-wide statistics
    all_balances = tracker.get_all_balances(period_months=3)
    mean_balance = sum(all_balances) / len(all_balances)
    std_dev = calculate_std_dev(all_balances)

    # Fairness thresholds
    WARN_THRESHOLD = mean_balance + (1.5 * std_dev)  # 1.5 std dev
    VIOLATION_THRESHOLD = mean_balance + (2.0 * std_dev)  # 2 std dev

    if target_balance_after > VIOLATION_THRESHOLD:
        return {
            "violation": True,
            "severity": "error",
            "message": f"{swap_request.target_faculty.name} would have swap balance "
                       f"of {target_balance_after} ({target_balance_after - mean_balance:.1f} "
                       f"above average). Unfair workload distribution."
        }
    elif target_balance_after > WARN_THRESHOLD:
        return {
            "violation": False,
            "severity": "warning",
            "message": f"{swap_request.target_faculty.name} would be {target_balance_after - mean_balance:.1f} "
                       f"swaps above average. Monitor for equity."
        }

    return {
        "violation": False,
        "severity": "info",
        "message": "Swap balance within normal range"
    }
```

**Equity Metrics:**
- **Net balance:** `(weeks_taken - weeks_given)`
- **Healthy range:** Within ±2 from mean per quarter
- **Warning threshold:** >1.5 standard deviations from mean
- **Violation threshold:** >2 standard deviations from mean

### Mitigation

**Prevention:**
1. **Track swap equity** for all faculty (quarterly reports)
2. **Flag imbalanced swaps** during validation
3. **Require justification** if balance exceeds threshold
4. **Rotate opportunities** for high-demand weeks

**Remediation:**
```python
if fairness_analysis["violation"]:
    # Check if there are less-utilized faculty who could take the week
    balanced_alternatives = find_faculty_below_average_balance(
        week=swap_request.source_week,
        count=3
    )

    return {
        "decision": "FLAG",
        "message": fairness_analysis["message"],
        "required_action": "Coordinator approval required for equity override",
        "alternatives": [
            {
                "faculty": alt.name,
                "current_balance": alt.balance,
                "rationale": f"{alt.balance} swaps below {target_balance_after} "
                             f"(more equitable distribution)"
            }
            for alt in balanced_alternatives
        ]
    }
```

---

## Failure Mode Summary Table

| Failure Mode | Detection Rate | Impact | Mitigation Priority |
|--------------|----------------|--------|-------------------|
| Work Hour Creep | 95% (automated) | CRITICAL (ACGME violation) | HIGH |
| Continuity Breaks | 60% (partially automated) | HIGH (patient safety) | HIGH |
| Coverage Gaps | 90% (automated) | CRITICAL (mission failure) | HIGH |
| Moonlighting Conflicts | 40% (requires integration) | HIGH (ACGME violation) | MEDIUM |
| Fairness Violations | 80% (requires tracking) | MEDIUM (morale) | MEDIUM |

---

## Detection Automation

All failure modes should have **automated checks** in the safety validation pipeline:

```python
def comprehensive_failure_detection(swap_request: StructuredSwapRequest) -> list[dict]:
    """
    Run all failure mode detectors.

    Returns:
        List of detected issues (empty if all pass)
    """
    issues = []

    # 1. Work hour creep
    if detect_work_hour_creep(swap_request):
        issues.append({
            "mode": "WORK_HOUR_CREEP",
            "severity": "error",
            "message": "80-hour violation would occur"
        })

    # 2. Continuity breaks
    continuity_risk = detect_continuity_break(swap_request)
    if continuity_risk["risk_level"] != "LOW":
        issues.append({
            "mode": "CONTINUITY_BREAK",
            "severity": "warning" if continuity_risk["risk_level"] == "MEDIUM" else "error",
            "message": f"Continuity risk: {continuity_risk['risk_level']}"
        })

    # 3. Coverage gaps
    if detect_coverage_gap(swap_request):
        issues.append({
            "mode": "COVERAGE_GAP",
            "severity": "error",
            "message": "Insufficient coverage would result"
        })

    # 4. Moonlighting conflicts
    moonlighting = detect_moonlighting_conflict(swap_request)
    if moonlighting and moonlighting["has_conflict"]:
        issues.append({
            "mode": "MOONLIGHTING_CONFLICT",
            "severity": "warning",
            "message": moonlighting["message"]
        })

    # 5. Fairness violations
    fairness = detect_fairness_violation(swap_request)
    if fairness["violation"]:
        issues.append({
            "mode": "FAIRNESS_VIOLATION",
            "severity": fairness["severity"],
            "message": fairness["message"]
        })

    return issues
```

---

## Monitoring and Alerting

Track failure mode occurrences for continuous improvement:

```python
# Prometheus metrics
swap_failure_counter = Counter(
    'swap_failures_total',
    'Total swap failures by failure mode',
    ['failure_mode', 'severity']
)

# Log each detection
for issue in detected_issues:
    swap_failure_counter.labels(
        failure_mode=issue["mode"],
        severity=issue["severity"]
    ).inc()
```

**Dashboard alerts:**
- Work hour creep detections >5/month → Review validation logic
- Continuity breaks >10/month → Enforce minimum notice period
- Coverage gaps >2/month → Improve backup coverage planning
- Fairness violations >3/quarter → Coordinator intervention needed
