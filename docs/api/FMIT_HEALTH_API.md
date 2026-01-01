# FMIT Health API

The FMIT (Faculty Member In Training) Health API provides comprehensive monitoring and analysis for faculty scheduling, swap management, and coverage tracking.

## Base URL

```
/fmit
```

## Endpoints Overview

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/fmit/health` | GET | Overall FMIT subsystem health |
| `/fmit/status` | GET | Detailed system status |
| `/fmit/metrics` | GET | FMIT-specific metrics |
| `/fmit/coverage` | GET | Coverage report by date range |
| `/fmit/coverage/gaps` | GET | Detect coverage gaps |
| `/fmit/coverage/suggestions` | GET | Auto-suggested solutions |
| `/fmit/coverage/forecast` | GET | Predict future gaps |
| `/fmit/alerts/summary` | GET | Alert summary by severity |

---

## Health Status

**Purpose:** Get overall FMIT subsystem health with issues and recommendations.

```http
GET /fmit/health
```

### Response

```json
{
  "timestamp": "2024-01-15T10:30:00.000000",
  "status": "healthy",
  "total_swaps_this_month": 25,
  "pending_swap_requests": 3,
  "active_conflict_alerts": 2,
  "coverage_percentage": 94.5,
  "issues": [],
  "recommendations": []
}
```

### Status Values
- `healthy`: All systems operating normally
- `degraded`: Some issues detected (pending swaps > 10, coverage < 85%, alerts > 5)
- `critical`: Severe issues (critical alerts > 5, coverage < 70%)

### Issue Examples
```json
{
  "issues": [
    "15 pending swap requests require attention",
    "Coverage at 82.5% (target: 90%+)",
    "3 critical alerts require immediate attention"
  ],
  "recommendations": [
    "Review and process pending swap requests",
    "Review uncovered FMIT slots and assign faculty",
    "Address critical conflicts immediately"
  ]
}
```

---

## Detailed Status

**Purpose:** Comprehensive swap and alert statistics.

```http
GET /fmit/status
```

### Response

```json
{
  "timestamp": "2024-01-15T10:30:00.000000",
  "pending_swaps": 3,
  "approved_swaps": 5,
  "executed_swaps": 45,
  "rejected_swaps": 2,
  "cancelled_swaps": 1,
  "rolled_back_swaps": 0,
  "active_alerts": 5,
  "new_alerts": 2,
  "acknowledged_alerts": 3,
  "resolved_alerts": 50,
  "critical_alerts": 1,
  "warning_alerts": 3,
  "info_alerts": 1,
  "recent_swap_activity": [
    {
      "id": "swap-uuid-1",
      "status": "executed",
      "swap_type": "one_to_one",
      "requested_at": "2024-01-15T09:00:00.000000",
      "source_faculty_id": "person-uuid-1",
      "target_faculty_id": "person-uuid-2"
    }
  ],
  "recent_alerts": [
    {
      "id": "alert-uuid-1",
      "severity": "warning",
      "status": "new",
      "conflict_type": "double_booking",
      "created_at": "2024-01-15T08:30:00.000000",
      "faculty_id": "person-uuid-3"
    }
  ]
}
```

---

## FMIT Metrics

**Purpose:** Detailed metrics with approval rates and processing times.

```http
GET /fmit/metrics
```

### Response

```json
{
  "timestamp": "2024-01-15T10:30:00.000000",
  "total_swaps_this_month": 25,
  "pending_swap_requests": 3,
  "active_conflict_alerts": 5,
  "coverage_percentage": 94.5,
  "swap_approval_rate": 92.5,
  "average_swap_processing_time_hours": 4.2,
  "alert_resolution_rate": 85.0,
  "critical_alerts_count": 1,
  "one_to_one_swaps_count": 20,
  "absorb_swaps_count": 5
}
```

### Metric Descriptions

| Metric | Description |
|--------|-------------|
| `swap_approval_rate` | Percentage of completed swaps that were approved |
| `average_swap_processing_time_hours` | Average time from request to execution |
| `alert_resolution_rate` | Percentage of alerts resolved this month |
| `one_to_one_swaps_count` | Direct faculty exchanges |
| `absorb_swaps_count` | One faculty absorbs another's shift |

---

## Coverage Report

**Purpose:** Week-by-week coverage analysis with faculty assignments.

```http
GET /fmit/coverage?start_date=2024-01-01&end_date=2024-01-31&period=weekly
```

### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `start_date` | date | today | Start of date range |
| `end_date` | date | start + 30 days | End of date range |
| `period` | string | weekly | Grouping: `daily`, `weekly`, `monthly` |

### Response

```json
{
  "start_date": "2024-01-01",
  "end_date": "2024-01-31",
  "total_weeks": 5,
  "overall_coverage_percentage": 92.5,
  "weeks": [
    {
      "week_start": "2024-01-01",
      "total_fmit_slots": 20,
      "covered_slots": 19,
      "uncovered_slots": 1,
      "coverage_percentage": 95.0,
      "faculty_assigned": ["Dr. Smith", "Dr. Jones", "Dr. Williams"]
    }
  ]
}
```

---

## Coverage Gaps

**Purpose:** Detect and classify all coverage gaps by severity.

```http
GET /fmit/coverage/gaps?start_date=2024-01-01&end_date=2024-02-28&severity_filter=critical
```

### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `start_date` | date | today | Start of date range |
| `end_date` | date | start + 60 days | End of date range |
| `severity_filter` | string | null | Filter: `critical`, `high`, `medium`, `low` |

### Response

```json
{
  "timestamp": "2024-01-15T10:30:00.000000",
  "total_gaps": 8,
  "critical_gaps": 2,
  "high_priority_gaps": 3,
  "medium_priority_gaps": 2,
  "low_priority_gaps": 1,
  "gaps_by_period": {
    "daily": 1,
    "weekly": 3,
    "monthly": 3,
    "future": 1
  },
  "gaps": [
    {
      "gap_id": "block-123_2024-01-20_AM",
      "date": "2024-01-20",
      "time_of_day": "AM",
      "block_id": "block-123",
      "severity": "critical",
      "days_until": 5,
      "affected_area": "FMIT",
      "department": "Cardiology",
      "current_assignments": 0,
      "required_assignments": 1,
      "gap_size": 1
    }
  ]
}
```

### Severity Classification

| Severity | Days Until | Gap Size |
|----------|------------|----------|
| critical | ≤ 3 | any |
| high | 4-7 | > 1 |
| medium | 4-14 | 1 |
| low | > 14 | any |

---

## Coverage Suggestions

**Purpose:** Auto-generated solutions for coverage gaps.

```http
GET /fmit/coverage/suggestions?start_date=2024-01-15&end_date=2024-02-15&max_suggestions=20
```

### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `start_date` | date | today | Start of date range |
| `end_date` | date | start + 30 days | End of date range |
| `max_suggestions` | integer | 20 | Maximum suggestions to return |

### Response

```json
{
  "timestamp": "2024-01-15T10:30:00.000000",
  "total_suggestions": 8,
  "gaps_addressed": 8,
  "suggestions": [
    {
      "gap_id": "block-123_2024-01-20_AM",
      "suggestion_type": "assign_available",
      "priority": 1,
      "faculty_candidates": ["Dr. Smith", "Dr. Jones"],
      "estimated_conflict_score": 0.25,
      "reasoning": "Recommended: Dr. Smith (conflict score: 0.25) - Excellent fit, minimal conflicts",
      "alternative_dates": null
    },
    {
      "gap_id": "block-456_2024-01-22_PM",
      "suggestion_type": "swap_recommended",
      "priority": 2,
      "faculty_candidates": [],
      "estimated_conflict_score": 1.0,
      "reasoning": "No faculty available on 2024-01-22. Consider swap with existing assignments.",
      "alternative_dates": null
    }
  ]
}
```

### Suggestion Types

| Type | Description |
|------|-------------|
| `assign_available` | Faculty available for direct assignment |
| `swap_recommended` | No one available, swap needed |
| `overtime` | Consider overtime or additional coverage |

### Conflict Score Interpretation

| Score Range | Interpretation |
|-------------|----------------|
| 0.0 - 0.3 | Excellent fit, minimal conflicts |
| 0.3 - 0.6 | Good fit, some workload considerations |
| 0.6 - 1.0 | Available but high workload |

---

## Coverage Forecast

**Purpose:** Predict future coverage gaps based on trends.

```http
GET /fmit/coverage/forecast?weeks_ahead=12
```

### Query Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `weeks_ahead` | integer | 12 | 1-52 | Weeks to forecast |

### Response

```json
{
  "timestamp": "2024-01-15T10:30:00.000000",
  "forecast_start_date": "2024-01-15",
  "forecast_end_date": "2024-04-08",
  "overall_trend": "stable",
  "average_predicted_coverage": 91.5,
  "forecasts": [
    {
      "forecast_date": "2024-01-15",
      "predicted_coverage_percentage": 92.0,
      "predicted_gaps": 1,
      "confidence_level": 0.90,
      "trend": "stable",
      "risk_factors": []
    },
    {
      "forecast_date": "2024-02-12",
      "predicted_coverage_percentage": 88.0,
      "predicted_gaps": 2,
      "confidence_level": 0.75,
      "trend": "declining",
      "risk_factors": [
        "Below target coverage threshold (85%)",
        "2 holiday blocks may reduce availability"
      ]
    }
  ]
}
```

### Trend Values
- `improving`: Coverage trending upward
- `stable`: No significant change
- `declining`: Coverage trending downward

### Confidence Level
- Decreases with forecast distance (0.9 for week 1, ~0.5 for week 20+)

---

## Alert Summary

**Purpose:** Aggregated alert statistics by severity and type.

```http
GET /fmit/alerts/summary
```

### Response

```json
{
  "timestamp": "2024-01-15T10:30:00.000000",
  "critical_count": 2,
  "warning_count": 5,
  "info_count": 3,
  "total_count": 10,
  "by_type": {
    "double_booking": 3,
    "coverage_gap": 4,
    "acgme_violation": 2,
    "workload_imbalance": 1
  },
  "by_status": {
    "new": 4,
    "acknowledged": 3,
    "resolved": 45,
    "dismissed": 2
  },
  "oldest_unresolved": "2024-01-10T14:30:00.000000",
  "average_resolution_time_hours": 8.5
}
```

---

## Related Documentation

**Related API Documentation:**
- [Swaps API](SWAPS_API.md) - Swap management and execution
- [Resilience API](RESILIENCE_API.md) - System health and crisis management
- [Schedule API](SCHEDULE_API.md) - Schedule generation and validation
- [Health API](HEALTH_API.md) - Overall system health monitoring

**Architecture Decision Records:**
- [ADR-006: Swap System with Auto-Matching](../.claude/dontreadme/synthesis/DECISIONS.md#adr-006-swap-system-with-auto-matching) - Swap system design
- [ADR-004: Resilience Framework](../architecture/decisions/ADR-004-resilience-framework.md) - Cross-disciplinary resilience concepts

**Architecture Documentation:**
- [FMIT Constraints](../architecture/FMIT_CONSTRAINTS.md) - FMIT scheduling constraints

**Implementation Code:**
- `backend/app/api/routes/fmit_health.py` - FMIT health API routes
- `backend/app/services/fmit_coverage.py` - Coverage analysis
- `backend/app/services/swap_matcher.py` - Swap recommendation engine
