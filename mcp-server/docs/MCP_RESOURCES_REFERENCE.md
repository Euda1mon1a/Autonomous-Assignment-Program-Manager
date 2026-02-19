# MCP Resources Reference

This document provides a comprehensive reference for the MCP (Model Context Protocol) resources exposed by the Residency Scheduler MCP server.

## Overview

MCP resources provide read-only access to schedule data, compliance summaries, and system status. Unlike tools (which perform actions), resources return current state information.

---

## Resources

### 1. `schedule://status`

Returns the current schedule status with coverage metrics and operational data.

#### URI Pattern

```
schedule://status/{schedule_id}
schedule://status/{schedule_id}?date_range={start},{end}
```

#### Response

```json
{
  "schedule_id": "uuid",
  "query_timestamp": "2025-12-20T10:00:00Z",
  "assignments": [
    {
      "id": "assignment-uuid",
      "person_id": "person-uuid",
      "person_role": "Faculty",
      "person_type": "faculty",
      "pgy_level": null,
      "rotation": "Inpatient",
      "block_date": "2025-12-20",
      "block_type": "AM",
      "role": "supervising",
      "is_supervising": true
    }
  ],
  "coverage_metrics": {
    "total_days": 28,
    "covered_days": 26,
    "coverage_rate": 0.929,
    "understaffed_days": 2,
    "overstaffed_days": 0,
    "avg_faculty_per_day": 4.2,
    "avg_residents_per_day": 8.5
  },
  "operational_status": {
    "active_conflicts": 3,
    "pending_swaps": 2,
    "last_schedule_run": "2025-12-18T14:30:00Z",
    "algorithm_used": "greedy_with_constraints"
  }
}
```

#### Database Queries

The resource performs these queries:
1. Assignments with JOINs to Block, Person, RotationTemplate
2. Coverage calculation (covered vs. total blocks)
3. Conflict count from ConflictAlert table
4. Pending swaps from SwapRecord table
5. Last ScheduleRun metadata

---

### 2. `compliance://summary`

Returns ACGME compliance summary with violation details.

#### URI Pattern

```
compliance://summary/{schedule_id}
compliance://summary/{schedule_id}?date_range={start},{end}
```

#### Response

```json
{
  "schedule_id": "uuid",
  "check_timestamp": "2025-12-20T10:00:00Z",
  "date_range": {
    "start": "2025-12-01",
    "end": "2025-12-31"
  },
  "overall_compliant": false,
  "compliance_rate": 0.92,
  "violations": [
    {
      "rule": "80_hour",
      "severity": "critical",
      "affected_person_id": "person-uuid",
      "affected_person_role": "PGY-2",
      "period": "2025-12-08 to 2025-12-14",
      "details": "Worked 86 hours (6 hours over limit)",
      "recommendation": "Reduce 1 block assignment"
    }
  ],
  "rule_summaries": {
    "80_hour": {
      "checks": 24,
      "violations": 1,
      "compliance_rate": 0.958
    },
    "1_in_7": {
      "checks": 24,
      "violations": 0,
      "compliance_rate": 1.0
    },
    "supervision": {
      "checks": 56,
      "violations": 2,
      "compliance_rate": 0.964
    }
  },
  "affected_residents": 3,
  "recommendations": [
    "Reduce Dr. Smith's assignments in week 2",
    "Add supervising faculty to Dec 15 PM block",
    "Review workload distribution for PGY-1 residents"
  ]
}
```

#### ACGME Validation Logic

**80-Hour Rule:**
```python
# Track assignments per resident over rolling 4-week windows
# Each block = 6 hours
# Max 53 blocks per 4-week period (80 * 4 / 6 = 53.3)
for week_start in rolling_windows:
    week_blocks = count_blocks(resident, week_start, week_start + 28)
    if week_blocks > 53:
        add_violation("80_hour", resident, week_start)
```

**1-in-7 Rule:**
```python
# Check for 7+ consecutive duty days
for resident in residents:
    consecutive = 0
    for day in date_range:
        if has_assignment(resident, day):
            consecutive += 1
            if consecutive > 6:
                add_violation("1_in_7", resident, day)
        else:
            consecutive = 0
```

**Supervision Ratios:**
```python
# PGY-1: 1 faculty per 2 residents
# PGY-2/3: 1 faculty per 4 residents
for block in blocks:
    pgy1_count = count_pgy1(block)
    pgy23_count = count_pgy23(block)
    faculty_count = count_faculty(block)

    required_faculty = (pgy1_count / 2) + (pgy23_count / 4)
    if faculty_count < required_faculty:
        add_violation("supervision", block)
```

---

## Database Integration

### Session Management

Resources use a dedicated database session helper:

```python
def _get_db_session() -> Session:
    """Get database session from configured DATABASE_URL."""
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not configured")

    engine = create_engine(database_url)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()
```

### Query Optimization

Resources use eager loading to avoid N+1 queries:

```python
from sqlalchemy.orm import joinedload

query = (
    select(Assignment)
    .options(
        joinedload(Assignment.person),
        joinedload(Assignment.block),
        joinedload(Assignment.rotation_template)
    )
    .where(Assignment.schedule_id == schedule_id)
)
```

---

## Error Handling

Resources return standardized error responses:

```json
{
  "error": true,
  "error_code": "RESOURCE_NOT_FOUND",
  "message": "Schedule with ID 'xyz' does not exist",
  "timestamp": "2025-12-20T10:00:00Z"
}
```

### Error Codes

| Code | Description |
|------|-------------|
| `RESOURCE_NOT_FOUND` | Schedule/resource doesn't exist |
| `DATABASE_ERROR` | Database query failed |
| `INVALID_DATE_RANGE` | Invalid date range parameter |
| `CONFIGURATION_ERROR` | Missing environment config |

---

## Caching

Resources support response caching for performance:

| Resource | TTL | Invalidation |
|----------|-----|--------------|
| `schedule://status` | 60s | On assignment change |
| `compliance://summary` | 300s | On assignment change |

---

## Authentication

Resources inherit authentication from the MCP session. No additional authentication is required when accessed through Claude.

---

## Integration Example

### Accessing Resources

```
User: What's the current schedule compliance status?

Claude: I'll check the compliance summary for the current schedule.

[Reads compliance://summary resource]

The December schedule is 92% compliant with 3 issues:
1. Critical: Dr. Smith exceeded 80-hour limit (week of Dec 8)
2. Warning: Supervision ratio low on Dec 15 PM
3. Warning: Supervision ratio low on Dec 22 AM

Recommendations:
- Reduce Dr. Smith's assignments by 1 block in week 2
- Add supervising faculty to the flagged blocks
```

---

## See Also

- [MCP Tools Reference](./MCP_TOOLS_REFERENCE.md)
- [ACGME Compliance Rules](../docs/user-guide/compliance.md)
- [Database Schema](../docs/architecture/database.md)
