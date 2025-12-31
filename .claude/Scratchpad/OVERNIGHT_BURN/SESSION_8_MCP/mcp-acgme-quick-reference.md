# MCP ACGME Tools - Quick Reference

**Fast lookup guide for ACGME compliance validation via MCP**

---

## All ACGME Tools at a Glance

### Core Validation (3 tools)

| Tool | Purpose | When to Use |
|------|---------|------------|
| `validate_schedule_tool()` | Validate date range for ACGME compliance | Weekly/monthly compliance checks |
| `validate_schedule_by_id_tool()` | Validate persisted schedule by ID | Finalize schedule before publication |
| `detect_conflicts_tool()` | Find specific violations in date range | Troubleshoot problem areas |

### Contingency & Impact (3 tools)

| Tool | Purpose | When to Use |
|------|---------|------------|
| `run_contingency_analysis_tool()` | Simulate absence/emergency scenarios | Planning for faculty/resident leave |
| `run_contingency_analysis_resilience_tool()` | N-1 contingency with resilience | Stress-test schedule robustness |
| `check_mtf_compliance_tool()` | Military MTF compliance check | Military medical programs only |

### Resilience & Defense (3 tools)

| Tool | Purpose | When to Use |
|------|---------|------------|
| `check_utilization_threshold_tool()` | Check 80% capacity threshold | Early warning for overload |
| `get_defense_level_tool()` | Current defense level (GREEN/YELLOW/RED) | Monitor system health |
| `get_static_fallbacks_tool()` | Pre-computed compliant backups | Emergency schedule takeover |

### Background Tasks (4 tools)

| Tool | Purpose | When to Use |
|------|---------|------------|
| `start_background_task_tool()` | Launch async validation | Large schedules |
| `get_task_status_tool()` | Query async task progress | Monitor long operations |
| `cancel_task_tool()` | Stop running task | Abort hung validations |
| `list_active_tasks_tool()` | See all active background tasks | Visibility into operations |

---

## The 4 Core ACGME Rules

### 1. 80-Hour Rule

**Rule:** Max 80 hours/week (4-week rolling average)
**Tool:** `validate_schedule_tool(check_work_hours=True)`
**Applies To:** Residents only
**Check With:** `constraint_config="default"`

```python
# Violation looks like:
{
  "rule": "80_HOUR_WEEKLY_LIMIT",
  "average_hours": 84.5,  # Exceeds 80
  "violation_hours": 4.5
}
```

### 2. 1-in-7 Rule

**Rule:** One 24-hour period off every 7 days (max 6 consecutive duty days)
**Tool:** `validate_schedule_tool(check_rest_periods=True)`
**Applies To:** Residents only
**Check With:** `constraint_config="default"`

```python
# Violation looks like:
{
  "rule": "1_IN_7_RULE_VIOLATION",
  "consecutive_duty_days": 8,  # Exceeds 6
  "violation_days": 2
}
```

### 3. Supervision Ratios

**Rule:** PGY-1: 1 faculty:2 residents | PGY-2/3: 1 faculty:4 residents
**Tool:** `validate_schedule_tool(check_supervision=True)`
**Applies To:** All assignments
**Check With:** `constraint_config="default"`

```python
# Violation looks like:
{
  "rule": "SUPERVISION_RATIO_VIOLATION",
  "pgy_level": "PGY1",
  "ratio_required": "2:1",
  "ratio_actual": "2.5:1",  # 5 residents, 2 faculty
  "missing_faculty": 1
}
```

### 4. Availability (Absence Enforcement)

**Rule:** No assignments during scheduled absences
**Tool:** `validate_schedule_tool()` (automatic)
**Applies To:** All person types
**Check With:** `constraint_config="default"`

```python
# Violation looks like:
{
  "rule": "AVAILABILITY_VIOLATION",
  "person": "RESIDENT-001",
  "absence_type": "TDY",
  "assigned_date": "2025-01-15",
  "absence_date": "2025-01-15"
}
```

---

## Common Use Cases

### Use Case 1: Validate Entire Block

```python
# Block 10 = 13-week academic block
result = await validate_schedule_tool(
    start_date="2025-01-06",
    end_date="2025-04-06",
    check_work_hours=True,
    check_supervision=True,
    check_rest_periods=True,
    check_consecutive_duty=True
)

if result.is_valid:
    print("✓ Schedule passes all ACGME checks")
else:
    print(f"✗ Found {result.critical_issues} critical violations")
```

### Use Case 2: Quick Problem Diagnosis

```python
# Find specific issues in a week
result = await detect_conflicts_tool(
    start_date="2025-01-13",
    end_date="2025-01-19",
    conflict_types=[
        "work_hour_violation",
        "rest_period_violation",
        "supervision_gap"
    ]
)

for conflict in result.conflicts:
    print(f"{conflict.conflict_type}: {conflict.description}")
```

### Use Case 3: Plan for Faculty Leave

```python
# Faculty going on leave Jan 20-27
impact = await run_contingency_analysis_tool(
    scenario="faculty_absence",
    affected_person_ids=["fac-12345"],
    start_date="2025-01-20",
    end_date="2025-01-27"
)

print(f"Coverage gaps: {impact.impact.coverage_gaps}")
print(f"ACGME violations: {impact.impact.compliance_violations}")
print(f"Can resolve: {len([o for o in impact.resolution_options if o.success_probability > 0.75])}")
```

### Use Case 4: Monitor Utilization

```python
# Check if schedule is overloaded
defense = await check_utilization_threshold_tool()

if defense.level in ["RED", "BLACK"]:
    print(f"⚠️ Schedule at critical capacity!")
    print(f"Action: {defense.action_required}")
```

---

## Constraint Configuration Cheat Sheet

```python
validate_schedule_by_id_tool(
    schedule_id="block10-2025",
    constraint_config="X"  # Pick one:
)
```

| Config | Speed | Checks | Use Case |
|--------|-------|--------|----------|
| `"minimal"` | 50ms | Basic only | Quick sanity check |
| `"default"` | 300ms | ACGME rules | Standard validation |
| `"strict"` | 800ms | All constraints | Comprehensive check |
| `"resilience"` | 1500ms | ACGME + resilience | Robustness analysis |

---

## Violation Severity Mapping

| Severity | Meaning | Action |
|----------|---------|--------|
| CRITICAL | ACGME rule broken | Must fix before publish |
| WARNING | Policy/soft rule broken | Fix recommended |
| INFO | Warning threshold | Monitor trend |

---

## Response Fields Reference

### ValidationResult

```python
{
    "is_valid": bool,                        # Pass/fail
    "overall_compliance_rate": 0.0-1.0,     # % compliant
    "total_issues": int,                    # All violations
    "critical_issues": int,                 # Must-fix count
    "warning_issues": int,
    "info_issues": int,
    "issues": [                             # Detailed list
        {
            "severity": "CRITICAL|WARNING|INFO",
            "rule_type": "80_HOUR_WEEKLY_LIMIT",
            "message": "...",
            "person_id": "RESIDENT-001",    # Anonymized
            "date_range": ("2025-01-01", "2025-01-28"),
            "suggested_fix": "...",
            "details": {...}
        }
    ],
    "validated_at": datetime,
}
```

---

## Error Codes & Solutions

| Error | Cause | Fix |
|-------|-------|-----|
| `schedule_id contains invalid characters` | Bad ID format | Use UUID or alphanumeric only |
| `Invalid constraint_config: xyz` | Wrong config name | Use: minimal/default/strict/resilience |
| `Backend unavailable` | FastAPI server down | Start backend: `docker-compose up -d backend` |
| `date_range timeout` | Schedule too large | Break into weekly chunks or use background task |

---

## When to Use Each Tool

```
Question: "Is this schedule ACGME compliant?"
→ validate_schedule_tool() ✓

Question: "What's wrong with this schedule?"
→ detect_conflicts_tool() ✓

Question: "What if faculty member X takes leave?"
→ run_contingency_analysis_tool() ✓

Question: "Can this schedule survive N-1 failure?"
→ run_contingency_analysis_resilience_tool() ✓

Question: "Is our capacity OK?"
→ check_utilization_threshold_tool() ✓

Question: "I have a specific schedule ID to validate"
→ validate_schedule_by_id_tool() ✓
```

---

## ACGME Constants Reference

```python
# Work Hours
MAX_HOURS_PER_WEEK = 80
ROLLING_AVERAGE_WEEKS = 4  # 4-week window

# Rest & Duty Days
MAX_CONSECUTIVE_DAYS = 6   # Must have 1 day off in 7
MAX_CONSECUTIVE_HOURS = 24  # Plus 4 for handoff
MAX_HANDOFF_HOURS = 4

# Supervision Ratios
PGY1_RATIO = "1:2"  # 1 faculty per 2 residents
PGY2_3_RATIO = "1:4" # 1 faculty per 4 residents

# Night Float (if used)
MAX_NIGHT_FLOAT_CONSECUTIVE = 6
HOURS_PER_NIGHT_SHIFT = 12
```

---

## Common Fixes Quick List

| Violation | Quick Fix |
|-----------|-----------|
| 80-hour violation | Reduce rotation assignments, extend timeline |
| 1-in-7 violation | Insert rest day, swap with colleague |
| Supervision gap | Add faculty, reduce resident capacity |
| Availability violation | Remove assignment from absence date |
| Post-call violation | Make post-call day light duty |

---

## Testing a Tool Locally

```python
# Load MCP client
from scheduler_mcp import client

# Test validate_schedule_tool
result = await client.validate_schedule_tool(
    start_date="2025-01-06",
    end_date="2025-01-13",
    check_work_hours=True
)

# Print result
print(f"Valid: {result.is_valid}")
print(f"Issues: {len(result.issues)}")
for issue in result.issues:
    print(f"  - {issue.severity}: {issue.rule_type}")
```

---

## Files to Know

| File | What It Has |
|------|------------|
| `mcp-server/src/scheduler_mcp/server.py` | All tool registrations |
| `mcp-server/src/scheduler_mcp/scheduling_tools.py` | Tool implementations |
| `backend/app/services/constraints/acgme.py` | **CANONICAL** constraint code |
| `backend/app/validators/acgme_validators.py` | Validation functions |

---

**Last Updated:** 2025-12-30
**Version:** 1.0
