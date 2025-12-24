# Compliance Monitoring

Monitor ACGME compliance in real-time.

---

## Compliance Dashboard

Navigate to **Compliance** to see:

- **Overall Score**: Program-wide compliance percentage
- **Active Violations**: Current issues requiring attention
- **Trends**: Compliance over time
- **By Person**: Individual compliance status

---

## ACGME Rules Monitored

| Rule | Description | Threshold |
|------|-------------|-----------|
| **80-Hour Rule** | Weekly work hours | ≤80 hours/week avg |
| **1-in-7 Rule** | Day off frequency | 1 day off per 7 days |
| **24-Hour Limit** | Continuous duty | ≤24 hours continuous |
| **Supervision** | Faculty ratios | PGY-1: 1:2, PGY-2/3: 1:4 |

---

## Violation Severity

| Level | Color | Response Required |
|-------|-------|------------------|
| **Critical** | :material-circle:{ style="color: #E57373" } Red | Immediate action |
| **High** | :material-circle:{ style="color: #FF8A65" } Orange | Same-day resolution |
| **Medium** | :material-circle:{ style="color: #FFD54F" } Yellow | Weekly review |
| **Low** | :material-circle:{ style="color: #4FC3F7" } Blue | Informational |

---

## Proactive Compliance: Scheduled Hours Calculator

!!! tip "Prevention Over Correction"
    The **Scheduled Hours Calculator** displays projected work hours based on schedule assignments, enabling you to identify potential ACGME violations **before** they occur.

### Scheduled vs. Actual Hours

| Metric | Source | Purpose |
|--------|--------|---------|
| **Scheduled Hours** | Schedule assignments | Proactive planning |
| **Actual Duty Hours** | MyEvaluations | Official ACGME reporting |

The Scheduled Hours Calculator shows:
- Current week projected hours
- 4-week rolling average projection
- Compliance status: On Track / Review Needed / Action Required

When status shows **Review Needed** or **Action Required**, adjust the schedule proactively before violations occur.

See [GUI Improvements > Scheduled Hours Calculator](gui-improvements.md#scheduled-hours-calculator) for full details.

---

## Resolving Violations

1. Click on a violation in the dashboard
2. Review details and affected parties
3. Choose resolution:
    - **Reassign**: Move assignment to another person
    - **Reschedule**: Change timing
    - **Document Exception**: Record approved variance
4. Add resolution notes
5. Click **Resolve**

---

## Compliance Reports

Generate compliance reports:

1. Go to **Compliance** → **Reports**
2. Select date range
3. Choose report type:
    - Summary report
    - Detail by resident
    - Violation history
4. Export to PDF or Excel
