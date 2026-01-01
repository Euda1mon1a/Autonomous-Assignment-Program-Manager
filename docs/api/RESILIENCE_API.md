# Resilience API Reference

**Endpoint Prefix:** `/api/resilience`

## Overview

The Resilience API provides system health monitoring, crisis management, and load shedding controls. This system integrates cross-industry resilience concepts including queuing theory, epidemiology, and defense-in-depth strategies.

### Key Features

- **System Health Monitoring**: Real-time system status and utilization metrics
- **Crisis Management**: Activate/deactivate crisis mode for emergency situations
- **Fallback Schedules**: Pre-computed backup schedules for N-1 scenarios
- **Load Shedding**: Controlled degradation to prevent cascade failures
- **Vulnerability Analysis**: Detect system weaknesses before failures
- **Event History**: Audit trail of all resilience events

### Defense Levels

The system operates at 5 defense levels:

1. **GREEN**: Optimal (< 60% utilization)
2. **YELLOW**: Elevated (60-75% utilization)
3. **ORANGE**: High (75-85% utilization)
4. **RED**: Critical (85-95% utilization)
5. **BLACK**: Emergency (> 95% or crisis mode active)

---

## Endpoints

### GET /health

Get current system health status.

**Request:**
```bash
curl -X GET 'http://localhost:8000/api/resilience/health?persist=true&include_contingency=false' \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

**Query Parameters:**
- `start_date` (optional, YYYY-MM-DD): Analyze from this date
- `end_date` (optional, YYYY-MM-DD): Analyze until this date
- `include_contingency` (optional, default: false): Include N-1/N-2 contingency analysis
- `persist` (optional, default: true): Store result in database
- `max_faculty` (optional): Limit faculty records for large datasets
- `max_blocks` (optional): Limit block records for large datasets

**Response (200):**
```json
{
  "timestamp": "2025-12-31T16:30:00Z",
  "overall_status": "green",
  "defense_level": "GREEN",
  "utilization": {
    "utilization_rate": 0.65,
    "level": "YELLOW",
    "buffer_remaining": 0.35
  },
  "immediate_actions": [],
  "watch_items": [
    {
      "metric": "capacity_utilization",
      "current_value": 0.65,
      "threshold": 0.80,
      "recommendation": "Monitor for increased scheduling pressure"
    }
  ],
  "n1_pass": true,
  "n2_pass": true,
  "load_shedding_level": "none",
  "active_fallbacks": [],
  "crisis_mode": false,
  "phase_transition_risk": "low",
  "contingency_analysis": {
    "coverage_if_faculty_loss": 0.95,
    "critical_faculty": [
      {
        "faculty_id": "550e8400-e29b-41d4-a716-446655440010",
        "name": "Dr. Sarah Johnson",
        "coverage_impact": 0.15,
        "reason": "Only attending in Cardiology"
      }
    ]
  }
}
```

**Health Status Levels:**
- `green`: System healthy, normal operations
- `yellow`: Elevated utilization, monitor closely
- `orange`: High utilization, prepare contingencies
- `red`: Critical utilization, may activate load shedding
- `black`: Emergency, crisis mode recommended

---

### GET /health/history

Get historical health check data.

**Request:**
```bash
curl -X GET 'http://localhost:8000/api/resilience/health/history?start_date=2025-12-01&end_date=2025-12-31&page=1&page_size=50' \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

**Query Parameters:**
- `start_date` (optional, YYYY-MM-DD): From date
- `end_date` (optional, YYYY-MM-DD): To date
- `page` (optional, default: 1): Page number
- `page_size` (optional, default: 50): Items per page

**Response (200):**
```json
{
  "items": [
    {
      "timestamp": "2025-12-31T16:30:00Z",
      "overall_status": "green",
      "utilization_rate": 0.65,
      "defense_level": "YELLOW",
      "n1_pass": true,
      "n2_pass": true,
      "load_shedding_level": "none",
      "active_fallbacks": 0,
      "crisis_mode": false
    }
  ],
  "total": 48,
  "page": 1,
  "page_size": 50
}
```

---

### POST /crisis/activate

Activate crisis mode for emergency response.

**Request:**
```bash
curl -X POST http://localhost:8000/api/resilience/crisis/activate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{
    "reason": "Military deployment of 3 faculty",
    "expected_duration_hours": 72,
    "auto_deactivate": true,
    "triggered_by": "Admin"
  }'
```

**Request Body:**
```json
{
  "reason": "string (required)",
  "expected_duration_hours": "number (optional)",
  "auto_deactivate": "boolean (optional, default: true)",
  "triggered_by": "string (optional)"
}
```

**Response (200):**
```json
{
  "success": true,
  "crisis_mode": true,
  "activated_at": "2025-12-31T16:30:00Z",
  "expected_deactivation": "2026-01-03T16:30:00Z",
  "load_shedding_initiated": true,
  "fallback_activated": true,
  "message": "Crisis mode activated. Load shedding and fallback schedule engaged."
}
```

**Crisis Mode Effects:**

1. **Load Shedding**: Non-critical assignments reduced
2. **Fallback Schedule**: Pre-computed backup schedule activated
3. **Reduced Utilization**: System targets 70% utilization
4. **Emergency Communication**: Alerts sent to stakeholders
5. **Priority Assignments**: Only critical assignments scheduled

---

### POST /crisis/deactivate

Deactivate crisis mode and restore normal operations.

**Request:**
```bash
curl -X POST http://localhost:8000/api/resilience/crisis/deactivate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{
    "reason": "Emergency resolved",
    "restore_from_fallback": false
  }'
```

**Request Body:**
```json
{
  "reason": "string (required)",
  "restore_from_fallback": "boolean (optional, default: false)"
}
```

**Response (200):**
```json
{
  "success": true,
  "crisis_mode": false,
  "deactivated_at": "2025-12-31T19:30:00Z",
  "duration_hours": 3,
  "fallback_restored": false,
  "message": "Crisis mode deactivated. Normal scheduling resumed."
}
```

---

### POST /fallback/activate

Manually activate a pre-computed fallback schedule.

**Request:**
```bash
curl -X POST http://localhost:8000/api/resilience/fallback/activate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{
    "fallback_id": "550e8400-e29b-41d4-a716-446655440700",
    "reason": "Faculty emergency leave"
  }'
```

**Request Body:**
```json
{
  "fallback_id": "string (UUID, required)",
  "reason": "string (required)"
}
```

**Response (200):**
```json
{
  "success": true,
  "fallback_id": "550e8400-e29b-41d4-a716-446655440700",
  "activated_at": "2025-12-31T16:45:00Z",
  "coverage_rate": 0.98,
  "assignments_changed": 47,
  "message": "Fallback schedule activated"
}
```

---

### POST /fallback/deactivate

Deactivate a fallback schedule and return to normal.

**Request:**
```bash
curl -X POST http://localhost:8000/api/resilience/fallback/deactivate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{
    "fallback_id": "550e8400-e29b-41d4-a716-446655440700",
    "reason": "Return to normal schedule"
  }'
```

**Response (200):**
```json
{
  "success": true,
  "fallback_id": "550e8400-e29b-41d4-a716-446655440700",
  "deactivated_at": "2025-12-31T19:30:00Z",
  "duration_minutes": 165,
  "assignments_restored": 47,
  "message": "Fallback schedule deactivated"
}
```

---

### GET /fallback/list

List pre-computed fallback schedules.

**Request:**
```bash
curl -X GET 'http://localhost:8000/api/resilience/fallback/list?status=ready' \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

**Query Parameters:**
- `status` (optional): Filter by status - `'ready'`, `'active'`, `'expired'`

**Response (200):**
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440700",
      "start_date": "2025-01-01",
      "end_date": "2025-12-31",
      "coverage_rate": 0.98,
      "scenario": "Faculty loss (single)",
      "status": "ready",
      "created_at": "2025-12-30T10:00:00Z",
      "expires_at": "2025-12-31T23:59:59Z"
    }
  ],
  "total": 3,
  "active_fallback": null
}
```

---

### GET /events/history

Get resilience event history.

**Request:**
```bash
curl -X GET 'http://localhost:8000/api/resilience/events/history?start_date=2025-12-01&event_type=crisis&page=1' \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

**Query Parameters:**
- `start_date` (optional, YYYY-MM-DD): From date
- `end_date` (optional, YYYY-MM-DD): To date
- `event_type` (optional): Filter by type
- `severity` (optional): Filter by severity
- `page` (optional, default: 1): Page number

**Response (200):**
```json
{
  "items": [
    {
      "timestamp": "2025-12-31T16:30:00Z",
      "event_type": "crisis_activated",
      "severity": "critical",
      "reason": "Military deployment of 3 faculty",
      "triggered_by": "Admin",
      "previous_state": {
        "crisis_mode": false,
        "defense_level": "YELLOW"
      },
      "new_state": {
        "crisis_mode": true,
        "defense_level": "BLACK"
      }
    }
  ],
  "total": 12,
  "page": 1
}
```

---

### GET /vulnerabilities

Identify system vulnerabilities.

**Request:**
```bash
curl -X GET 'http://localhost:8000/api/resilience/vulnerabilities?include_remediation=true' \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

**Query Parameters:**
- `include_remediation` (optional, default: true): Include remediation suggestions

**Response (200):**
```json
{
  "vulnerabilities": [
    {
      "id": "vuln_001",
      "category": "single_point_of_failure",
      "severity": "high",
      "affected_resource": "Dr. Sarah Johnson (Cardiology attending)",
      "impact": "Loss of Cardiology attending removes ability to supervise all cardiology rotations",
      "coverage_if_lost": 0.0,
      "remediation": [
        "Cross-train Dr. Michael Chen in cardiology supervision",
        "Recruit additional cardiology faculty"
      ]
    }
  ],
  "critical_count": 1,
  "high_count": 3,
  "medium_count": 5,
  "total_score": 0.45
}
```

---

### POST /load-shedding/activate

Activate load shedding to reduce utilization.

**Request:**
```bash
curl -X POST http://localhost:8000/api/resilience/load-shedding/activate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{
    "level": "moderate",
    "target_utilization": 0.70,
    "reason": "High capacity utilization"
  }'
```

**Request Body:**
```json
{
  "level": "light | moderate | heavy (required)",
  "target_utilization": "number between 0.5 and 0.9 (optional)",
  "reason": "string (required)"
}
```

**Load Shedding Levels:**

- **light**: Reduce 5-10% of non-critical assignments
- **moderate**: Reduce 10-20% of non-critical assignments
- **heavy**: Reduce 20-30% of non-critical assignments

**Response (200):**
```json
{
  "success": true,
  "load_shedding_level": "moderate",
  "activated_at": "2025-12-31T16:30:00Z",
  "target_utilization": 0.70,
  "current_utilization": 0.82,
  "assignments_to_shed": 42,
  "message": "Load shedding activated"
}
```

---

### POST /load-shedding/deactivate

Deactivate load shedding and restore normal scheduling.

**Request:**
```bash
curl -X POST http://localhost:8000/api/resilience/load-shedding/deactivate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{
    "reason": "Capacity returned to normal"
  }'
```

**Response (200):**
```json
{
  "success": true,
  "load_shedding_level": "none",
  "deactivated_at": "2025-12-31T18:30:00Z",
  "assignments_restored": 42,
  "message": "Load shedding deactivated"
}
```

---

## Common Workflows

### 1. Faculty Emergency - Activate Crisis Mode

```bash
# 1. Check current health
curl -X GET http://localhost:8000/api/resilience/health \
  -H "Authorization: Bearer <ACCESS_TOKEN>" | jq '.defense_level'

# 2. Activate crisis mode
curl -X POST http://localhost:8000/api/resilience/crisis/activate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{
    "reason": "3 faculty unplanned absences",
    "expected_duration_hours": 48
  }'

# 3. Monitor health
curl -X GET http://localhost:8000/api/resilience/health \
  -H "Authorization: Bearer <ACCESS_TOKEN>" | jq '.crisis_mode'

# 4. Deactivate when resolved
curl -X POST http://localhost:8000/api/resilience/crisis/deactivate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{"reason": "Absences resolved"}'
```

### 2. Prepare Fallback Schedules

```bash
# List available fallbacks
curl -X GET 'http://localhost:8000/api/resilience/fallback/list?status=ready' \
  -H "Authorization: Bearer <ACCESS_TOKEN>"

# Activate fallback if needed
curl -X POST http://localhost:8000/api/resilience/fallback/activate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{
    "fallback_id": "fallback_id",
    "reason": "Faculty emergency"
  }'
```

### 3. Load Shedding During High Utilization

```bash
# Check health status
curl -X GET http://localhost:8000/api/resilience/health \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  | jq '.utilization.utilization_rate'

# If > 85%, activate load shedding
curl -X POST http://localhost:8000/api/resilience/load-shedding/activate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{
    "level": "moderate",
    "target_utilization": 0.75,
    "reason": "Utilization above 85%"
  }'
```

---

## Data Models

### Health Check Response

```json
{
  "timestamp": "string (ISO 8601)",
  "overall_status": "string (green/yellow/orange/red/black)",
  "defense_level": "string",
  "utilization": {
    "utilization_rate": "number 0.0-1.0",
    "level": "string",
    "buffer_remaining": "number"
  },
  "n1_pass": "boolean",
  "n2_pass": "boolean",
  "load_shedding_level": "string",
  "active_fallbacks": ["string"],
  "crisis_mode": "boolean",
  "immediate_actions": ["string"],
  "watch_items": ["object"]
}
```

---

## Error Codes

| Code | Name | Description |
|------|------|-------------|
| 400 | Bad Request | Invalid request format |
| 401 | Unauthorized | Authentication required |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 500 | Internal Server Error | Server error |

---

## Related Documentation

**Related API Documentation:**
- [FMIT Health API](FMIT_HEALTH_API.md) - FMIT coverage and swap monitoring
- [Schedule API](SCHEDULE_API.md) - Schedule generation for fallback schedules
- [Health API](HEALTH_API.md) - Overall system health
- [Swaps API](SWAPS_API.md) - Swap management during crisis mode

**Architecture Decision Records:**
- [ADR-004: Cross-Disciplinary Resilience Framework](../architecture/decisions/ADR-004-resilience-framework.md) - Resilience framework design and rationale
- [ADR-002: Constraint Programming](../architecture/decisions/ADR-002-constraint-programming-ortools.md) - Solver used for fallback schedules

**Architecture Documentation:**
- [Cross-Disciplinary Resilience](../architecture/cross-disciplinary-resilience.md) - Full resilience framework documentation
- [Exotic Frontier Concepts](../architecture/EXOTIC_FRONTIER_CONCEPTS.md) - Tier 5 advanced resilience concepts
- [Resilience Defense Level Runbook](../architecture/RESILIENCE_DEFENSE_LEVEL_RUNBOOK.md) - Response procedures by defense level
- [Resilience Contingency Procedures](../architecture/RESILIENCE_CONTINGENCY_PROCEDURES.md) - Emergency protocols

**Implementation Code:**
- `backend/app/api/routes/resilience.py` - Resilience API routes
- `backend/app/resilience/hub.py` - Resilience hub orchestrator
- `backend/app/resilience/crisis.py` - Crisis mode management
- `backend/app/resilience/load_shedding.py` - Load shedding implementation

**Admin Guides:**
- [Crisis Response Procedures](../admin-manual/crisis-response.md) - Administrative procedures
- [Fallback Schedule Planning](../planning/fallback-schedules.md) - Planning guide
