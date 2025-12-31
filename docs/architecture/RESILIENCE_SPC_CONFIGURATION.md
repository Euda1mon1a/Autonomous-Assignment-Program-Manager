# Statistical Process Control (SPC) Configuration Guide

**Status:** Operational Configuration Reference
**Date:** 2025-12-31
**Purpose:** SPC monitoring configuration, thresholds, and alert rules
**Audience:** System Administrators, Database Administrators, Monitoring Teams

---

## Table of Contents

1. [SPC System Overview](#spc-system-overview)
2. [Control Limit Configuration](#control-limit-configuration)
3. [Alert Configuration](#alert-configuration)
4. [Integration Points](#integration-points)
5. [Monitoring Rules](#monitoring-rules)
6. [Dashboard Configuration](#dashboard-configuration)
7. [Alert Response SLAs](#alert-response-slas)

---

## SPC System Overview

### What is SPC?

Statistical Process Control monitors weekly work hours against **Western Electric Rules** to detect:
- **Rule 1:** Extreme values (out of statistical control)
- **Rule 2:** Sustained shifts in workload baseline
- **Rule 3:** Gradual trends
- **Rule 4:** Permanent baseline changes

### System Components

**Data Input:** Weekly work hour totals per resident (collected every Monday 0100 UTC)

**Processing:** Run SPC algorithm (Python, `spc_monitoring.py`)

**Output:** Alerts classified by severity (CRITICAL, WARNING, INFO)

**Action:** Route alerts to appropriate personnel for response

### Frequency

- **Calculation:** Weekly (every Monday)
- **Alert Generation:** Immediate on violation detection
- **Dashboard Update:** Real-time (< 5 minutes after calculation)
- **Notification:** Immediate for CRITICAL, within 2 hours for WARNING

---

## Control Limit Configuration

### Default Parameters

```python
# Target workload: 60 hours per week
TARGET_HOURS = 60.0

# Process standard deviation: 5 hours per week
SIGMA = 5.0

# Calculated control limits:
UCL_3_SIGMA = 75.0   # Upper Control Limit (CRITICAL)
UCL_2_SIGMA = 70.0   # Upper Warning Limit (WARNING)
UCL_1_SIGMA = 65.0   # Upper Zone boundary
CENTERLINE = 60.0    # Target
LCL_1_SIGMA = 55.0   # Lower Zone boundary
LCL_2_SIGMA = 50.0   # Lower Warning Limit
LCL_3_SIGMA = 45.0   # Lower Control Limit (CRITICAL)
```

### Rationale for Parameters

**TARGET_HOURS = 60:**
- ACGME allows 80 hours/week maximum
- Safe operating point leaves 20-hour buffer
- Allows for rotation variation (some weeks 55-65h normal)

**SIGMA = 5:**
- Empirically observed process variation
- Accounts for rotation schedules, call patterns, leave
- 3σ limit (75h) is 5h below ACGME maximum (regulatory buffer)

### Customization by Program

**Military Medical Programs (High-Stress):**

```python
MILITARY_ADJUSTMENTS = {
    "target_hours": 70.0,       # Higher baseline due to TDY/deployment
    "sigma": 6.0,               # Greater variation expected
    "ucl_3_sigma": 88.0,        # Higher limits, but still <ACGME 80h
    "lcl_3_sigma": 52.0,
}
```

**Civilian Academic Programs (Lower-Stress):**

```python
CIVILIAN_ADJUSTMENTS = {
    "target_hours": 58.0,
    "sigma": 4.5,
    "ucl_3_sigma": 71.5,
    "lcl_3_sigma": 44.5,
}
```

**Specialty-Specific (if applicable):**

| Specialty | Target Hours | Sigma | UCL 3σ |
|-----------|------------|-------|--------|
| Emergency Medicine | 65 | 5.5 | 81.5 |
| Surgery | 75 | 6.0 | 93.0 (capped at 90) |
| Pediatrics | 55 | 4.5 | 68.5 |
| Psychiatry | 50 | 3.5 | 60.5 |

### Configuration File

```yaml
# backend/config/spc_config.yaml

spc_monitoring:
  enabled: true

  global_defaults:
    target_hours: 60.0
    sigma: 5.0

  programs:
    program_001_military:
      target_hours: 70.0
      sigma: 6.0
      ucl_3_sigma: 88.0
      lcl_3_sigma: 52.0

    program_002_civilian:
      target_hours: 58.0
      sigma: 4.5
      ucl_3_sigma: 71.5
      lcl_3_sigma: 44.5

  specialties:
    emergency_medicine:
      target_hours: 65.0
      sigma: 5.5
    surgery:
      target_hours: 75.0
      sigma: 6.0
      ucl_3_sigma_cap: 90.0  # Don't exceed ACGME limit
    psychiatry:
      target_hours: 50.0
      sigma: 3.5
```

---

## Alert Configuration

### Rule 1: One Point Beyond 3σ (CRITICAL)

**Trigger:** Any single week with hours > UCL_3σ OR < LCL_3σ

**Default Threshold:**
```python
UCL_CRITICAL = 75.0  # hours/week
LCL_CRITICAL = 45.0  # hours/week

Alert Fired If:
  weekly_hours > 75.0 OR weekly_hours < 45.0
```

**Severity:** CRITICAL
**Response Time:** Within 24 hours
**Notification:** Immediate (phone call + email + SMS)

**Alert Message Template:**

```
CRITICAL SPC VIOLATION - RULE 1

Resident: {name} ({resident_id})
Week Of: {date_range}
Actual Hours: {hours} (limit: {threshold})
Violation Type: {'OVERWORK' if hours > threshold else 'UNDERUTILIZATION'}

Process Status: OUT OF STATISTICAL CONTROL

This is a rare event (≤0.27% of normal process).
When it occurs, it indicates:
- Possible data entry error
- Unusual clinical event
- ACGME violation risk (if overwork)

REQUIRED ACTIONS:
1. Verify data accuracy (within 1 hour)
2. Investigate root cause (within 4 hours)
3. Implement intervention (within 24 hours)
4. Follow up (daily for 1 week)

Contact: {program_director} {phone} {email}
```

### Rule 2: 2 of 3 Beyond 2σ (WARNING)

**Trigger:** In any 3-week window, 2+ weeks with hours > UCL_2σ OR < LCL_2σ (same side)

**Default Threshold:**
```python
UCL_WARNING = 70.0  # hours/week
LCL_WARNING = 50.0  # hours/week

Alert Fired If:
  In window of 3 weeks:
    count(hours > 70) >= 2 OR count(hours < 50) >= 2
```

**Severity:** WARNING
**Response Time:** Within 48 hours
**Notification:** Email + dashboard alert (no SMS unless military/critical program)

**Alert Message Template:**

```
WARNING SPC VIOLATION - RULE 2

Resident: {name}
Time Period: {week1} to {week3}
Hours: {[week1_hours, week2_hours, week3_hours]}
Threshold: {threshold}

PATTERN DETECTED: Process Shift

Interpretation: Sustained elevation or depression in workload baseline.
Indicates systematic change (rotation change, staffing issue, seasonal increase).

RECOMMENDED ACTIONS:
1. Schedule review with resident (within 48 hours)
2. Analyze cause:
   - Rotation change?
   - New responsibilities?
   - Staffing shortage?
   - Seasonal workload increase?
3. If sustained: Plan workload adjustment
4. Monitor weekly hours going forward

This pattern is expected ~2.3% of the time with normal process.
Doesn't indicate immediate danger, but requires investigation.

Contact: {chief_resident} {phone}
```

### Rule 3: 4 of 5 Beyond 1σ (WARNING)

**Trigger:** In any 5-week window, 4+ weeks with hours > UCL_1σ OR < LCL_1σ (same side)

**Default Threshold:**
```python
UCL_TREND = 65.0   # hours/week
LCL_TREND = 55.0   # hours/week

Alert Fired If:
  In window of 5 weeks:
    count(hours > 65) >= 4 OR count(hours < 55) >= 4
```

**Severity:** WARNING
**Response Time:** Within 1 week
**Notification:** Email + dashboard (standard priority)

**Alert Message Template:**

```
WARNING SPC VIOLATION - RULE 3

Resident: {name}
Time Period: {5_week_window}
Hours: {[w1, w2, w3, w4, w5]}
Threshold: {threshold}

PATTERN DETECTED: Gradual Trend

Interpretation: Systematic drift over 5 weeks.
Suggests gradual environmental change (rotation progression, accumulating
burnout, or increasing clinical demands).

ANALYSIS:
- Trend direction: {'INCREASING' if increasing else 'DECREASING'}
- Rate of change: {slope:.2f} hours/week
- Projection (4 weeks): {projected_hours:.1f} hours

RECOMMENDED ACTIONS:
1. Monitor trend (daily for next 2 weeks)
2. If increasing trend toward 75+ → escalate to RED
3. If stable or decreasing → routine monitoring
4. Check for external factors (rotation change, staffing)?
5. Plan proactive workload adjustment if needed

This pattern is expected ~4.7% of the time with normal process.
Early warning of potential escalation.

Contact: {program_director}
```

### Rule 4: 8 Consecutive Same Side (INFO)

**Trigger:** 8+ consecutive weeks all > CENTERLINE OR all < CENTERLINE

**Default Threshold:**
```python
CENTERLINE = 60.0

Alert Fired If:
  8+ consecutive weeks with hours > 60 (all above)
  OR 8+ consecutive weeks with hours < 60 (all below)
```

**Severity:** INFO
**Response Time:** Within 1 week (non-urgent)
**Notification:** Dashboard only (no email unless requested)

**Alert Message Template:**

```
INFO SPC OBSERVATION - RULE 4

Resident: {name}
Duration: {duration_weeks} weeks
Mean Hours: {mean_hours:.1f}
Direction: {'ABOVE' if mean > 60 else 'BELOW'} baseline

OBSERVATION: Sustained Baseline Shift

Interpretation: Process mean has permanently shifted.
May indicate:
- Appropriate PGY progression (junior → senior)
- New role/responsibilities
- Sustainable new workload pattern
- May be intentional program adjustment

ASSESSMENT NEEDED:
1. Is this shift expected/appropriate?
2. If YES → Update baseline, re-center control limits
3. If NO → Investigate why shift occurred
4. Is resident coping well with new baseline?

This is not inherently problematic; context matters.

Suggested Action: Schedule program director discussion about
workload expectations and resident satisfaction.

Contact: {program_director}
```

---

## Integration Points

### Data Source: Work Hour Collection

**Weekly Schedule:**
- **Day:** Monday 0100 UTC
- **Source:** Assignment database (blocks completed in previous week)
- **Validation:**
  - Hours must be 0-168 (hours in week)
  - Must have ≥1 assignment in week (no data = 0 hours recorded)
  - Outliers flagged for manual review

**Data Quality Checks:**

```python
def validate_weekly_hours(resident_id, week_ending_date, hours):
    """Validate hour data before SPC processing."""

    # Check bounds
    if not (0 <= hours <= 168):
        raise ValueError(f"Hours out of range: {hours}")

    # Check for duplicate entries
    existing = get_resident_hours(resident_id, week_ending_date)
    if existing and existing != hours:
        log_warning(f"Conflicting hours: {existing} vs {hours}")
        return False  # Reject update

    # Check for anomalies
    recent_avg = get_resident_average(resident_id, weeks=12)
    if abs(hours - recent_avg) > 3 * sigma:
        log_alert(f"Anomaly: {hours} vs avg {recent_avg:.1f}")

    return True  # Accept
```

### Output: Alert Generation

**Alert Storage:**

```sql
INSERT INTO spc_alerts (
  alert_id,
  resident_id,
  rule,
  severity,
  hours_value,
  threshold_value,
  message,
  timestamp,
  acknowledged,
  acknowledged_by,
  action_taken
) VALUES (...)
```

**Alert Routing:**

```python
def route_alert(alert):
    """Route alert to appropriate personnel."""

    if alert.severity == "CRITICAL":
        # Call program director immediately
        notify_phone(alert.program_director.phone)
        notify_email(alert.program_director.email)
        notify_sms([
            alert.program_director.phone,
            alert.chief_resident.phone
        ])

    elif alert.severity == "WARNING":
        # Email chief resident, dashboard alert
        notify_email(alert.chief_resident.email)
        notify_dashboard(alert)

    elif alert.severity == "INFO":
        # Dashboard only
        notify_dashboard(alert)

    # Always log
    log_alert(alert)
```

---

## Monitoring Rules

### Rule Precedence (if multiple triggered)

1. **Rule 1 (CRITICAL)** - Report immediately
2. **Rule 3 (Trend)** - If also escalating, report with trend
3. **Rule 2 (Shift)** - If Rule 3 explains it, consolidate
4. **Rule 4 (Baseline)** - Report as context

### Example Multi-Rule Scenario

```
Resident X hours over 12 weeks: [58, 62, 61, 65, 68, 72, 75, 79, 82, 78, 76, 74]

Analysis:
  ├─ Rule 1: Week 9 (82h) exceeds 75h → CRITICAL
  ├─ Rule 3: Weeks 4-8 trend upward (4 of 5 > 65h) → WARNING (trend)
  ├─ Rule 2: Not triggered (no 3-week sustained >70h pattern before surge)
  └─ Rule 4: Not triggered (not 8 consecutive same side)

COMBINED ALERT:
"CRITICAL: Rule 1 violation (82h, week 9).
Pattern: 5-week upward trend detected (Rule 3).
Interpretation: Gradual escalation culminating in critical overwork.
Action: Urgent investigation required (not just one-week anomaly)."
```

### Hysteresis for SPC Alerts

**Prevent Alert Spam:** Don't re-alert on same rule for same resident within 7 days

```python
def check_hysteresis(resident_id, rule, timestamp):
    """Prevent duplicate alerts within 7 days."""

    last_alert = get_last_alert(resident_id, rule)
    days_since = (timestamp - last_alert.timestamp).days

    if days_since < 7:
        log_info(f"Hysteresis: Suppressing duplicate {rule} alert")
        return False  # Don't send alert

    return True  # Send alert
```

---

## Dashboard Configuration

### Grafana Dashboard: SPC Monitoring

**Panels to Create:**

#### Panel 1: Alert Heatmap

```
Title: SPC Alert Distribution
Type: Heatmap
X-Axis: Resident ID
Y-Axis: Week (rolling 12 weeks)
Color: Alert severity
  ├─ Green: No alert
  ├─ Yellow: Rule 2 or 3 (WARNING)
  ├─ Orange: Rule 1 high zone (caution)
  └─ Red: Rule 1 violation (CRITICAL)
```

#### Panel 2: Current Alerts

```
Title: Active SPC Violations
Type: Table
Columns:
  ├─ Resident Name
  ├─ Rule
  ├─ Current Hours
  ├─ Threshold
  ├─ Status (↑ Improving, ↓ Worsening, → Stable)
  ├─ Days in Violation
  └─ Acknowledgement

Refresh: Real-time
Row Limit: 20 (show most critical)
Alert Rows: Highlighted in red
```

#### Panel 3: Process Capability Index (Cpk)

```
Title: ACGME Compliance Process Capability
Type: Gauge
Metric: Cpk (process capability index)
  ├─ Cpk < 1.0:  Red (not capable)
  ├─ Cpk 1.0-1.33: Yellow (marginally capable)
  ├─ Cpk 1.33-1.67: Green (capable)
  └─ Cpk ≥ 1.67: Dark green (highly capable)

Threshold: 1.33 (industry standard)
Program-Level: Aggregate across all residents
```

#### Panel 4: Rule Distribution

```
Title: SPC Violations by Rule (Last 30 Days)
Type: Pie Chart / Bar Chart
Metrics:
  ├─ Rule 1 (CRITICAL): Count
  ├─ Rule 2 (Shift): Count
  ├─ Rule 3 (Trend): Count
  └─ Rule 4 (Baseline): Count
```

#### Panel 5: Alert Response Metrics

```
Title: SPC Alert Response Performance
Type: Time Series
Metrics:
  ├─ Alerts Generated (daily count)
  ├─ Alerts Acknowledged (% within SLA)
  ├─ Average Response Time (hours)
  └─ Resolved % (within target timeframe)

SLA Targets:
  ├─ CRITICAL: 4 hours
  ├─ WARNING: 24 hours
  └─ INFO: 7 days
```

#### Panel 6: Individual Resident Trend

```
Title: Individual Resident Workload Control Chart
Type: Line Graph
X-Axis: Weeks
Y-Axis: Hours/Week
Lines:
  ├─ Actual hours (blue line)
  ├─ Centerline (black)
  ├─ ±1σ (light gray)
  ├─ ±2σ (medium gray)
  └─ ±3σ (dark gray)

Alerts Overlay:
  ├─ Rule 1: Red dots
  ├─ Rule 2: Orange bars (3-week window)
  ├─ Rule 3: Yellow shading (5-week trend)
  └─ Rule 4: Green band (8-week baseline)
```

---

## Alert Response SLAs

### CRITICAL (Rule 1)

**Target Response Time:** Within 24 hours

**Response Steps:**
1. [ ] Acknowledge receipt (immediate)
2. [ ] Verify data accuracy (within 4 hours)
3. [ ] Investigate root cause (within 8 hours)
4. [ ] Implement intervention (within 24 hours)
5. [ ] Document all actions (same day)

**Escalation:** If not acknowledged within 2 hours, escalate to Hospital VP

**Notification Recipients:**
- [ ] Program Director (phone + email + SMS)
- [ ] Chief Resident (email + SMS)
- [ ] Hospital VP (email if not resolved in 4 hours)

### WARNING (Rules 2 & 3)

**Target Response Time:** Within 48 hours

**Response Steps:**
1. [ ] Acknowledge receipt (within 8 hours)
2. [ ] Schedule review meeting (within 24 hours)
3. [ ] Analyze pattern/cause (meeting)
4. [ ] Plan action (if needed)
5. [ ] Implement action (within 48 hours)

**Escalation:** If not acknowledged within 24 hours, escalate to Program Director

**Notification Recipients:**
- [ ] Chief Resident (email)
- [ ] Program Director (dashboard alert)
- [ ] Coordinator (tracking)

### INFO (Rule 4)

**Target Response Time:** Within 1 week

**Response Steps:**
1. [ ] Review at next routine meeting
2. [ ] Assess if shift is intentional/appropriate
3. [ ] Adjust tracking if permanent shift confirmed
4. [ ] Update baseline/control limits if indicated

**Notification:** Dashboard only (no urgent notification)

---

## Configuration Maintenance

### Quarterly Review

**Every 3 months:**
1. [ ] Review alert volume (too many? too few?)
2. [ ] Analyze false positive rate (Rule 1 should be <1% of actual hours)
3. [ ] Check if parameters still appropriate
4. [ ] Update if program changes (new specialty, staffing model, etc.)
5. [ ] Test alert notification system (send test alert)

### Annual Recalibration

**Every 12 months:**
1. [ ] Collect full-year hour data
2. [ ] Calculate empirical control limits
3. [ ] Compare to configured limits
4. [ ] Adjust if empirical data significantly different
5. [ ] Update documentation

---

## Troubleshooting

### Problem: Too Many Rule 2/3 Alerts (Alert Fatigue)

**Causes:**
- Sigma too small (process variation larger than modeled)
- Seasonal workload pattern (not accounted for)
- Rotation schedule change (baseline shifted)

**Solutions:**
- [ ] Increase sigma by 0.5-1.0 hour
- [ ] Apply seasonal adjustment (lower limits in busy season)
- [ ] Implement re-centering when rotation changes
- [ ] Review actual process capability (Cpk metric)

### Problem: Rule 1 Alerts for Data Entry Errors

**Causes:**
- Double-counting hours
- Manually-entered data errors
- System calculation errors

**Solutions:**
- [ ] Add data validation (check reasonableness before alert)
- [ ] Implement confirmation step (require double-check before alert)
- [ ] Audit data entry process (automate vs. manual)
- [ ] Log all hour changes with source/reason

### Problem: No Alerts When Issues Occur

**Causes:**
- Gradual escalation (doesn't trigger single rules)
- Limits too high (process naturally exceeds them)
- Residents not reporting actual hours

**Solutions:**
- [ ] Review multi-rule detection (combine rules)
- [ ] Lower limits (if appropriate for program)
- [ ] Audit data accuracy (verify reported hours match actual)
- [ ] Implement real-time hour tracking (not just weekly)

---

## References

- Western Electric Company (1956). Statistical Quality Control Handbook
- Montgomery, D. C. (2009). Introduction to Statistical Quality Control
- ACGME Work Hour Standards: https://www.acgme.org/

---

**Document Classification:** OPERATIONAL - TECHNICAL
**Approved for:** System Administrators, Database Administrators, Monitoring Teams
**Effective Date:** 2025-12-31
**Last Updated:** 2025-12-31

