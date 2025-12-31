# Resilience API Documentation

**Generated:** 2025-12-30
**Session:** G2 RECON - SEARCH_PARTY Probe
**Status:** Complete endpoint reference
**Coverage:** All resilience endpoints (core + exotic)

---

## Table of Contents

1. [Overview](#overview)
2. [Health Check Endpoints](#health-check-endpoints)
3. [Tier 1 Critical Endpoints](#tier-1-critical-endpoints)
4. [Tier 2 Strategic Endpoints](#tier-2-strategic-endpoints)
5. [Tier 3 Advanced Endpoints](#tier-3-advanced-endpoints)
6. [Exotic Resilience Endpoints](#exotic-resilience-endpoints)
7. [Metrics and Monitoring](#metrics-and-monitoring)
8. [Alert Integration Guide](#alert-integration-guide)
9. [Response Payload Examples](#response-payload-examples)

---

## Overview

The Resilience API provides comprehensive health monitoring, crisis management, and advanced analysis across five tiers of system resilience:

### Core Components

| Component | Purpose | Route Prefix |
|-----------|---------|--------------|
| **Health Checks** | Liveness, readiness, detailed health | `/health/*` |
| **Tier 1 (Critical)** | System health, crisis, fallbacks, load shedding | `/resilience/*` |
| **Tier 2 (Strategic)** | Homeostasis, zones, equilibrium | `/resilience/tier2/*` |
| **Tier 3 (Advanced)** | Cognitive load, stigmergy, hub analysis | `/resilience/tier3/*` |
| **Exotic (Frontier)** | Thermodynamics, immune systems, time crystal | `/resilience/exotic/*` |

### Authorization

- **Tier 1 & 2 endpoints**: Require `admin` or `coordinator` role
- **Health/readiness checks**: Public (no auth required)
- **Crisis/fallback management**: Require explicit admin approval

---

## Health Check Endpoints

Health checks are the primary monitoring surface for orchestrators (Kubernetes, Docker) and monitoring systems.

### GET /health/live

**Liveness Probe** - Indicates if container is running and responsive.

```http
GET /health/live HTTP/1.1
```

**Response (200):**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00.000000",
  "service": "residency-scheduler"
}
```

**Use Case:** Kubernetes/Docker container restart detection
**SLA:** <100ms response time

---

### GET /health/ready

**Readiness Probe** - Checks if service can accept traffic.

```http
GET /health/ready HTTP/1.1
```

**Response (200):**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00.000000",
  "database": true,
  "redis": true
}
```

**Response (503) - Not Ready:**
```json
{
  "detail": "Service not ready - dependencies unhealthy"
}
```

**Critical Dependencies Checked:**
- PostgreSQL database connection pool
- Redis connection
- Celery task queue

**Use Case:** Load balancer traffic routing
**SLA:** <500ms response time

---

### GET /health/detailed

**Comprehensive Health Check** - Full status across all services.

```http
GET /health/detailed HTTP/1.1
```

**Response (200):**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00.000000",
  "services": {
    "database": {
      "service": "database",
      "status": "healthy",
      "response_time_ms": 12.5,
      "details": {
        "database_version": "PostgreSQL 15.3",
        "connection_pool": {
          "size": 10,
          "checked_in": 8,
          "checked_out": 2
        }
      }
    },
    "redis": {
      "service": "redis",
      "status": "healthy",
      "response_time_ms": 5.2,
      "details": {
        "version": "7.0.0",
        "memory_usage_mb": 128.5,
        "connected_clients": 5
      }
    },
    "celery": {
      "service": "celery",
      "status": "healthy",
      "response_time_ms": 45.3,
      "details": {
        "worker_count": 2,
        "active_tasks": 3,
        "queue_depth": 0
      }
    },
    "circuit_breakers": {
      "service": "circuit_breakers",
      "status": "healthy",
      "response_time_ms": 2.1,
      "details": {
        "schedulers_closed": 4,
        "schedulers_open": 0
      }
    }
  },
  "summary": {
    "total_services": 4,
    "healthy_count": 4,
    "degraded_count": 0,
    "unhealthy_count": 0,
    "avg_response_time_ms": 15.3
  }
}
```

**Services Monitored:**
- Database (connection pool, schema version)
- Redis (memory, connected clients)
- Celery (workers, task queue depth)
- Circuit Breakers (resilience safety switches)

**Use Case:** Detailed monitoring dashboards, debugging
**SLA:** <2 second response time

---

### GET /health/services/{service_name}

**Individual Service Health** - Check specific service only.

```http
GET /health/services/database HTTP/1.1
```

**Valid service_names:**
- `database`
- `redis`
- `celery`
- `circuit_breakers`

**Response (200):**
```json
{
  "service": "database",
  "status": "healthy",
  "response_time_ms": 12.5,
  "timestamp": "2024-01-15T10:30:00.000000",
  "details": {
    "database_version": "PostgreSQL 15.3",
    "connection_pool": {
      "size": 10,
      "checked_in": 8,
      "checked_out": 2
    }
  }
}
```

**Response (404):**
```json
{
  "detail": "Unknown service: invalid_service. Valid services: database, redis, celery, circuit_breakers"
}
```

---

### GET /health/history

**Health Check History** - Retrieve recent health snapshots for trend analysis.

```http
GET /health/history?limit=20 HTTP/1.1
```

**Query Parameters:**
- `limit` (int, 1-100): Number of entries to return (default: 10)

**Response (200):**
```json
{
  "count": 20,
  "limit": 20,
  "history": [
    {
      "status": "healthy",
      "timestamp": "2024-01-15T10:30:00.000000",
      "services": { ... },
      "summary": { ... }
    }
  ]
}
```

**Use Case:** Trend analysis, identifying degradation patterns
**Retention:** Last 100 checks stored in memory

---

### GET /health/metrics

**Health Metrics Summary** - Aggregated performance statistics.

```http
GET /health/metrics HTTP/1.1
```

**Response (200):**
```json
{
  "history_enabled": true,
  "history_size": 50,
  "uptime_percentage": 98.5,
  "recent_checks": 10,
  "avg_response_times_ms": {
    "database": 12.3,
    "redis": 5.7,
    "celery": 25.1
  }
}
```

**Key Metrics:**
- `uptime_percentage`: Percentage of checks with "healthy" status
- `avg_response_times_ms`: Average response time per service
- `recent_checks`: Number of recent checks in history

---

### DELETE /health/history

**Clear History** - Remove all stored health check history.

```http
DELETE /health/history HTTP/1.1
```

**Response (200):**
```json
{
  "message": "Health check history cleared",
  "timestamp": "2024-01-15T10:30:00.000000"
}
```

---

### POST /health/check

**Trigger Manual Check** - Force immediate comprehensive health check.

```http
POST /health/check HTTP/1.1
Content-Type: application/json
```

**Response (200):**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00.000000",
  "services": { ... }
}
```

---

### GET /health/status

**Simplified Status** - Minimal response for dashboards.

```http
GET /health/status HTTP/1.1
```

**Response (200):**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00.000000",
  "services_checked": 3,
  "all_healthy": true,
  "healthy_count": 3,
  "degraded_count": 0,
  "unhealthy_count": 0
}
```

---

## Tier 1 Critical Endpoints

Tier 1 endpoints manage critical system responses: health monitoring, crisis activation, fallback schedules, and load shedding.

### GET /resilience/health

**System Health Check** - Comprehensive resilience status.

```http
GET /resilience/health?start_date=2024-01-01&end_date=2024-01-31&include_contingency=false&persist=true HTTP/1.1
```

**Query Parameters:**
- `start_date` (date, optional): Analysis period start
- `end_date` (date, optional): Analysis period end
- `include_contingency` (bool): Perform N-1/N-2 analysis (slower)
- `persist` (bool): Save results to database (default: true)
- `max_faculty` (int, optional): Limit faculty records for performance
- `max_blocks` (int, optional): Limit block records for performance

**Response (200):**
```json
{
  "timestamp": "2024-01-15T10:30:00.000000",
  "overall_status": "healthy",
  "utilization": {
    "utilization_rate": 0.75,
    "level": "YELLOW",
    "buffer_remaining": 0.25,
    "wait_time_multiplier": 1.5,
    "safe_capacity": 85,
    "current_demand": 75,
    "theoretical_capacity": 100
  },
  "defense_level": "PREVENTION",
  "redundancy_status": [
    {
      "service": "inpatient",
      "status": "N+2",
      "available": 5,
      "minimum_required": 3,
      "buffer": 2
    }
  ],
  "load_shedding_level": "NORMAL",
  "active_fallbacks": [],
  "crisis_mode": false,
  "n1_pass": true,
  "n2_pass": true,
  "phase_transition_risk": "low",
  "immediate_actions": [],
  "watch_items": ["Monitor coverage during holiday"]
}
```

**Utilization Levels:**
- `GREEN` (<70%): Healthy buffer
- `YELLOW` (70-80%): Approaching threshold
- `ORANGE` (80-90%): Degraded operations
- `RED` (90-95%): Critical, cascade risk
- `BLACK` (>95%): Imminent failure

**Defense Levels:**
- `PREVENTION`: Normal operations, full preventive measures
- `CONTROL`: Monitor closely, activate safeguards
- `SAFETY_SYSTEMS`: Enhanced safety protocols active
- `CONTAINMENT`: Blast radius isolation active
- `EMERGENCY`: All non-essential systems suspended

---

### POST /resilience/crisis/activate

**Activate Crisis Mode** - Enable emergency response procedures.

```http
POST /resilience/crisis/activate HTTP/1.1
Content-Type: application/json

{
  "severity": "critical",
  "reason": "Multiple faculty TDY deployments reduce coverage to 60%"
}
```

**Request Body:**
- `severity` (enum): `minor`, `moderate`, `severe`, `critical`
- `reason` (string, 10-500 chars): Justification for activation

**Response (200):**
```json
{
  "crisis_mode": true,
  "severity": "critical",
  "actions_taken": [
    "Activated fallback schedule PANDEMIC_ESSENTIAL",
    "Reduced load shedding to ORANGE",
    "Enabled circuit breaker protection",
    "Notified stakeholders"
  ],
  "load_shedding_level": "ORANGE",
  "recovery_plan": [
    "Restore faculty availability over 2 weeks",
    "Gradually restore research/education",
    "Return to normal operations after full capacity confirmation"
  ]
}
```

**Audit Trail:**
- Event logged to `resilience_events` table with reason
- Health check persisted at activation time
- All actions captured in event metadata

---

### POST /resilience/crisis/deactivate

**Deactivate Crisis Mode** - Return to normal operations.

```http
POST /resilience/crisis/deactivate HTTP/1.1
Content-Type: application/json

{
  "reason": "All faculty restored, coverage at 95%"
}
```

**Response (200):**
```json
{
  "crisis_mode": false,
  "severity": null,
  "actions_taken": [
    "Deactivated PANDEMIC_ESSENTIAL fallback",
    "Returned load shedding to NORMAL",
    "Disabled circuit breaker protection",
    "Notified stakeholders of recovery"
  ],
  "load_shedding_level": "NORMAL",
  "recovery_plan": null
}
```

---

### GET /resilience/fallbacks

**List Fallback Schedules** - Show available contingency schedules.

```http
GET /resilience/fallbacks HTTP/1.1
```

**Response (200):**
```json
{
  "fallbacks": [
    {
      "scenario": "single_faculty_loss",
      "description": "Pre-computed schedule for 1 faculty loss (standard)",
      "is_active": false,
      "is_precomputed": true,
      "assignments_count": 342,
      "coverage_rate": 0.92,
      "services_reduced": [],
      "assumptions": [
        "1 attending physician absent",
        "Clinic capacity reduced 20%",
        "Night float coverage maintained"
      ],
      "activation_count": 2
    },
    {
      "scenario": "pcs_season_50_percent",
      "description": "PCS season with 50% personnel turnover",
      "is_active": false,
      "is_precomputed": true,
      "assignments_count": 280,
      "coverage_rate": 0.78,
      "services_reduced": ["education", "research"],
      "assumptions": [
        "50% of junior residents PCS",
        "New residents reduce productivity 30%",
        "Core clinical maintained"
      ],
      "activation_count": 0
    },
    {
      "scenario": "mass_casualty",
      "description": "Mass casualty incident response",
      "is_active": false,
      "is_precomputed": true,
      "assignments_count": 180,
      "coverage_rate": 0.60,
      "services_reduced": ["education", "research", "clinic", "admin"],
      "assumptions": [
        "All personnel available for clinical",
        "Non-clinical suspended",
        "Surge capacity activated"
      ],
      "activation_count": 0
    }
  ],
  "active_count": 0
}
```

**Pre-computed Scenarios:**
1. `single_faculty_loss`: Loss of one attending
2. `double_faculty_loss`: Loss of two attendings
3. `pcs_season_50_percent`: Seasonal transitions
4. `holiday_skeleton`: Holiday/weekend minimal staffing
5. `pandemic_essential`: Pandemic response (patient care only)
6. `mass_casualty`: Mass casualty incident
7. `weather_emergency`: Weather/facility closure

---

### POST /resilience/fallbacks/activate

**Activate Fallback Schedule** - Switch to pre-computed contingency.

```http
POST /resilience/fallbacks/activate HTTP/1.1
Content-Type: application/json

{
  "scenario": "single_faculty_loss",
  "reason": "Faculty emergency leave (medical family hardship)"
}
```

**Response (200):**
```json
{
  "success": true,
  "scenario": "single_faculty_loss",
  "assignments_count": 342,
  "coverage_rate": 0.92,
  "services_reduced": [],
  "message": "Fallback schedule activated. 342 assignments loaded, coverage 92%"
}
```

**Effects:**
- Active schedule is replaced with fallback
- All assignments transferred to fallback version
- ACGME compliance rechecked
- Event logged with reason

---

### POST /resilience/fallbacks/deactivate

**Deactivate Fallback Schedule** - Return to primary schedule.

```http
POST /resilience/fallbacks/deactivate HTTP/1.1
Content-Type: application/json

{
  "scenario": "single_faculty_loss",
  "reason": "Faculty returned, restoration in place"
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "Fallback schedule deactivated. Returned to primary schedule."
}
```

---

### GET /resilience/load-shedding

**Get Load Shedding Status** - Current load shedding level and activities.

```http
GET /resilience/load-shedding HTTP/1.1
```

**Response (200):**
```json
{
  "level": "NORMAL",
  "activities_suspended": [],
  "activities_protected": [
    "inpatient_care",
    "outpatient_clinic",
    "night_float",
    "call_coverage"
  ],
  "capacity_available": 0.85,
  "capacity_demand": 0.65
}
```

**Load Shedding Levels (Triage-Based):**
- `NORMAL`: All activities
- `YELLOW`: Suspend optional education (grand rounds, conferences)
- `ORANGE`: Also suspend admin & research
- `RED`: Also suspend core education (simulation, didactics)
- `BLACK`: Essentials only (clinical and night float)
- `CRITICAL`: Patient safety only

---

### POST /resilience/load-shedding

**Change Load Shedding Level** - Adjust response severity.

```http
POST /resilience/load-shedding HTTP/1.1
Content-Type: application/json

{
  "level": "ORANGE",
  "reason": "Faculty availability reduced 30%, implementing load shedding"
}
```

**Response (200):**
```json
{
  "level": "ORANGE",
  "activities_suspended": [
    "optional_education",
    "administration",
    "research"
  ],
  "activities_protected": [
    "inpatient_care",
    "outpatient_clinic",
    "night_float",
    "call_coverage",
    "core_education"
  ],
  "capacity_available": 0.60,
  "capacity_demand": 0.70
}
```

---

### GET /resilience/vulnerability

**N-1/N-2 Vulnerability Analysis** - Contingency compliance report.

```http
GET /resilience/vulnerability?include_fatal_pairs=true HTTP/1.1
```

**Response (200):**
```json
{
  "analyzed_at": "2024-01-15T10:30:00.000000",
  "period_start": "2024-01-01",
  "period_end": "2024-01-31",
  "n1_pass": true,
  "n2_pass": false,
  "phase_transition_risk": "high",
  "n1_vulnerabilities": [],
  "n2_fatal_pairs": [
    {
      "faculty_1": "fac-001",
      "faculty_2": "fac-003",
      "shared_coverage": ["inpatient_call", "procedures"],
      "replacement_difficulty": 0.95,
      "risk_level": "critical"
    }
  ],
  "most_critical_faculty": [
    {
      "faculty_id": "fac-001",
      "faculty_name": "PGY2-01",
      "centrality_score": 0.87,
      "services_covered": 8,
      "unique_coverage_slots": 3,
      "replacement_difficulty": 0.78,
      "risk_level": "high"
    }
  ],
  "recommended_actions": [
    "Cross-train backup for inpatient call coverage",
    "Establish formal mentorship for high-risk faculty",
    "Create redundancy for procedure coverage"
  ]
}
```

**Interpretation:**
- `n1_pass: true` = System survives loss of any single faculty member
- `n2_pass: false` = System fails if 2+ specific faculty are lost (check fatal_pairs)
- `phase_transition_risk: high` = At risk of collapse if stressors combine

---

### GET /resilience/report

**Comprehensive Resilience Report** - Full system status snapshot.

```http
GET /resilience/report HTTP/1.1
```

**Response (200):**
```json
{
  "generated_at": "2024-01-15T10:30:00.000000",
  "overall_status": "healthy",
  "summary": {
    "utilization_rate": 0.75,
    "utilization_level": "YELLOW",
    "defense_level": "PREVENTION",
    "crisis_active": false,
    "n1_compliant": true,
    "n2_compliant": false
  },
  "immediate_actions": [
    "Monitor N-2 fatal pairs for cross-training opportunity"
  ],
  "watch_items": [
    "Utilization approaching 80% threshold - monitor closely",
    "PCS season starting - staffing changes expected"
  ],
  "components": {
    "utilization": { ... },
    "redundancy": { ... },
    "vulnerability": { ... },
    "fallbacks": { ... }
  }
}
```

---

### GET /resilience/history/health

**Health Check History** - Historical health snapshots.

```http
GET /resilience/history/health?page=1&page_size=10 HTTP/1.1
```

**Query Parameters:**
- `page` (int): Page number (1-indexed)
- `page_size` (int, 1-100): Results per page

**Response (200):**
```json
{
  "items": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "timestamp": "2024-01-15T10:30:00.000000",
      "overall_status": "healthy",
      "utilization_rate": 0.75,
      "utilization_level": "YELLOW",
      "defense_level": "PREVENTION",
      "n1_pass": true,
      "n2_pass": false,
      "crisis_mode": false
    }
  ],
  "total": 256,
  "page": 1,
  "page_size": 10
}
```

---

### GET /resilience/history/events

**Resilience Event Audit Log** - All state changes and actions.

```http
GET /resilience/history/events?page=1&page_size=10 HTTP/1.1
```

**Response (200):**
```json
{
  "items": [
    {
      "id": "789e1234-a12b-34c5-d678-901e23f4g5h6",
      "timestamp": "2024-01-15T09:15:00.000000",
      "event_type": "fallback_activated",
      "severity": "severe",
      "reason": "Faculty emergency leave",
      "triggered_by": "user:admin-001"
    },
    {
      "id": "abc1234d-e5f6-789a-bcde-f012g345h678",
      "timestamp": "2024-01-14T14:30:00.000000",
      "event_type": "load_shedding_activated",
      "severity": "moderate",
      "reason": "Utilization exceeded 85%",
      "triggered_by": "system:scheduled_task"
    }
  ],
  "total": 48,
  "page": 1,
  "page_size": 10
}
```

**Event Types:**
- `health_check`: Periodic health snapshot
- `crisis_activated`: Crisis mode enabled
- `crisis_deactivated`: Crisis mode disabled
- `fallback_activated`: Fallback schedule loaded
- `fallback_deactivated`: Fallback schedule unloaded
- `load_shedding_activated`: Load shedding level changed
- `load_shedding_deactivated`: Load shedding disabled
- `defense_level_changed`: Defense posture changed
- `threshold_exceeded`: Critical utilization exceeded
- `n1_violation`: N-1 contingency failed
- `n2_violation`: N-2 contingency failed

---

### GET /resilience/mtf-compliance

**Iron Dome Military Medical Facility Compliance** - DRRS/Mission capability assessment.

```http
GET /resilience/mtf-compliance HTTP/1.1
```

**Response (200):**
```json
{
  "drrs_category": "C2",
  "mission_capability": "Capable of conducting primary mission with minor limitations",
  "personnel_rating": "P2",
  "capability_rating": "S2",
  "circuit_breaker": {
    "status": "CLOSED",
    "utilization": 0.75,
    "next_check": "2024-01-16T00:00:00.000000"
  },
  "executive_summary": "MTF is mission capable with good staffing and resource availability",
  "deficiencies": [],
  "mfrs_generated": 0,
  "rffs_generated": 0,
  "iron_dome_status": "green",
  "severity": "healthy"
}
```

**DRRS Categories (Medical Readiness):**
- `C1`: Not operationally capable
- `C2`: Capable with major limitations
- `C3`: Capable with minor limitations
- `C4`: Fully capable

**Personnel Ratings:**
- `P1`: Insufficient personnel
- `P2`: Personnel with significant gaps
- `P3`: Personnel with minor gaps
- `P4`: Personnel available, fully staffed

---

## Tier 2 Strategic Endpoints

Tier 2 endpoints implement strategic-level resilience: homeostasis (feedback loops), blast radius containment, and equilibrium analysis.

### GET /resilience/tier2/homeostasis

**Homeostasis Status** - Feedback loop health across system.

```http
GET /resilience/tier2/homeostasis HTTP/1.1
```

**Response (200):**
```json
{
  "timestamp": "2024-01-15T10:30:00.000000",
  "overall_state": "homeostasis",
  "feedback_loops_healthy": 4,
  "feedback_loops_deviating": 1,
  "active_corrections": 0,
  "positive_feedback_risks": 0,
  "average_allostatic_load": 25.5,
  "recommendations": [
    "Monitor coverage rate - approaching threshold"
  ],
  "feedback_loops": [
    {
      "loop_name": "coverage_rate",
      "setpoint": {
        "name": "coverage_rate",
        "description": "Fraction of scheduled slots filled",
        "target_value": 0.95,
        "tolerance": 0.05,
        "unit": "ratio",
        "is_critical": true
      },
      "current_value": 0.92,
      "deviation": -0.03,
      "deviation_severity": "minor",
      "consecutive_deviations": 2,
      "trend_direction": "stable",
      "is_improving": false,
      "last_checked": "2024-01-15T10:30:00.000000",
      "total_corrections": 1
    }
  ],
  "positive_risks": []
}
```

**Allostatic States:**
- `homeostasis`: Within normal parameters
- `allostasis`: Compensating but stable
- `allostatic_load`: Multiple compensations active
- `allostatic_overload`: System overwhelmed, risk of failure

---

### POST /resilience/tier2/homeostasis/check

**Check Homeostasis** - Evaluate system against setpoints.

```http
POST /resilience/tier2/homeostasis/check HTTP/1.1
Content-Type: application/json

{
  "metrics": {
    "coverage_rate": 0.92,
    "faculty_utilization": 0.78,
    "nights_per_month": 4.2
  }
}
```

**Response (200):**
```json
{
  "timestamp": "2024-01-15T10:30:00.000000",
  "overall_state": "homeostasis",
  "feedback_loops_healthy": 4,
  "feedback_loops_deviating": 1,
  "active_corrections": 0,
  "positive_feedback_risks": 0,
  "average_allostatic_load": 25.5,
  "recommendations": [
    "Monitor coverage rate - approaching threshold"
  ]
}
```

---

### POST /resilience/tier2/allostasis/calculate

**Calculate Allostatic Load** - Measure cumulative stress on entity.

```http
POST /resilience/tier2/allostasis/calculate HTTP/1.1
Content-Type: application/json

{
  "entity_id": "fac-001",
  "entity_type": "faculty",
  "consecutive_weekend_calls": 2,
  "nights_past_month": 8,
  "schedule_changes_absorbed": 3,
  "holidays_worked_this_year": 2,
  "overtime_hours_month": 12.5,
  "coverage_gap_responses": 4,
  "cross_coverage_events": 2
}
```

**Response (200):**
```json
{
  "entity_id": "fac-001",
  "entity_type": "faculty",
  "calculated_at": "2024-01-15T10:30:00.000000",
  "consecutive_weekend_calls": 2,
  "nights_past_month": 8,
  "schedule_changes_absorbed": 3,
  "holidays_worked_this_year": 2,
  "overtime_hours_month": 12.5,
  "coverage_gap_responses": 4,
  "cross_coverage_events": 2,
  "acute_stress_score": 45.2,
  "chronic_stress_score": 38.6,
  "total_allostatic_load": 83.8,
  "state": "allostatic_load",
  "risk_level": "high"
}
```

**Allostatic Load Interpretation:**
- <20: Minimal stress (homeostasis)
- 20-50: Moderate compensation (allostasis)
- 50-80: Heavy load, at risk (allostatic_load)
- >80: Overload, intervention needed (allostatic_overload)

---

### GET /resilience/tier2/zones

**List Scheduling Zones** - All blast radius containment zones.

```http
GET /resilience/tier2/zones HTTP/1.1
```

**Response (200):**
```json
{
  "zones": [
    {
      "id": "zone-001",
      "name": "Inpatient-A",
      "zone_type": "inpatient",
      "description": "Inpatient ward A coverage",
      "services": ["ward_coverage", "night_float"],
      "minimum_coverage": 2,
      "optimal_coverage": 3,
      "priority": 8,
      "status": "green",
      "containment_level": "soft",
      "borrowing_limit": 1,
      "lending_limit": 2,
      "is_active": true
    }
  ],
  "total": 6
}
```

**Zone Types:**
- `inpatient`: Inpatient ward coverage
- `outpatient`: Clinic/outpatient coverage
- `education`: Educational services
- `research`: Research programs
- `administrative`: Administrative functions
- `on_call`: Call coverage and night float

---

### GET /resilience/tier2/zones/report

**Blast Radius Containment Report** - Zone health and isolation status.

```http
GET /resilience/tier2/zones/report HTTP/1.1
```

**Response (200):**
```json
{
  "generated_at": "2024-01-15T10:30:00.000000",
  "total_zones": 6,
  "zones_healthy": 5,
  "zones_degraded": 1,
  "zones_critical": 0,
  "containment_active": false,
  "containment_level": "none",
  "zones_isolated": 0,
  "active_borrowing_requests": 2,
  "pending_borrowing_requests": 1,
  "zone_reports": [
    {
      "zone_id": "zone-001",
      "zone_name": "Inpatient-A",
      "zone_type": "inpatient",
      "checked_at": "2024-01-15T10:30:00.000000",
      "status": "green",
      "containment_level": "soft",
      "is_self_sufficient": true,
      "has_surplus": true,
      "available_faculty": 3,
      "minimum_required": 2,
      "optimal_required": 3,
      "capacity_ratio": 1.5,
      "faculty_borrowed": 0,
      "faculty_lent": 1,
      "net_borrowing": -1,
      "active_incidents": 0,
      "services_affected": [],
      "recommendations": []
    }
  ],
  "recommendations": [
    "Zone Clinic has reduced capacity - monitor for degradation"
  ]
}
```

**Zone Status Levels:**
- `green`: Self-sufficient, optimal capacity
- `yellow`: Approaching minimum, may borrow
- `orange`: Below minimum, borrowing active
- `red`: Critical, full containment active
- `black`: Failed, no contingency

---

### POST /resilience/tier2/stress

**Apply System Stress** - Simulate demand surge or faculty loss.

```http
POST /resilience/tier2/stress HTTP/1.1
Content-Type: application/json

{
  "stress_type": "faculty_loss",
  "description": "Two faculty unexpectedly unavailable for 2 weeks",
  "magnitude": 0.25,
  "duration_days": 14,
  "capacity_impact": -0.20,
  "demand_impact": 0.15,
  "is_acute": true,
  "is_reversible": true
}
```

**Response (200):**
```json
{
  "id": "stress-001",
  "stress_type": "faculty_loss",
  "description": "Two faculty unexpectedly unavailable for 2 weeks",
  "magnitude": 0.25,
  "duration_days": 14,
  "capacity_impact": -0.20,
  "demand_impact": 0.15,
  "applied_at": "2024-01-15T10:30:00.000000",
  "is_active": true
}
```

**Stress Types:**
- `faculty_loss`: Unexpected faculty unavailability
- `demand_surge`: Unexpected demand increase
- `quality_pressure`: External pressure on quality metrics
- `time_compression`: Reduced available time per case
- `resource_scarcity`: Limited resources or equipment
- `external_pressure`: External regulatory or operational pressure

---

### POST /resilience/tier2/compensation

**Initiate Compensation Response** - Activate coping mechanism.

```http
POST /resilience/tier2/compensation HTTP/1.1
Content-Type: application/json

{
  "stress_id": "stress-001",
  "compensation_type": "cross_coverage",
  "description": "Redistributing coverage across available faculty",
  "magnitude": 0.18,
  "effectiveness": 0.85,
  "sustainability_days": 14,
  "immediate_cost": 0.0,
  "hidden_cost": 8.5
}
```

**Response (200):**
```json
{
  "id": "comp-001",
  "stress_id": "stress-001",
  "compensation_type": "cross_coverage",
  "description": "Redistributing coverage across available faculty",
  "compensation_magnitude": 0.18,
  "effectiveness": 0.85,
  "initiated_at": "2024-01-15T10:30:00.000000",
  "is_active": true
}
```

**Compensation Types:**
- `overtime`: Extended work hours
- `cross_coverage`: Cross-trained coverage
- `deferred_leave`: Postpone planned leave
- `service_reduction`: Reduce service scope
- `efficiency_gain`: Process improvements
- `backup_activation`: Activate backup personnel
- `quality_trade`: Accept lower quality metrics temporarily

---

### GET /resilience/tier2/equilibrium

**Equilibrium Analysis Report** - Balance of capacity vs. demand.

```http
GET /resilience/tier2/equilibrium HTTP/1.1
```

**Response (200):**
```json
{
  "generated_at": "2024-01-15T10:30:00.000000",
  "current_equilibrium_state": "stable",
  "current_capacity": 85.0,
  "current_demand": 72.5,
  "current_coverage_rate": 0.85,
  "active_stresses": [
    {
      "id": "stress-001",
      "stress_type": "faculty_loss",
      "description": "Two faculty unavailable",
      "magnitude": 0.25,
      "duration_days": 14,
      "capacity_impact": -0.20,
      "demand_impact": 0.15,
      "applied_at": "2024-01-15T10:30:00.000000",
      "is_active": true
    }
  ],
  "total_stress_magnitude": 0.25,
  "active_compensations": [
    {
      "id": "comp-001",
      "stress_id": "stress-001",
      "compensation_type": "cross_coverage",
      "description": "Redistributing coverage",
      "compensation_magnitude": 0.18,
      "effectiveness": 0.85,
      "initiated_at": "2024-01-15T10:30:00.000000",
      "is_active": true
    }
  ],
  "total_compensation_magnitude": 0.18,
  "compensation_debt": 2.3,
  "sustainability_score": 0.78,
  "days_until_equilibrium": 14,
  "days_until_exhaustion": 45,
  "recommendations": [
    "Monitor compensation debt - sustainable for 45 days only"
  ]
}
```

**Equilibrium States:**
- `stable`: Capacity > demand, sustainable
- `compensating`: Using coping mechanisms, temporary
- `stressed`: At limit, high burnout risk
- `unsustainable`: Degrading rapidly, intervention needed
- `critical`: Imminent collapse, emergency response required

---

### GET /resilience/tier2/status

**Tier 2 Status Summary** - Combined homeostasis, zones, equilibrium.

```http
GET /resilience/tier2/status HTTP/1.1
```

**Response (200):**
```json
{
  "generated_at": "2024-01-15T10:30:00.000000",
  "homeostasis_state": "homeostasis",
  "feedback_loops_healthy": 4,
  "feedback_loops_deviating": 1,
  "average_allostatic_load": 25.5,
  "positive_feedback_risks": 0,
  "total_zones": 6,
  "zones_healthy": 5,
  "zones_critical": 0,
  "containment_active": false,
  "containment_level": "none",
  "equilibrium_state": "stable",
  "current_coverage_rate": 0.85,
  "compensation_debt": 0.0,
  "sustainability_score": 0.95,
  "tier2_status": "healthy",
  "recommendations": []
}
```

---

## Tier 3 Advanced Endpoints

Tier 3 endpoints implement advanced intelligence: cognitive load management, stigmergy (collective behavior), and hub analysis (network criticality).

### POST /resilience/tier3/cognitive/decision

**Create Scheduling Decision** - Track complex decisions with cognitive cost.

```http
POST /resilience/tier3/cognitive/decision HTTP/1.1
Content-Type: application/json

{
  "category": "swap",
  "complexity": "complex",
  "description": "Request swap between PGY2 residents for vacation conflict",
  "options": ["approve_swap", "deny_swap", "defer_to_pd"],
  "recommended_option": "approve_swap",
  "safe_default": "defer_to_pd",
  "is_urgent": false
}
```

**Response (200):**
```json
{
  "decision_id": "dec-001",
  "category": "swap",
  "complexity": "complex",
  "description": "Request swap between PGY2 residents",
  "options": ["approve_swap", "deny_swap", "defer_to_pd"],
  "recommended_option": "approve_swap",
  "has_safe_default": true,
  "is_urgent": false,
  "estimated_cognitive_cost": 25.5
}
```

**Decision Complexity:**
- `trivial`: <5 cognitive cost
- `simple`: 5-15 cognitive cost
- `moderate`: 15-30 cognitive cost
- `complex`: 30-50 cognitive cost
- `strategic`: >50 cognitive cost

---

### GET /resilience/tier3/cognitive/queue

**Decision Queue Status** - Pending decisions and cognitive load.

```http
GET /resilience/tier3/cognitive/queue HTTP/1.1
```

**Response (200):**
```json
{
  "total_pending": 8,
  "by_complexity": {
    "trivial": 2,
    "simple": 3,
    "moderate": 2,
    "complex": 1,
    "strategic": 0
  },
  "by_category": {
    "swap": 4,
    "leave": 2,
    "coverage": 1,
    "override": 1
  },
  "urgent_count": 1,
  "can_auto_decide": 5,
  "oldest_pending": "2024-01-15T08:00:00.000000",
  "estimated_cognitive_cost": 125.5,
  "recommendations": [
    "Decision queue contains 1 urgent decision - prioritize swap approval"
  ]
}
```

---

### POST /resilience/tier3/stigmergy/preference

**Record Preference Trail** - Capture faculty scheduling preferences.

```http
POST /resilience/tier3/stigmergy/preference HTTP/1.1
Content-Type: application/json

{
  "faculty_id": "fac-001",
  "trail_type": "preference",
  "slot_type": "night_float",
  "strength": 0.8
}
```

**Response (200):**
```json
{
  "trail_id": "trail-001",
  "faculty_id": "fac-001",
  "trail_type": "preference",
  "strength": 0.8,
  "strength_category": "strong",
  "slot_type": "night_float",
  "reinforcement_count": 5,
  "age_days": 12.5
}
```

**Trail Types:**
- `preference`: Likes this assignment
- `avoidance`: Dislikes this assignment
- `swap_affinity`: Works well with specific faculty
- `workload`: Capacity limits
- `sequence`: Preferred assignment sequences

**Trail Strength Categories:**
- `very_weak`: <0.2
- `weak`: 0.2-0.4
- `moderate`: 0.4-0.6
- `strong`: 0.6-0.8
- `very_strong`: >0.8

---

### GET /resilience/tier3/stigmergy/status

**Stigmergy System Status** - Collective behavior trail status.

```http
GET /resilience/tier3/stigmergy/status HTTP/1.1
```

**Response (200):**
```json
{
  "timestamp": "2024-01-15T10:30:00.000000",
  "total_trails": 234,
  "active_trails": 189,
  "trails_by_type": {
    "preference": 95,
    "avoidance": 58,
    "swap_affinity": 42,
    "workload": 28,
    "sequence": 11
  },
  "average_strength": 0.62,
  "average_age_days": 18.3,
  "evaporation_debt_hours": 45.2,
  "popular_slots": [
    "clinic_tuesday_morning",
    "elective_procedure",
    "conference_friday"
  ],
  "unpopular_slots": [
    "night_float_weekend",
    "holiday_coverage",
    "weekend_call"
  ],
  "strong_swap_pairs": 15,
  "recommendations": [
    "High evaporation debt - consider reinforcement of popular assignments"
  ]
}
```

---

### GET /resilience/tier3/hubs/top

**Top Hub Faculty** - Most critical network positions.

```http
GET /resilience/tier3/hubs/top?limit=10 HTTP/1.1
```

**Response (200):**
```json
{
  "hubs": [
    {
      "faculty_id": "fac-001",
      "faculty_name": "PGY3-01",
      "composite_score": 0.92,
      "risk_level": "critical",
      "is_hub": true,
      "degree_centrality": 0.95,
      "betweenness_centrality": 0.88,
      "services_covered": 12,
      "unique_services": 5,
      "replacement_difficulty": 0.94
    }
  ],
  "count": 1
}
```

**Risk Levels:**
- `low`: Easily replaced
- `moderate`: Some coverage gap if lost
- `high`: Significant impact if lost
- `critical`: Major services at risk
- `catastrophic`: Program-wide impact

---

### GET /resilience/tier3/hubs/distribution

**Hub Distribution Report** - Network vulnerability summary.

```http
GET /resilience/tier3/hubs/distribution HTTP/1.1
```

**Response (200):**
```json
{
  "generated_at": "2024-01-15T10:30:00.000000",
  "total_faculty": 24,
  "total_hubs": 3,
  "catastrophic_hubs": 0,
  "critical_hubs": 1,
  "high_risk_hubs": 2,
  "hub_concentration": 0.35,
  "single_points_of_failure": 5,
  "average_hub_score": 0.68,
  "services_with_single_provider": [
    "pediatric_cardiology_procedures",
    "quality_improvement_lead"
  ],
  "services_with_dual_coverage": [
    "inpatient_call",
    "night_float",
    "clinic_coverage"
  ],
  "well_covered_services": [
    "education",
    "research",
    "admin"
  ],
  "recommendations": [
    "Cross-train backup for pediatric cardiology procedures (single provider)",
    "Develop redundancy for QI lead role"
  ]
}
```

---

### GET /resilience/tier3/status

**Tier 3 Status Summary** - Cognitive, stigmergy, hub status combined.

```http
GET /resilience/tier3/status HTTP/1.1
```

**Response (200):**
```json
{
  "generated_at": "2024-01-15T10:30:00.000000",
  "pending_decisions": 8,
  "urgent_decisions": 1,
  "estimated_cognitive_cost": 125.5,
  "can_auto_decide": 5,
  "total_trails": 234,
  "active_trails": 189,
  "average_strength": 0.62,
  "popular_slots": [
    "clinic_tuesday_morning",
    "elective_procedure"
  ],
  "unpopular_slots": [
    "night_float_weekend",
    "holiday_coverage"
  ],
  "total_hubs": 3,
  "catastrophic_hubs": 0,
  "critical_hubs": 1,
  "active_protection_plans": 1,
  "pending_cross_training": 3,
  "tier3_status": "healthy",
  "issues": [],
  "recommendations": [
    "Process 1 urgent decision to reduce cognitive load"
  ]
}
```

---

## Exotic Resilience Endpoints

Exotic endpoints provide frontier-level resilience analysis: thermodynamics (entropy, phase transitions), immune systems, and time crystal (periodicity, anti-churn).

### POST /resilience/exotic/thermodynamics/entropy

**Schedule Entropy Analysis** - Information-theoretic schedule assessment.

```http
POST /resilience/exotic/thermodynamics/entropy HTTP/1.1
Content-Type: application/json

{
  "schedule_id": "sched-001",
  "start_date": "2024-01-01",
  "end_date": "2024-01-31"
}
```

**Response (200):**
```json
{
  "person_entropy": 3.45,
  "rotation_entropy": 2.98,
  "time_entropy": 2.76,
  "joint_entropy": 8.12,
  "mutual_information": 0.85,
  "normalized_entropy": 0.68,
  "entropy_production_rate": 0.023,
  "interpretation": "Schedule shows moderate entropy with good distribution. Faculty assignments are relatively balanced without over-concentration.",
  "recommendations": [
    "Consider increasing rotation variety for some faculty",
    "Monitor entropy production rate - stable and healthy"
  ]
}
```

**Entropy Interpretation:**
- High entropy: Good diversity, well-distributed
- Low entropy: Clustered, uneven distribution
- Normalized entropy: Ratio to maximum possible (0-1)
- Entropy production: Rate of disorder generation

---

### POST /resilience/exotic/thermodynamics/phase-transition

**Phase Transition Detection** - Critical point analysis.

```http
POST /resilience/exotic/thermodynamics/phase-transition HTTP/1.1
Content-Type: application/json

{
  "schedule_id": "sched-001",
  "days_lookback": 60
}
```

**Response (200):**
```json
{
  "is_approaching_transition": true,
  "critical_point_estimate": "2024-02-15T00:00:00.000000",
  "transition_probability": 0.72,
  "latent_heat_analogy": 23.4,
  "control_parameter_value": 0.88,
  "control_parameter_critical": 0.92,
  "variance_increasing": true,
  "relaxation_time_hours": 52.3,
  "immediate_actions": [
    "Increase faculty availability to delay transition",
    "Reduce non-essential activities before critical point"
  ]
}
```

---

### POST /resilience/exotic/immune/assess

**Schedule Immune System Assessment** - Anomaly detection capability.

```http
POST /resilience/exotic/immune/assess HTTP/1.1
Content-Type: application/json

{
  "schedule_id": "sched-001",
  "detection_sensitivity": 0.8
}
```

**Response (200):**
```json
{
  "immune_strength": 0.85,
  "anomalies_detected": 3,
  "anomaly_details": [
    {
      "type": "coverage_spike",
      "location": "inpatient_ward",
      "severity": "minor",
      "recommended_action": "monitor"
    }
  ],
  "self_tolerance_violations": 0,
  "false_positive_rate": 0.05,
  "detection_latency_hours": 4.2,
  "health_summary": "Immune system is functioning well with appropriate sensitivity"
}
```

---

### POST /resilience/exotic/time-crystal/rigidity

**Schedule Rigidity Analysis** - Anti-churn and stability assessment.

```http
POST /resilience/exotic/time-crystal/rigidity HTTP/1.1
Content-Type: application/json

{
  "schedule_id": "sched-001",
  "period_start": "2024-01-01",
  "period_end": "2024-01-31"
}
```

**Response (200):**
```json
{
  "rigidity_score": 0.78,
  "rigidity_interpretation": "Schedule shows good stability with minimal churn",
  "changes_this_period": 12,
  "changes_per_day": 0.39,
  "persistence_ratio": 0.92,
  "period_boundaries_stable": true,
  "subharmonic_score": 0.82,
  "stroboscopic_order": 4,
  "recommendations": [
    "Rigidity is healthy - maintain current stability level",
    "Clear periodic structure detected at 7-day and 14-day cycles"
  ]
}
```

**Rigidity Score Interpretation:**
- 0.0-0.3: High churn, unstable
- 0.3-0.6: Moderate churn, some instability
- 0.6-0.8: Good stability, low churn
- 0.8-1.0: Excellent stability, minimal changes

---

## Metrics and Monitoring

### Key Monitoring Metrics

| Metric | Source | SLA |
|--------|--------|-----|
| **Utilization Rate** | Resilience health check | <85% (GREEN/YELLOW) |
| **N-1 Compliance** | Vulnerability analysis | Pass (100%) |
| **N-2 Compliance** | Vulnerability analysis | Pass (100%) |
| **Defense Level** | Crisis response | PREVENTION or CONTROL |
| **Coverage Rate** | Homeostasis feedback loop | >95% |
| **Allostatic Load** | Faculty stress tracking | <50 (healthy) |
| **Zone Health** | Blast radius monitoring | >50% GREEN status |
| **Equilibrium State** | Le Chatelier analysis | STABLE or COMPENSATING |
| **Hub Concentration** | Network analysis | <0.5 (well-distributed) |
| **Entropy** | Thermodynamics | 0.5-0.8 (healthy diversity) |

### Alert Triggers

| Alert | Trigger | Severity | Action |
|-------|---------|----------|--------|
| **Utilization Critical** | >90% | CRITICAL | Activate load shedding |
| **N-1 Violation** | Failed contingency | CRITICAL | Crisis mode |
| **Defense Escalation** | Level up | MAJOR | Review status, take action |
| **Zone Degradation** | Status RED | MAJOR | Enable containment |
| **Equilibrium Shift** | State changes | MODERATE | Monitor and plan |
| **Hub Loss** | CATASTROPHIC risk | CRITICAL | Activate protection plan |
| **Phase Transition** | Approaching | MODERATE | Preventive measures |

---

## Alert Integration Guide

### Webhook Integration

The resilience system can trigger webhooks on state changes:

```bash
# Configure webhook in environment
RESILIENCE_WEBHOOK_URL=https://alerts.example.com/resilience
RESILIENCE_WEBHOOK_SECRET=<32-char-secret>
```

### Webhook Payload

```json
{
  "timestamp": "2024-01-15T10:30:00.000000",
  "event_type": "health_check",
  "severity": "major",
  "reason": "Utilization exceeded 85% threshold",
  "triggered_by": "scheduled_task",
  "previous_state": {
    "overall_status": "healthy",
    "utilization_rate": 0.82
  },
  "new_state": {
    "overall_status": "degraded",
    "utilization_rate": 0.87
  },
  "immediate_actions": [
    "Activate load shedding YELLOW",
    "Notify coordinators"
  ]
}
```

### Integration Examples

**Datadog/New Relic:**
```python
# In app.core.config
MONITORING_INTEGRATION = "datadog"
DATADOG_API_KEY = os.getenv("DATADOG_API_KEY")
```

**Slack Notifications:**
```python
# Configured via webhook
# Sends alerts to #resilience-alerts channel
```

**PagerDuty Escalation:**
```python
# CRITICAL events trigger PagerDuty incident
# Assigned to on-call coordinator
```

---

## Response Payload Examples

### Complete Health Check Response

```json
{
  "timestamp": "2024-01-15T10:30:00.000000",
  "overall_status": "degraded",
  "utilization": {
    "utilization_rate": 0.87,
    "level": "ORANGE",
    "buffer_remaining": 0.13,
    "wait_time_multiplier": 2.1,
    "safe_capacity": 70,
    "current_demand": 87,
    "theoretical_capacity": 100
  },
  "defense_level": "CONTROL",
  "redundancy_status": [
    {
      "service": "inpatient",
      "status": "N+1",
      "available": 4,
      "minimum_required": 3,
      "buffer": 1
    },
    {
      "service": "clinic",
      "status": "N+0",
      "available": 2,
      "minimum_required": 2,
      "buffer": 0
    }
  ],
  "load_shedding_level": "YELLOW",
  "active_fallbacks": [],
  "crisis_mode": false,
  "n1_pass": true,
  "n2_pass": false,
  "phase_transition_risk": "medium",
  "immediate_actions": [
    "Activate load shedding YELLOW - suspend optional education",
    "Review N-2 fatal pairs for cross-training",
    "Increase monitoring frequency to every 4 hours"
  ],
  "watch_items": [
    "Two faculty on medical leave - monitor return dates",
    "Utilization sustained at 87% - trending concerning",
    "Clinic coverage at N+0 - no buffer for additional losses"
  ]
}
```

### Hub Protection Plan Example

```json
{
  "plan_id": "plan-001",
  "hub_faculty_id": "fac-001",
  "hub_faculty_name": "PGY3-01",
  "period_start": "2024-01-15",
  "period_end": "2024-03-15",
  "reason": "Critical hub - implementing protection plan",
  "workload_reduction": 0.3,
  "backup_assigned": true,
  "backup_faculty_ids": ["fac-005", "fac-012"],
  "status": "active",
  "protective_measures": [
    "30% workload reduction during protection period",
    "Backup faculty PGY3-02 and PGY2-04 shadowing critical procedures",
    "Cross-training sessions scheduled weekly",
    "Mentorship doubled for backup faculty"
  ],
  "recovery_milestones": [
    "2024-01-31: Backup faculty can cover 50% of procedures",
    "2024-02-15: Backup faculty can cover 75% independently",
    "2024-03-15: Plan review, consider extensions or graduation"
  ]
}
```

---

## Summary

The Resilience API provides comprehensive monitoring and control across five tiers:

1. **Health Checks**: Liveness, readiness, detailed health for all dependencies
2. **Tier 1 Critical**: Crisis management, fallbacks, load shedding, contingency
3. **Tier 2 Strategic**: Homeostasis feedback loops, zone containment, equilibrium
4. **Tier 3 Advanced**: Cognitive load, collective behavior, network analysis
5. **Exotic Frontier**: Thermodynamics, immune systems, time crystal periodicity

All endpoints support:
- Complete audit trails and event history
- Real-time alerts and webhooks
- Persisted state for post-incident review
- Role-based access control
- Comprehensive error handling

For integration guidance, see:
- `/docs` - OpenAPI specification
- `docs/monitoring/RESILIENCE_MONITORING.md` - Monitoring setup
- `docs/architecture/cross-disciplinary-resilience.md` - Resilience concepts

