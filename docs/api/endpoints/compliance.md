# ACGME Compliance API Endpoints

Complete reference for ACGME compliance validation and monitoring.

---

## Overview

The Compliance API provides endpoints for:
- Real-time ACGME compliance validation
- Work hour tracking and reporting
- Supervision ratio verification
- Compliance violation management

**Base Path**: `/api/v1/schedule/validate` (part of Schedule API)

**Authentication**: All endpoints require JWT authentication.

**ACGME Rules**: See [ACGME Compliance Rules](#acgme-compliance-rules) below.

---

## Validate Schedule

<span class="endpoint-badge get">GET</span> `/api/v1/schedule/validate`

Validate a schedule for ACGME compliance across a date range.

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | string (date) | Yes | Start date (YYYY-MM-DD) |
| `end_date` | string (date) | Yes | End date (YYYY-MM-DD) |

### Response

**All Compliant (200 OK)**

```json
{
  "valid": true,
  "total_violations": 0,
  "violations": [],
  "coverage_rate": 1.0,
  "statistics": {
    "total_residents": 9,
    "residents_checked": 9,
    "date_range_days": 31,
    "80_hour_violations": 0,
    "1_in_7_violations": 0,
    "supervision_violations": 0,
    "avg_hours_per_week": 68.5,
    "max_hours_per_week": 76.0,
    "min_hours_per_week": 60.5
  }
}
```

**Violations Found (200 OK)**

```json
{
  "valid": false,
  "total_violations": 3,
  "violations": [
    {
      "type": "80_HOUR_RULE",
      "severity": "CRITICAL",
      "person_id": "550e8400-e29b-41d4-a716-446655440000",
      "person_name": "PGY1-01",
      "block_id": null,
      "message": "80-hour rule violated: 84.5 hours in 4-week period ending 2024-07-28",
      "details": {
        "actual_hours": 84.5,
        "max_hours": 80.0,
        "period_start": "2024-07-01",
        "period_end": "2024-07-28",
        "excess_hours": 4.5
      }
    },
    {
      "type": "SUPERVISION_RATIO",
      "severity": "HIGH",
      "person_id": null,
      "person_name": null,
      "block_id": "550e8400-e29b-41d4-a716-446655440001",
      "message": "Supervision ratio violated on 2024-07-15 AM: 1:5 (required: 1:2 for PGY-1)",
      "details": {
        "actual_ratio": 5,
        "required_ratio": 2,
        "pgy_level": 1,
        "date": "2024-07-15",
        "session": "AM",
        "residents": 5,
        "faculty": 1
      }
    },
    {
      "type": "1_IN_7_RULE",
      "severity": "HIGH",
      "person_id": "550e8400-e29b-41d4-a716-446655440002",
      "person_name": "PGY2-03",
      "block_id": null,
      "message": "1-in-7 rule violated: no 24-hour period off in 8 days (2024-07-10 to 2024-07-17)",
      "details": {
        "last_day_off": "2024-07-09",
        "days_worked": 8,
        "max_days": 7,
        "period_start": "2024-07-10",
        "period_end": "2024-07-17"
      }
    }
  ],
  "coverage_rate": 0.98,
  "statistics": {
    "total_residents": 9,
    "residents_checked": 9,
    "date_range_days": 31,
    "80_hour_violations": 1,
    "1_in_7_violations": 1,
    "supervision_violations": 1,
    "avg_hours_per_week": 72.5,
    "max_hours_per_week": 84.5,
    "min_hours_per_week": 60.0
  }
}
```

### Example Requests

**cURL**

```bash
curl "http://localhost:8000/api/v1/schedule/validate?start_date=2024-07-01&end_date=2024-07-31" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Python**

```python
import requests

params = {
    "start_date": "2024-07-01",
    "end_date": "2024-07-31"
}

response = requests.get(
    "http://localhost:8000/api/v1/schedule/validate",
    headers={"Authorization": f"Bearer {token}"},
    params=params
)

validation = response.json()

if validation['valid']:
    print(f"✅ Schedule is ACGME compliant")
    print(f"   Coverage rate: {validation['coverage_rate']:.1%}")
    print(f"   Avg hours/week: {validation['statistics']['avg_hours_per_week']:.1f}")
else:
    print(f"❌ {validation['total_violations']} violations found")
    for v in validation['violations']:
        print(f"\n{v['severity']}: {v['type']}")
        print(f"  {v['message']}")
        if v.get('person_name'):
            print(f"  Person: {v['person_name']}")
```

---

## ACGME Compliance Rules

### 1. 80-Hour Rule

**Requirement**: Residents must not exceed 80 hours of work per week, averaged over a 4-week period.

**Calculation**:
- Rolling 4-week window (28 days)
- Includes all clinical and educational activities
- Call hours count as work hours

**Severity**: CRITICAL

**Example Violation**:
```json
{
  "type": "80_HOUR_RULE",
  "severity": "CRITICAL",
  "message": "80-hour rule violated: 84.5 hours in 4-week period ending 2024-07-28",
  "details": {
    "actual_hours": 84.5,
    "max_hours": 80.0,
    "excess_hours": 4.5
  }
}
```

### 2. 1-in-7 Rule

**Requirement**: Residents must have at least one 24-hour period free of clinical work every 7 days, averaged over 4 weeks.

**Calculation**:
- 24-hour period = midnight to midnight
- Must occur at least once every 7 days
- Some flexibility for clinical emergencies

**Severity**: HIGH

**Example Violation**:
```json
{
  "type": "1_IN_7_RULE",
  "severity": "HIGH",
  "message": "1-in-7 rule violated: no 24-hour period off in 8 days",
  "details": {
    "last_day_off": "2024-07-09",
    "days_worked": 8,
    "max_days": 7
  }
}
```

### 3. Supervision Ratios

**Requirement**: Adequate faculty supervision based on resident level.

**Ratios**:
| PGY Level | Required Ratio | Description |
|-----------|----------------|-------------|
| PGY-1 | 1:2 | One faculty per 2 residents |
| PGY-2 | 1:4 | One faculty per 4 residents |
| PGY-3 | 1:4 | One faculty per 4 residents |

**Calculation**:
- Per block (AM/PM session)
- Ratio calculated as residents/faculty
- Violations flagged when exceeded

**Severity**: HIGH

**Example Violation**:
```json
{
  "type": "SUPERVISION_RATIO",
  "severity": "HIGH",
  "message": "Supervision ratio violated on 2024-07-15 AM: 1:5 (required: 1:2 for PGY-1)",
  "details": {
    "actual_ratio": 5,
    "required_ratio": 2,
    "pgy_level": 1,
    "residents": 5,
    "faculty": 1
  }
}
```

---

## Violation Severity Levels

| Severity | Description | Action Required |
|----------|-------------|-----------------|
| **CRITICAL** | Major ACGME violation, immediate action required | Fix before resident works |
| **HIGH** | Significant violation, should be corrected soon | Address within 24-48 hours |
| **MEDIUM** | Minor violation, should be monitored | Review and adjust if pattern emerges |
| **LOW** | Warning/advisory, no immediate action | Monitor for trends |

---

## Common Use Cases

### 1. Pre-Generation Validation

```python
import requests

def validate_before_generation(start_date, end_date, token):
    """Check compliance before generating new schedule."""
    params = {
        "start_date": start_date,
        "end_date": end_date
    }

    response = requests.get(
        "http://localhost:8000/api/v1/schedule/validate",
        headers={"Authorization": f"Bearer {token}"},
        params=params
    )

    validation = response.json()

    if not validation['valid']:
        print(f"⚠️  Found {validation['total_violations']} violations")
        print("Violations by type:")

        # Group by type
        by_type = {}
        for v in validation['violations']:
            vtype = v['type']
            if vtype not in by_type:
                by_type[vtype] = 0
            by_type[vtype] += 1

        for vtype, count in by_type.items():
            print(f"  - {vtype}: {count}")

        return False

    return True

# Usage
if validate_before_generation("2024-07-01", "2024-07-31", token):
    print("✅ Safe to generate schedule")
else:
    print("❌ Fix violations first")
```

### 2. Monitor Weekly Compliance

```python
from datetime import datetime, timedelta

def check_weekly_compliance(token):
    """Check compliance for current week."""
    today = datetime.now().date()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)

    response = requests.get(
        "http://localhost:8000/api/v1/schedule/validate",
        headers={"Authorization": f"Bearer {token}"},
        params={
            "start_date": week_start.isoformat(),
            "end_date": week_end.isoformat()
        }
    )

    validation = response.json()

    print(f"Week of {week_start}:")
    print(f"  Valid: {validation['valid']}")
    print(f"  Violations: {validation['total_violations']}")
    print(f"  Coverage: {validation['coverage_rate']:.1%}")

    return validation

# Run daily check
validation = check_weekly_compliance(token)
```

### 3. Generate Compliance Report

```python
def generate_compliance_report(start_date, end_date, token):
    """Generate detailed compliance report."""
    response = requests.get(
        "http://localhost:8000/api/v1/schedule/validate",
        headers={"Authorization": f"Bearer {token}"},
        params={
            "start_date": start_date,
            "end_date": end_date
        }
    )

    validation = response.json()
    stats = validation['statistics']

    print(f"ACGME Compliance Report")
    print(f"Period: {start_date} to {end_date}")
    print(f"\n{'='*50}")
    print(f"\nOverall Status: {'✅ COMPLIANT' if validation['valid'] else '❌ NON-COMPLIANT'}")
    print(f"Total Violations: {validation['total_violations']}")
    print(f"Coverage Rate: {validation['coverage_rate']:.1%}")

    print(f"\n{'='*50}")
    print(f"\nStatistics:")
    print(f"  Residents Checked: {stats['residents_checked']}/{stats['total_residents']}")
    print(f"  Average Hours/Week: {stats['avg_hours_per_week']:.1f}")
    print(f"  Max Hours/Week: {stats['max_hours_per_week']:.1f}")
    print(f"  Min Hours/Week: {stats['min_hours_per_week']:.1f}")

    print(f"\n{'='*50}")
    print(f"\nViolations by Type:")
    print(f"  80-Hour Rule: {stats['80_hour_violations']}")
    print(f"  1-in-7 Rule: {stats['1_in_7_violations']}")
    print(f"  Supervision: {stats['supervision_violations']}")

    if validation['violations']:
        print(f"\n{'='*50}")
        print(f"\nDetailed Violations:")
        for i, v in enumerate(validation['violations'], 1):
            print(f"\n{i}. {v['type']} ({v['severity']})")
            print(f"   {v['message']}")
            if v.get('person_name'):
                print(f"   Person: {v['person_name']}")

    return validation

# Usage
report = generate_compliance_report("2024-07-01", "2024-07-31", token)
```

### 4. Alert on Violations

```python
def alert_on_violations(start_date, end_date, token, email_to=None):
    """Check compliance and send alert if violations found."""
    response = requests.get(
        "http://localhost:8000/api/v1/schedule/validate",
        headers={"Authorization": f"Bearer {token}"},
        params={
            "start_date": start_date,
            "end_date": end_date
        }
    )

    validation = response.json()

    if not validation['valid']:
        critical = [v for v in validation['violations'] if v['severity'] == 'CRITICAL']
        high = [v for v in validation['violations'] if v['severity'] == 'HIGH']

        alert_message = f"""
ACGME COMPLIANCE ALERT

Period: {start_date} to {end_date}
Total Violations: {validation['total_violations']}

Critical: {len(critical)}
High: {len(high)}

Action Required:
"""
        for v in critical:
            alert_message += f"\n⚠️  {v['type']}: {v['message']}"

        print(alert_message)

        if email_to:
            # Send email (implement your email service)
            send_email(email_to, "ACGME Compliance Alert", alert_message)

        return True  # Alert sent

    return False  # No violations

# Usage - Run daily
alert_sent = alert_on_violations("2024-07-01", "2024-07-31", token, email_to="pd@example.com")
```

---

## Compliance Metrics

### Coverage Rate

Percentage of blocks with assigned residents:

```
coverage_rate = assigned_blocks / total_blocks
```

- **Target**: ≥ 0.95 (95%)
- **Minimum**: 0.90 (90%)

### Average Hours Per Week

Mean work hours across all residents:

```
avg_hours = sum(resident_hours) / num_residents
```

- **Target**: 60-70 hours
- **Maximum**: 80 hours (ACGME limit)

### Violation Rate

Violations per resident:

```
violation_rate = total_violations / residents_checked
```

- **Target**: 0.0 (no violations)
- **Acceptable**: ≤ 0.1 (10% of residents)

---

## Error Codes

| Code | Status | Description |
|------|--------|-------------|
| `INVALID_DATE_FORMAT` | 400 | Date must be in YYYY-MM-DD format |
| `INVALID_DATE_RANGE` | 400 | start_date must be before end_date |
| `DATE_RANGE_TOO_LARGE` | 400 | Date range exceeds maximum (365 days) |
| `NO_ASSIGNMENTS` | 422 | No assignments found in date range |

---

## Best Practices

### 1. Validate Before and After

```python
# Before schedule generation
validate_before_generation(start_date, end_date, token)

# Generate schedule
generate_schedule(...)

# After schedule generation
validate_after_generation(start_date, end_date, token)
```

### 2. Monitor Continuously

Set up automated compliance checks:

```python
# Daily compliance check (cron job)
import schedule
import time

def daily_compliance_check():
    today = datetime.now().date()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)

    validation = check_weekly_compliance(token)

    if not validation['valid']:
        alert_on_violations(
            week_start.isoformat(),
            week_end.isoformat(),
            token,
            email_to="pd@example.com"
        )

# Run daily at 8 AM
schedule.every().day.at("08:00").do(daily_compliance_check)

while True:
    schedule.run_pending()
    time.sleep(60)
```

### 3. Track Trends

```python
def track_compliance_trends(token, weeks=4):
    """Track compliance over multiple weeks."""
    import pandas as pd
    from datetime import datetime, timedelta

    results = []
    today = datetime.now().date()

    for i in range(weeks):
        week_start = today - timedelta(days=today.weekday() + (i * 7))
        week_end = week_start + timedelta(days=6)

        validation = check_weekly_compliance(token)

        results.append({
            'week': week_start.isoformat(),
            'valid': validation['valid'],
            'violations': validation['total_violations'],
            'coverage': validation['coverage_rate'],
            'avg_hours': validation['statistics']['avg_hours_per_week']
        })

    # Create DataFrame and analyze
    df = pd.DataFrame(results)
    print(df)

    # Check if violations are increasing
    if df['violations'].is_monotonic_increasing:
        print("⚠️  Warning: Violations trending upward")
```

---

## See Also

- [Schedule API](schedules.md) - Schedule generation with validation
- [Assignments API](assignments.md) - Assignment creation with ACGME checks
- [Resilience API](resilience.md) - System health monitoring
- [Authentication](../authentication.md) - Token management
