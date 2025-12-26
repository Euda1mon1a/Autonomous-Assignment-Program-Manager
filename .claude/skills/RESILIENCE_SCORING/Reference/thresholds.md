# Reference: Alert Thresholds

## Overview

This document defines the thresholds for escalating resilience issues. When metrics cross these thresholds, specific actions should be triggered.

---

## Health Score Thresholds

### Overall Health Score

| Threshold | Status | Alert Level | Action Required | Notification |
|-----------|--------|-------------|-----------------|--------------|
| ≥ 0.85 | EXCELLENT | None | Monitor quarterly | None |
| 0.70-0.84 | GOOD | Info | Monitor monthly | Program Coordinator |
| 0.50-0.69 | FAIR | Warning | Monitor weekly, mitigate | Chief Resident + PD |
| 0.30-0.49 | POOR | Alert | Daily monitoring, urgent mitigation | PD + APD + Admin |
| < 0.30 | CRITICAL | Emergency | Immediate intervention | All stakeholders + Hospital Admin |

**Escalation Example:**
```
Health = 0.68 (FAIR)
→ Send weekly email to Chief Resident and Program Director
→ Schedule resilience review meeting within 7 days
→ Run N-1 analysis to identify vulnerabilities
```

---

## Component Thresholds

### Coverage Component

| Coverage | Status | Action |
|----------|--------|--------|
| ≥ 0.80 | Excellent | No action |
| 0.67-0.79 | Acceptable | Monitor |
| 0.50-0.66 | Understaffed | Add supplemental staff or reduce rotation requirements |
| < 0.50 | Critical | Emergency staffing intervention |

**Alert Trigger:**
```
if coverage < 0.67:
  alert(
    level="WARNING",
    message="Rotation coverage below target",
    action="Review rotation minimum staffing requirements"
  )
```

### Margin Component

| Margin | Work Hours/Week (avg) | Status | Action |
|--------|----------------------|--------|--------|
| ≥ 0.50 | ≤ 40 hours | Excellent | No action |
| 0.30-0.49 | 40-56 hours | Acceptable | Monitor |
| 0.15-0.29 | 56-68 hours | High utilization | Reduce workload |
| < 0.15 | > 68 hours | Critical | Immediate workload reduction, ACGME risk |

**Alert Trigger:**
```
if margin < 0.30:
  alert(
    level="WARNING",
    message="Residents approaching work hour limits",
    action="Reduce call frequency or add coverage"
  )
```

### Continuity Component

| Continuity | Mid-Block Switches | Status | Action |
|------------|-------------------|--------|--------|
| ≥ 0.85 | ≤ 15% blocks | Excellent | No action |
| 0.70-0.84 | 15-30% blocks | Acceptable | Monitor |
| 0.50-0.69 | 30-50% blocks | Disruptive | Stabilize rotations |
| < 0.50 | > 50% blocks | Chaotic | Redesign schedule |

**Alert Trigger:**
```
if continuity < 0.70:
  alert(
    level="INFO",
    message="Continuity below target (excessive rotation switches)",
    action="Review rotation block structure"
  )
```

---

## N-1 Analysis Thresholds

### Critical Resident Count

| Critical Resident Count | Risk Level | Action |
|------------------------|------------|--------|
| 0 | Low | No single points of failure, monitor quarterly |
| 1-2 | Moderate | Document backup plans, cross-train 1-2 residents |
| 3-5 | High | Urgent cross-training program, add supplemental staff |
| > 5 | Critical | Schedule redesign required, too many single points of failure |

**Alert Trigger:**
```
if critical_resident_count > 2:
  alert(
    level="ALERT",
    message=f"{critical_resident_count} single points of failure detected",
    action="Implement cross-training program or add supplemental staff"
  )
```

### High-Impact Resident Count

| High-Impact Count | Action |
|------------------|--------|
| 0-3 | Acceptable |
| 4-6 | Review workload distribution |
| > 6 | Schedule too tightly coupled, increase slack |

### Understaffing Hours (per 7-day absence)

| Understaffing Hours | Severity | Action |
|--------------------|----------|--------|
| 0 | None | Fully absorbed |
| 1-40 | Minor | Internal redistribution sufficient |
| 41-80 | Moderate | May require supplemental staff |
| 81-168 | Major | Definitely requires supplemental staff or schedule redesign |
| > 168 | Critical | Rotation non-functional without this resident |

**Alert Trigger:**
```
if understaffing_hours > 80:
  alert(
    level="ALERT",
    message=f"Resident absence would cause {understaffing_hours} hours understaffing",
    action="Pre-arrange supplemental staff or cross-train backups"
  )
```

---

## Multi-Failure Thresholds

### Collapse Probability

| Collapse Probability | Risk Level | Action |
|---------------------|------------|--------|
| < 5% | Low | Acceptable, deploy schedule |
| 5-10% | Moderate | Deploy with enhanced monitoring |
| 10-20% | High | Mitigation required before deployment |
| > 20% | Critical | DO NOT DEPLOY - redesign schedule |

**Alert Trigger:**
```
if collapse_probability > 0.10:
  alert(
    level="CRITICAL",
    message=f"Collapse probability {collapse_probability:.1%} exceeds 10% threshold",
    action="DO NOT DEPLOY - Add staffing or reduce rotation requirements"
  )
```

### Median Time-to-Failure

| Median TTF | Risk Level | Action |
|------------|------------|--------|
| > 7 days | Robust | Can withstand 1-week multi-absence |
| 3-7 days | Moderate | Enhanced monitoring during high-risk periods |
| 1-3 days | Fragile | Pre-position supplemental staff |
| < 1 day | Critical | Immediate failure likely, do not deploy |

**Alert Trigger:**
```
if median_time_to_failure < 3:
  alert(
    level="ALERT",
    message=f"Median time-to-failure {median_time_to_failure} days is critically short",
    action="Increase schedule margin or add supplemental staff"
  )
```

### Fragile Rotation Failure Rate

| Failure Rate | Severity | Action |
|--------------|----------|--------|
| < 10% | Low | Acceptable resilience |
| 10-25% | Medium | Monitor closely, consider increasing staffing |
| 25-50% | High | Significant vulnerability, mitigation recommended |
| > 50% | Critical | Single point of failure, must address |

**Alert Trigger:**
```
for rotation in fragile_rotations:
  if rotation.failure_rate > 0.50:
    alert(
      level="ALERT",
      message=f"Rotation {rotation.id} fails in {rotation.failure_rate:.1%} of multi-failure scenarios",
      action=f"Increase minimum staffing for {rotation.id} or add backup residents"
    )
```

---

## Recovery Planning Thresholds

### Recovery Time

| Recovery Time | Status | Action |
|---------------|--------|--------|
| < 24 hours | Fast | Internal redistribution possible |
| 24-48 hours | Moderate | May require supplemental staff (credentialing delay) |
| 48-72 hours | Slow | Definitely requires supplemental staff |
| > 72 hours | Critical | Unacceptable delay, pre-position supplemental staff |

**Alert Trigger:**
```
if estimated_recovery_time > 48:
  alert(
    level="WARNING",
    message=f"Recovery time {estimated_recovery_time} hours exceeds 48-hour threshold",
    action="Pre-credential supplemental staff to reduce recovery time"
  )
```

### Bottleneck Detection

**Credentialing Delay:**
```
if supplemental_staff_required and credentialing_time > 24:
  alert(
    level="INFO",
    message="Supplemental staff delayed by credentialing (24+ hours)",
    action="Maintain pre-credentialed pool of supplemental staff"
  )
```

**Work Hour Constraint:**
```
if internal_redistribution_blocked_by_acgme:
  alert(
    level="WARNING",
    message="Cannot redistribute internally without ACGME violations",
    action="Reduce baseline utilization to 60-70 hours/week max"
  )
```

**Lack of Cross-Training:**
```
if no_cross_trained_residents_available:
  alert(
    level="INFO",
    message="No residents cross-trained for affected rotations",
    action="Implement cross-training program for high-risk rotations"
  )
```

---

## Historical Trend Thresholds

### Health Score Degradation Rate

| 30-Day Trend | Status | Action |
|--------------|--------|--------|
| > 0 | Improving | No action |
| -0.01 to 0 | Stable | Monitor |
| -0.01 to -0.05 | Gradual decline | Investigate cause, mitigate |
| < -0.05 | Rapid decline | Urgent investigation, immediate mitigation |

**Alert Trigger:**
```
health_trend_30day = (health_today - health_30days_ago) / 30

if health_trend_30day < -0.05:
  alert(
    level="ALERT",
    message=f"Health score declining rapidly ({health_trend_30day:.3f} per day)",
    action="Investigate recent schedule changes or increased absences"
  )
```

### Incident Correlation

**Threshold:** If health score drops below 0.70 within 7 days of a schedule change, investigate correlation.

```
if health_dropped_below_threshold and recent_schedule_change:
  alert(
    level="WARNING",
    message="Health score drop correlated with recent schedule change",
    action="Review schedule change for unintended consequences"
  )
```

---

## Seasonal Thresholds

### Deployment Season (Jun-Aug)

**Adjusted Thresholds:**
- Health Score: Lower acceptable threshold to 0.65 (instead of 0.70)
- Critical Resident Count: Lower acceptable threshold to 1 (instead of 2)

**Rationale:** Deployment season inherently reduces resilience due to TDY/deployment absences.

### Flu Season (Nov-Feb)

**Adjusted Thresholds:**
- Collapse Probability: Lower acceptable threshold to 7.5% (instead of 10%)
- Median TTF: Increase warning threshold to 5 days (instead of 3 days)

**Rationale:** Flu season increases likelihood of multi-failure scenarios.

---

## Alert Notification Matrix

| Alert Level | Metric Threshold Crossed | Notification Recipients | Response Time |
|-------------|-------------------------|------------------------|---------------|
| **INFO** | Continuity < 0.70 | Program Coordinator | 7 days |
| **WARNING** | Coverage < 0.67<br>Margin < 0.30<br>Recovery Time > 48h | Chief Resident + Program Director | 3 days |
| **ALERT** | Health < 0.50<br>Critical Count > 2<br>Collapse Prob > 10%<br>Median TTF < 3 days | PD + APD + Chief Resident | 24 hours |
| **CRITICAL** | Health < 0.30<br>Collapse Prob > 20%<br>Understaffing > 168h | All stakeholders + Hospital Admin | Immediate |
| **EMERGENCY** | Active schedule collapse (real-time) | All stakeholders + Emergency Operations | Immediate |

---

## Auto-Mitigation Thresholds

Some thresholds should trigger **automatic** mitigation actions (not just alerts):

### Automatic Schedule Hold

```
if collapse_probability > 0.20:
  # DO NOT DEPLOY - automatically mark schedule as "needs_revision"
  schedule.status = "needs_revision"
  schedule.deployment_blocked = True
  schedule.block_reason = f"Collapse probability {collapse_probability:.1%} exceeds 20%"
```

### Automatic Supplemental Staff Request

```
if critical_resident_count > 5:
  # Automatically generate supplemental staff request
  create_supplemental_staff_request(
    reason=f"{critical_resident_count} single points of failure detected",
    urgency="HIGH",
    duration_weeks=4
  )
```

### Automatic Cross-Training Recommendation

```
for rotation in fragile_rotations:
  if rotation.failure_rate > 0.50:
    # Automatically create cross-training task
    create_cross_training_task(
      rotation=rotation.id,
      reason=f"Rotation fails in {rotation.failure_rate:.1%} of multi-failure scenarios",
      priority="HIGH"
    )
```

---

## Threshold Calibration

Thresholds should be reviewed and adjusted based on historical data:

### Quarterly Review

- Compare actual incidents to predicted collapse probability
- Adjust thresholds if false positive rate > 20% or false negative rate > 5%

### Annual Review

- Reassess threshold weights based on:
  - Actual ACGME violations (if margin threshold is too lenient)
  - Actual coverage failures (if coverage threshold is too lenient)
  - Resident feedback on continuity disruption

### Calibration Example

```
# Historical Data (past 12 months):
# - Schedules with collapse_prob > 10%: 8 deployed
# - Actual collapses: 1 (12.5% actual collapse rate)
# - Threshold appears well-calibrated

# vs

# Historical Data (past 12 months):
# - Schedules with margin < 0.30: 12 deployed
# - Actual ACGME violations: 5 (41.7% violation rate)
# - Threshold too lenient → increase to margin < 0.35
```

---

## Testing Threshold Effectiveness

### Sensitivity Analysis

**Question:** Does lowering threshold reduce incident rate?

```
Test: Lower coverage threshold from 0.67 → 0.70
Expected: Fewer coverage failures in deployed schedules
Metric: Actual coverage failure rate should drop by 10-20%
```

### Specificity Analysis

**Question:** Does threshold generate too many false alarms?

```
Test: Track alerts where no actual incident occurred
Acceptable: False positive rate < 20%
If higher: Threshold too conservative, adjust upward
```

---

## Summary Checklist

Before deploying a schedule, verify it passes ALL critical thresholds:

- ✅ Health Score ≥ 0.70 (or 0.65 during deployment season)
- ✅ Coverage ≥ 0.67 (all rotations at minimum or above)
- ✅ Margin ≥ 0.30 (residents not approaching work hour limits)
- ✅ Critical Resident Count ≤ 2 (no more than 2 single points of failure)
- ✅ Collapse Probability < 10% (robust under multi-failure)
- ✅ Median TTF ≥ 3 days (can withstand 3 days of multi-absence)
- ✅ No fragile rotations with failure rate > 50% (no critical single points of failure)

**If any threshold is crossed:**
1. Run full resilience analysis (N-1 + multi-failure + recovery)
2. Document specific vulnerabilities
3. Implement mitigations (cross-training, supplemental staff, schedule adjustment)
4. Re-run analysis to verify improvement
5. Only deploy after all critical thresholds pass

---

*This reference document provides the decision rules for escalating resilience issues and triggering mitigation actions.*
