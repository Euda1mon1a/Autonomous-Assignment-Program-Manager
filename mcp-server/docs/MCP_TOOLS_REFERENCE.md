# MCP Tools Reference

This document provides a comprehensive reference for the MCP (Model Context Protocol) tools implemented in the Residency Scheduler MCP server.

## Overview

The MCP server exposes 5 primary tools for schedule validation, contingency analysis, conflict detection, and swap matching. These tools enable AI assistants to perform intelligent scheduling operations.

---

## Tools

### 1. `validate_schedule`

Validates a schedule against ACGME compliance rules.

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `schedule_id` | string | Yes | UUID of the schedule to validate |
| `date_range` | object | No | Optional date range filter |
| `rules` | array | No | Specific rules to check (default: all) |

#### ACGME Rules Validated

| Rule | Threshold | Implementation |
|------|-----------|----------------|
| **80-Hour Rule** | Max 80 hrs/week (4-week average) | 6 hours per block, max 53 blocks per 4-week window |
| **1-in-7 Rest Rule** | One day off per 7 days | Max 6 consecutive duty days |
| **Supervision Ratios** | PGY-1: 1:2, PGY-2/3: 1:4 | Faculty count per block |

#### Response

```json
{
  "schedule_id": "uuid",
  "validation_timestamp": "2025-12-20T10:00:00Z",
  "is_compliant": false,
  "overall_compliance_rate": 0.92,
  "issues": [
    {
      "severity": "critical",
      "rule": "80_hour",
      "description": "Dr. Smith exceeds 80-hour limit in week of Dec 15",
      "affected_entities": ["person-uuid-1"],
      "suggested_fix": "Reduce assignments by 2 blocks"
    }
  ],
  "summary": {
    "critical_count": 1,
    "warning_count": 3,
    "info_count": 5
  }
}
```

---

### 1a. `validate_schedule_by_id` (ConstraintService Integration)

> **New in v1.1** - Enhanced validation tool with ConstraintService backend integration.

Validates a schedule by ID using the backend ConstraintService with proper input sanitization and PII protection.

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `schedule_id` | string | Yes | UUID or alphanumeric identifier (validated against injection) |
| `constraint_config` | enum | No | Configuration level: `default`, `minimal`, `strict`, `resilience` |
| `include_suggestions` | boolean | No | Include suggested actions for issues (default: true) |

#### Input Validation

The `schedule_id` is validated against:
- Path traversal (`..`, `/`, `\`)
- Injection characters (`<`, `>`, `'`, `"`, `;`, `&`, `|`, `$`, `` ` ``)
- Control characters (`\n`, `\r`, `\x00`)
- Must be a valid UUID or alphanumeric identifier (max 64 chars)

#### Constraint Configurations

| Config | Description |
|--------|-------------|
| `default` | Standard ACGME compliance checks |
| `minimal` | Fast validation with critical rules only |
| `strict` | All rules with lower thresholds |
| `resilience` | Include resilience framework checks |

#### Response (Sanitized)

```json
{
  "schedule_id": "abc123",
  "is_valid": true,
  "compliance_rate": 0.95,
  "total_issues": 2,
  "critical_count": 0,
  "warning_count": 1,
  "info_count": 1,
  "issues": [
    {
      "severity": "warning",
      "rule_type": "supervision",
      "message": "Block has 3 PGY-1 with 1 faculty (requires 2)",
      "constraint_name": "supervision_ratio",
      "affected_entity_ref": "block-2025-12-20-AM",
      "suggested_action": "Add faculty supervision"
    }
  ],
  "validated_at": "2025-12-20T10:00:00Z",
  "constraint_config": "default",
  "metadata": {
    "source": "constraint_service"
  }
}
```

#### Security Features

- **Input Sanitization**: All schedule IDs validated against injection attacks
- **PII Protection**: No person names in responses, only role-based identifiers
- **Graceful Degradation**: Returns placeholder data if backend unavailable

---

### 2. `analyze_contingency`

Performs N-1/N-2 contingency analysis based on the resilience framework.

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `schedule_id` | string | Yes | UUID of the schedule |
| `scenario` | string | Yes | Type: `faculty_absence`, `resident_absence`, `emergency`, `mass_absence` |
| `affected_person_ids` | array | Yes | Person UUIDs to simulate as absent |
| `date_range` | object | No | Date range for analysis |

#### Scenario Types

| Scenario | Description | Analysis Focus |
|----------|-------------|----------------|
| `faculty_absence` | Single faculty member unavailable | Supervision gaps, workload redistribution |
| `resident_absence` | Single resident unavailable | Coverage gaps, backup activation |
| `emergency` | Emergency coverage scenario | Critical service coverage |
| `mass_absence` | Multiple simultaneous absences | Cascade failure risk |

#### Response

```json
{
  "scenario": "faculty_absence",
  "analysis_timestamp": "2025-12-20T10:00:00Z",
  "impact_assessment": {
    "coverage_gaps": 5,
    "acgme_violations": 2,
    "workload_increase_pct": 15.5,
    "feasibility_score": 0.75,
    "critical_gaps": ["inpatient-mon-am", "call-tue-pm"]
  },
  "resolution_options": [
    {
      "option": "swap_assignments",
      "description": "Reassign 3 blocks to available faculty",
      "effort": "low",
      "success_probability": 0.85
    },
    {
      "option": "backup_pool",
      "description": "Activate backup faculty pool",
      "effort": "medium",
      "success_probability": 0.90
    }
  ],
  "recommendation": "swap_assignments"
}
```

---

### 3. `detect_conflicts`

Detects scheduling conflicts with auto-resolution options.

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `schedule_id` | string | Yes | UUID of the schedule |
| `conflict_types` | array | No | Filter by type (default: all) |
| `include_resolved` | boolean | No | Include already-resolved conflicts |

#### Conflict Types

| Type | Description | Auto-Resolution |
|------|-------------|-----------------|
| `double_booking` | Same person, multiple assignments | Remove duplicate |
| `work_hour_violation` | Exceeds 80-hour limit | Reduce assignments |
| `rest_period_violation` | No day off in 7 days | Insert rest day |
| `supervision_gap` | Inadequate faculty ratio | Add supervision |
| `leave_overlap` | Assignment during approved leave | Reassign |
| `credential_mismatch` | Missing required certifications | Reassign to qualified |

#### Response

```json
{
  "schedule_id": "uuid",
  "detection_timestamp": "2025-12-20T10:00:00Z",
  "conflicts": [
    {
      "conflict_id": "conflict-uuid",
      "type": "double_booking",
      "severity": "high",
      "description": "Dr. Jones assigned to both Clinic A and Inpatient on Dec 18 AM",
      "affected_assignments": ["assignment-1", "assignment-2"],
      "affected_blocks": ["block-uuid"],
      "affected_people": ["person-uuid"],
      "auto_resolution": {
        "available": true,
        "action": "remove_duplicate",
        "description": "Remove Clinic A assignment (lower priority)",
        "effort": "low",
        "success_probability": 0.95
      }
    }
  ],
  "summary": {
    "total_conflicts": 8,
    "auto_resolvable": 6,
    "requires_review": 2
  }
}
```

---

### 4. `find_swap_matches`

Finds compatible swap candidates using multi-factor scoring.

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `requester_id` | string | Yes | Faculty requesting the swap |
| `assignment_id` | string | Yes | Assignment to swap |
| `preferences` | object | No | Swap preferences |
| `max_candidates` | integer | No | Max results (default: 5) |

#### Scoring Algorithm

| Factor | Weight | Description |
|--------|--------|-------------|
| Date Proximity | 25% | Closer dates score higher |
| Preference Alignment | 30% | Mutual preferences bonus |
| Workload Balance | 20% | Fair distribution preferred |
| Swap History | 15% | Past successes boost score |
| Availability | 10% | Both parties available |

#### Response

```json
{
  "request_timestamp": "2025-12-20T10:00:00Z",
  "requester_id": "person-uuid",
  "source_assignment": {
    "id": "assignment-uuid",
    "date": "2025-12-22",
    "rotation": "Inpatient",
    "block_type": "AM"
  },
  "candidates": [
    {
      "candidate_id": "person-uuid-2",
      "candidate_role": "Faculty",
      "match_score": 0.92,
      "target_assignment": {
        "id": "assignment-uuid-2",
        "date": "2025-12-23",
        "rotation": "Clinic",
        "block_type": "AM"
      },
      "compatibility_factors": {
        "date_proximity": 0.95,
        "preference_match": 0.90,
        "workload_balance": 0.88,
        "history_score": 1.0,
        "availability": 1.0
      },
      "mutual_benefit": true,
      "approval_likelihood": "high"
    }
  ],
  "top_recommendation": "person-uuid-2",
  "candidates_found": 5
}
```

---

## Error Handling

All tools return standardized error responses:

```json
{
  "error": true,
  "error_code": "SCHEDULE_NOT_FOUND",
  "message": "Schedule with ID 'xyz' does not exist",
  "timestamp": "2025-12-20T10:00:00Z"
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `SCHEDULE_NOT_FOUND` | 404 | Invalid schedule ID |
| `PERSON_NOT_FOUND` | 404 | Invalid person ID |
| `INVALID_DATE_RANGE` | 400 | Date range is invalid |
| `VALIDATION_ERROR` | 400 | Request validation failed |
| `DATABASE_ERROR` | 500 | Database operation failed |

---

## Authentication

MCP tools require valid authentication via the parent session. The MCP server inherits authentication context from the Claude session.

---

## Rate Limits

| Tool | Limit | Window |
|------|-------|--------|
| `validate_schedule` | 60/min | Per schedule |
| `analyze_contingency` | 30/min | Per schedule |
| `detect_conflicts` | 60/min | Per schedule |
| `find_swap_matches` | 120/min | Per user |

---

## Integration Example

### Claude Desktop Configuration

```json
{
  "mcpServers": {
    "residency-scheduler": {
      "command": "python",
      "args": ["-m", "scheduler_mcp.server"],
      "cwd": "/path/to/mcp-server",
      "env": {
        "DATABASE_URL": "postgresql://..."
      }
    }
  }
}
```

### Tool Invocation

```
User: Check if the December schedule is ACGME compliant

Claude: I'll validate the December schedule for ACGME compliance.

[Calls validate_schedule with schedule_id and date_range]

Based on the validation results:
- Overall compliance: 92%
- 1 critical issue: Dr. Smith exceeds 80-hour limit
- 3 warnings: Minor supervision ratio concerns

Recommendation: Reduce Dr. Smith's assignments by 2 blocks in week 3.
```

---

## See Also

- [MCP Resources Reference](./MCP_RESOURCES_REFERENCE.md)
- [ACGME Compliance Rules](../docs/user-guide/compliance.md)
- [Resilience Framework](../docs/architecture/resilience.md)
