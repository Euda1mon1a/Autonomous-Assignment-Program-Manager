# Resilience API Endpoints

Complete reference for resilience framework monitoring and crisis management.

---

## Overview

The Resilience API provides endpoints for:
- **System Health Monitoring**: Real-time resilience metrics
- **Crisis Management**: Activate/deactivate crisis mode
- **Fallback Schedules**: Static backup schedules for emergencies
- **Load Shedding**: Prioritized service degradation
- **Vulnerability Analysis**: N-1/N-2 contingency testing
- **Defense Levels**: 5-tier escalation (GREEN → BLACK)

**Base Path**: `/api/v1/resilience`

**Authentication**: Most endpoints require JWT authentication. Admin role required for crisis activation.

**Framework**: Based on cross-disciplinary resilience (power grid N-1, queuing theory, epidemiology). See [Cross-Disciplinary Resilience](../cross-disciplinary-resilience.md).

---

## Get System Health

<span class="endpoint-badge get">GET</span> `/api/v1/resilience/health`

Get current resilience health status and metrics.

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | string (date) | No | Start date for analysis (default: today) |
| `end_date` | string (date) | No | End date for analysis (default: +30 days) |
| `include_contingency` | boolean | No | Run N-1/N-2 tests (default: false, slow) |
| `persist` | boolean | No | Save health check to database (default: true) |

### Response

```json
{
  "timestamp": "2024-07-01T10:00:00Z",
  "overall_status": "healthy",
  "utilization": {
    "utilization_rate": 0.72,
    "level": "normal",
    "buffer_remaining": 0.28,
    "max_sustainable": 0.80,
    "residents_working": 6,
    "residents_available": 9,
    "faculty_working": 8,
    "faculty_available": 12
  },
  "defense_level": "GREEN",
  "load_shedding_level": null,
  "n1_pass": true,
  "n2_pass": true,
  "phase_transition_risk": 0.05,
  "active_fallbacks": 0,
  "crisis_mode": false,
  "immediate_actions": [],
  "watch_items": [
    "Utilization approaching 75% - monitor for next 7 days"
  ],
  "metrics": {
    "total_assignments": 248,
    "coverage_rate": 0.98,
    "avg_hours_per_week": 68.5,
    "burnout_risk_score": 0.12
  }
}
```

### Defense Levels

| Level | Utilization | Status | Action Required |
|-------|-------------|--------|-----------------|
| **GREEN** | < 60% | Normal operations | None |
| **YELLOW** | 60-75% | Elevated watch | Monitor closely |
| **ORANGE** | 75-85% | High alert | Reduce load |
| **RED** | 85-95% | Critical | Activate fallbacks |
| **BLACK** | > 95% | System failure | Emergency protocols |

### Overall Status

| Status | Description |
|--------|-------------|
| `healthy` | All systems normal |
| `degraded` | Some issues, functioning |
| `critical` | Major problems, intervention needed |
| `failure` | System failure, emergency mode |

### Example Requests

**Basic health check**

```bash
curl "http://localhost:8000/api/v1/resilience/health" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Full health check with contingency analysis**

```bash
curl "http://localhost:8000/api/v1/resilience/health?include_contingency=true&start_date=2024-07-01&end_date=2024-07-31" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Python - Monitor health**

```python
import requests

response = requests.get(
    "http://localhost:8000/api/v1/resilience/health",
    headers={"Authorization": f"Bearer {token}"}
)

health = response.json()

print(f"Overall Status: {health['overall_status']}")
print(f"Defense Level: {health['defense_level']}")
print(f"Utilization: {health['utilization']['utilization_rate']:.1%}")

if health['defense_level'] in ['ORANGE', 'RED', 'BLACK']:
    print(f"\n⚠️  ALERT: Defense level {health['defense_level']}")
    for action in health['immediate_actions']:
        print(f"  - {action}")
```

---

## Activate Crisis Mode

<span class="endpoint-badge post">POST</span> `/api/v1/resilience/crisis/activate`

Activate crisis mode for emergency situations.

**Authorization**: Requires admin role.

### Request Body

```json
{
  "severity": "high",
  "reason": "Multiple faculty deployments - insufficient coverage",
  "expected_duration_hours": 168,
  "activate_fallback": true
}
```

### Request Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `severity` | string | Yes | Severity: `low`, `medium`, `high`, `critical` |
| `reason` | string | Yes | Reason for crisis activation |
| `expected_duration_hours` | integer | No | Expected crisis duration in hours |
| `activate_fallback` | boolean | No | Activate fallback schedule (default: false) |

### Response

```json
{
  "status": "activated",
  "severity": "high",
  "activated_at": "2024-07-01T10:00:00Z",
  "activated_by": "admin@example.com",
  "fallback_activated": true,
  "load_shedding_level": "medium",
  "message": "Crisis mode activated. Fallback schedule in effect."
}
```

### Example

```bash
curl -X POST http://localhost:8000/api/v1/resilience/crisis/activate \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "severity": "high",
    "reason": "COVID-19 outbreak - multiple staff quarantined",
    "expected_duration_hours": 336,
    "activate_fallback": true
  }'
```

---

## Deactivate Crisis Mode

<span class="endpoint-badge post">POST</span> `/api/v1/resilience/crisis/deactivate`

Deactivate crisis mode and return to normal operations.

**Authorization**: Requires admin role.

### Request Body

```json
{
  "reason": "Staffing restored to normal levels",
  "deactivate_fallback": true
}
```

### Response

```json
{
  "status": "deactivated",
  "deactivated_at": "2024-07-08T10:00:00Z",
  "deactivated_by": "admin@example.com",
  "fallback_deactivated": true,
  "message": "Crisis mode deactivated. Normal operations resumed."
}
```

### Example

```bash
curl -X POST http://localhost:8000/api/v1/resilience/crisis/deactivate \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "Staffing restored",
    "deactivate_fallback": true
  }'
```

---

## List Fallback Schedules

<span class="endpoint-badge get">GET</span> `/api/v1/resilience/fallbacks`

List all pre-computed fallback schedules.

### Response

```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "N-1 Fallback: Faculty Deployment",
      "scenario": "n1_faculty_deployment",
      "start_date": "2024-07-01",
      "end_date": "2024-07-31",
      "created_at": "2024-06-15T10:00:00Z",
      "is_active": false,
      "metadata": {
        "missing_faculty": 1,
        "coverage_rate": 0.95,
        "residents_affected": 3
      }
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "name": "N-2 Fallback: Dual Deployment",
      "scenario": "n2_dual_deployment",
      "start_date": "2024-07-01",
      "end_date": "2024-07-31",
      "created_at": "2024-06-15T10:30:00Z",
      "is_active": false,
      "metadata": {
        "missing_faculty": 2,
        "coverage_rate": 0.88,
        "residents_affected": 5
      }
    }
  ],
  "total": 5
}
```

### Fallback Scenarios

| Scenario | Description | Trigger |
|----------|-------------|---------|
| `n1_faculty_deployment` | One faculty deployed | Single deployment |
| `n2_dual_deployment` | Two faculty deployed | Dual deployment |
| `n1_resident_illness` | One resident out sick | Medical emergency |
| `holiday_coverage` | Reduced holiday staffing | Holidays |
| `pandemic_reduced` | Pandemic reduced capacity | COVID-19, flu outbreak |

### Example

```bash
curl "http://localhost:8000/api/v1/resilience/fallbacks" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Activate Fallback Schedule

<span class="endpoint-badge post">POST</span> `/api/v1/resilience/fallbacks/activate`

Activate a specific fallback schedule.

**Authorization**: Requires admin role.

### Request Body

```json
{
  "fallback_id": "550e8400-e29b-41d4-a716-446655440000",
  "reason": "Faculty deployment emergency",
  "effective_date": "2024-07-01"
}
```

### Response

```json
{
  "success": true,
  "fallback_id": "550e8400-e29b-41d4-a716-446655440000",
  "activated_at": "2024-07-01T10:00:00Z",
  "message": "Fallback schedule activated successfully"
}
```

### Example

```bash
curl -X POST http://localhost:8000/api/v1/resilience/fallbacks/activate \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "fallback_id": "550e8400-e29b-41d4-a716-446655440000",
    "reason": "Emergency deployment",
    "effective_date": "2024-07-01"
  }'
```

---

## Deactivate Fallback Schedule

<span class="endpoint-badge post">POST</span> `/api/v1/resilience/fallbacks/deactivate`

Deactivate current fallback schedule and return to primary schedule.

**Authorization**: Requires admin role.

### Request Body

```json
{
  "fallback_id": "550e8400-e29b-41d4-a716-446655440000",
  "reason": "Staffing restored to normal",
  "effective_date": "2024-07-08"
}
```

### Response

```json
{
  "success": true,
  "fallback_id": "550e8400-e29b-41d4-a716-446655440000",
  "deactivated_at": "2024-07-08T10:00:00Z",
  "message": "Fallback schedule deactivated. Primary schedule restored."
}
```

---

## Set Load Shedding Level

<span class="endpoint-badge post">POST</span> `/api/v1/resilience/load-shedding`

Adjust load shedding level to reduce system load.

**Authorization**: Requires admin role.

### Request Body

```json
{
  "level": "medium",
  "reason": "Approaching 80% utilization",
  "duration_hours": 24
}
```

### Load Shedding Levels

| Level | Services Affected | Impact |
|-------|-------------------|--------|
| `none` | None | Normal operations |
| `low` | Optional activities | Cancel electives, defer non-urgent |
| `medium` | Reduce clinic load | Reduce clinic sessions 25% |
| `high` | Minimum essential only | Emergency/inpatient only |
| `critical` | Skeleton crew | Absolute minimum coverage |

### Response

```json
{
  "level": "medium",
  "previous_level": "none",
  "set_at": "2024-07-01T10:00:00Z",
  "expires_at": "2024-07-02T10:00:00Z",
  "services_affected": [
    "Elective clinic sessions reduced by 25%",
    "Non-urgent procedures deferred",
    "Administrative duties postponed"
  ]
}
```

### Example

```bash
curl -X POST http://localhost:8000/api/v1/resilience/load-shedding \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "level": "medium",
    "reason": "High utilization - preventive measure",
    "duration_hours": 48
  }'
```

---

## Get Vulnerability Report

<span class="endpoint-badge get">GET</span> `/api/v1/resilience/vulnerability`

Run N-1/N-2 contingency analysis to identify vulnerabilities.

**Warning**: This endpoint is computationally expensive. Use sparingly.

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | string (date) | No | Analysis start date (default: today) |
| `end_date` | string (date) | No | Analysis end date (default: +30 days) |
| `scenarios` | string | No | Comma-separated scenarios to test |

### Response

```json
{
  "timestamp": "2024-07-01T10:00:00Z",
  "n1_pass": true,
  "n2_pass": false,
  "scenarios_tested": ["faculty_deployment", "resident_illness", "dual_deployment"],
  "vulnerabilities": [
    {
      "scenario": "dual_deployment",
      "severity": "high",
      "description": "System fails with 2 faculty deployed simultaneously",
      "impact": {
        "coverage_drop": 0.12,
        "supervision_violations": 8,
        "residents_affected": 5
      },
      "mitigation": "Pre-compute N-2 fallback schedule"
    }
  ],
  "recommendations": [
    "Create N-2 fallback schedule for dual deployment scenario",
    "Cross-train additional faculty for critical specialties",
    "Maintain buffer of on-call faculty for emergencies"
  ]
}
```

### Example

```bash
curl "http://localhost:8000/api/v1/resilience/vulnerability?start_date=2024-07-01&end_date=2024-07-31&scenarios=faculty_deployment,dual_deployment" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Get Health Check History

<span class="endpoint-badge get">GET</span> `/api/v1/resilience/health/history`

Retrieve historical health check records.

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | string (date) | No | Filter from this date |
| `end_date` | string (date) | No | Filter until this date |
| `limit` | integer | No | Maximum records to return (default: 100) |

### Response

```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "timestamp": "2024-07-01T10:00:00Z",
      "overall_status": "healthy",
      "utilization_rate": 0.72,
      "defense_level": "GREEN",
      "n1_pass": true,
      "n2_pass": true,
      "phase_transition_risk": 0.05
    }
  ],
  "total": 48
}
```

### Example

```bash
curl "http://localhost:8000/api/v1/resilience/health/history?start_date=2024-06-01&end_date=2024-07-01&limit=50" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Get Event History

<span class="endpoint-badge get">GET</span> `/api/v1/resilience/events`

Retrieve resilience event history (crisis activations, fallback activations, etc.).

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `event_type` | string | No | Filter by type: `crisis`, `fallback`, `load_shedding` |
| `severity` | string | No | Filter by severity: `low`, `medium`, `high`, `critical` |
| `start_date` | string (date) | No | Filter from this date |
| `end_date` | string (date) | No | Filter until this date |
| `limit` | integer | No | Maximum records (default: 100) |

### Response

```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "timestamp": "2024-07-01T10:00:00Z",
      "event_type": "crisis_activated",
      "severity": "high",
      "reason": "Multiple faculty deployments",
      "triggered_by": "admin@example.com",
      "previous_state": {"defense_level": "GREEN", "crisis_mode": false},
      "new_state": {"defense_level": "RED", "crisis_mode": true},
      "metadata": {
        "fallback_activated": true,
        "load_shedding_level": "medium"
      }
    }
  ],
  "total": 12
}
```

### Example

```bash
curl "http://localhost:8000/api/v1/resilience/events?event_type=crisis&severity=high&limit=20" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Common Use Cases

### 1. Daily Health Check Dashboard

```python
import requests

def daily_resilience_dashboard(token):
    """Generate daily resilience dashboard."""
    health = requests.get(
        "http://localhost:8000/api/v1/resilience/health",
        headers={"Authorization": f"Bearer {token}"}
    ).json()

    print(f"Resilience Dashboard - {health['timestamp']}")
    print(f"{'='*50}")

    # Overall status
    status_emoji = {
        'healthy': '✅',
        'degraded': '⚠️',
        'critical': '🔴',
        'failure': '💥'
    }

    print(f"\nOverall Status: {status_emoji.get(health['overall_status'], '❓')} {health['overall_status'].upper()}")
    print(f"Defense Level: {health['defense_level']}")

    # Utilization
    util = health['utilization']
    print(f"\nUtilization: {util['utilization_rate']:.1%}")
    print(f"  Residents: {util['residents_working']}/{util['residents_available']}")
    print(f"  Faculty: {util['faculty_working']}/{util['faculty_available']}")
    print(f"  Buffer: {util['buffer_remaining']:.1%}")

    # Contingency
    print(f"\nContingency Testing:")
    print(f"  N-1 (single failure): {'✅ PASS' if health['n1_pass'] else '❌ FAIL'}")
    print(f"  N-2 (dual failure): {'✅ PASS' if health['n2_pass'] else '❌ FAIL'}")

    # Actions
    if health['immediate_actions']:
        print(f"\n⚠️  IMMEDIATE ACTIONS REQUIRED:")
        for action in health['immediate_actions']:
            print(f"  - {action}")

    if health['watch_items']:
        print(f"\n👀 WATCH ITEMS:")
        for item in health['watch_items']:
            print(f"  - {item}")

    return health

# Run daily
dashboard = daily_resilience_dashboard(token)
```

### 2. Auto-Escalate on Defense Level Change

```python
def monitor_defense_level(token, alert_email=None):
    """Monitor and alert on defense level changes."""
    health = requests.get(
        "http://localhost:8000/api/v1/resilience/health",
        headers={"Authorization": f"Bearer {token}"}
    ).json()

    level = health['defense_level']

    # Escalate if ORANGE or above
    if level in ['ORANGE', 'RED', 'BLACK']:
        alert_message = f"""
DEFENSE LEVEL ALERT: {level}

Utilization: {health['utilization']['utilization_rate']:.1%}
Status: {health['overall_status']}

Immediate Actions:
"""
        for action in health['immediate_actions']:
            alert_message += f"\n- {action}"

        print(alert_message)

        if alert_email:
            send_email(alert_email, f"Defense Level {level}", alert_message)

        # Auto-activate fallback if RED or BLACK
        if level in ['RED', 'BLACK']:
            print("🚨 AUTO-ACTIVATING CRISIS MODE")
            requests.post(
                "http://localhost:8000/api/v1/resilience/crisis/activate",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "severity": "high" if level == "RED" else "critical",
                    "reason": f"Auto-activated due to {level} defense level",
                    "activate_fallback": True
                }
            )

# Run every 15 minutes
monitor_defense_level(token, alert_email="pd@example.com")
```

### 3. Pre-Generate Fallback Schedules

```python
def generate_contingency_fallbacks(token):
    """Pre-generate fallback schedules for common scenarios."""
    scenarios = [
        {"name": "N-1 Faculty Deployment", "scenario": "faculty_deployment"},
        {"name": "N-1 Resident Illness", "scenario": "resident_illness"},
        {"name": "N-2 Dual Deployment", "scenario": "dual_deployment"},
        {"name": "Holiday Reduced Staffing", "scenario": "holiday_coverage"}
    ]

    for scenario in scenarios:
        print(f"Generating fallback: {scenario['name']}")

        # Generate schedule for scenario
        # (Implementation depends on your fallback generation logic)

        print(f"  ✅ Generated and saved")

# Run monthly
generate_contingency_fallbacks(token)
```

---

## Error Codes

| Code | Status | Description |
|------|--------|-------------|
| `CRISIS_ALREADY_ACTIVE` | 409 | Crisis mode is already activated |
| `NO_ACTIVE_CRISIS` | 400 | No active crisis to deactivate |
| `FALLBACK_NOT_FOUND` | 404 | Fallback schedule does not exist |
| `FALLBACK_ALREADY_ACTIVE` | 409 | Fallback is already activated |
| `INSUFFICIENT_PERMISSIONS` | 403 | Admin role required |
| `INVALID_SEVERITY` | 422 | Invalid severity level |
| `INVALID_LOAD_LEVEL` | 422 | Invalid load shedding level |

---

## See Also

- [Cross-Disciplinary Resilience](../cross-disciplinary-resilience.md) - Framework concepts
- [Exotic Frontier API](../exotic-frontier-api.md) - Advanced resilience features
- [Schedule API](schedules.md) - Schedule generation
- [Compliance API](compliance.md) - ACGME validation
