# Template Variable Documentation

> **Version:** 1.0
> **Last Updated:** 2025-12-31

---

## Variable Naming Convention

All variables follow this pattern: `${CATEGORY_VARIABLE_NAME}`

### Categories

| Category | Purpose | Example |
|----------|---------|---------|
| `MISSION_*` | Mission parameters and objectives | `${MISSION_OBJECTIVE}` |
| `PERSON_*` | Personnel-related data | `${PERSON_ID}` |
| `PERSONNEL_*` | Population-level data | `${PERSONNEL_COUNT}` |
| `SCHEDULE_*` | Schedule identification and state | `${SCHEDULE_ID}` |
| `BLOCK_*` | Schedule block information | `${BLOCK_DATE}` |
| `ASSIGNMENT_*` | Assignment details | `${ASSIGNMENT_ID}` |
| `ROTATION_*` | Rotation-related data | `${ROTATION_TYPES}` |
| `COVERAGE_*` | Coverage metrics | `${COVERAGE_PERCENT}` |
| `COMPLIANCE_*` | ACGME/regulatory compliance | `${COMPLIANCE_STATUS}` |
| `RESOURCE_*` | Resource allocation | `${RESOURCE_COUNT}` |
| `CONSTRAINT_*` | Constraints and rules | `${CONSTRAINT_COUNT}` |
| `TIME_*` | Time-related values | `${TIME_LIMIT}` |
| `STATUS_*` | Current status information | `${STATUS}` |
| `RESULT_*` | Results and outcomes | `${RESULT}` |
| `ERROR_*` | Error information | `${ERROR_MESSAGE}` |
| `METRIC_*` | Key metrics | `${METRIC_COVERAGE}` |
| `ALERT_*` | Alert and warning information | `${ALERT_LEVEL}` |
| `SEVERITY_*` | Severity classification | `${SEVERITY_LEVEL}` |

---

## Common Variables Reference

### Mission Variables
```
${MISSION_OBJECTIVE}    - Primary mission goal (string)
${MISSION_TYPE}         - Type of mission (enum)
${MISSION_SCOPE}        - Scope of mission (string)
${MISSION_DEADLINE}     - Mission completion deadline (date)
```

### Personnel Variables
```
${PERSON_ID}            - Unique person identifier (UUID)
${PERSON_NAME}          - Person name (SANITIZED for OPSEC)
${PERSON_ROLE}          - Person's role (enum: RESIDENT, FACULTY, etc)
${PERSON_PGY}           - PGY level (1, 2, 3, ...)
${PERSON_STATUS}        - Current status (ACTIVE, INACTIVE, ON_LEAVE)
${PERSONNEL_COUNT}      - Total personnel count (int)
${ROSTER_COUNT}         - Active roster count (int)
${ROSTER_STRENGTH}      - Roster percentage (0-100)
```

### Schedule Variables
```
${SCHEDULE_ID}          - Schedule identifier (UUID)
${SCHEDULE_STATE}       - Schedule state (DRAFT, ACTIVE, ARCHIVED)
${SCHEDULE_PERIOD}      - Schedule period (string: "Q1 2025")
${START_DATE}           - Schedule start date (YYYY-MM-DD)
${END_DATE}             - Schedule end date (YYYY-MM-DD)
${DURATION_DAYS}        - Duration in days (int)
${BLOCK_DATE}           - Specific block date (YYYY-MM-DD)
${BLOCK_ID}             - Block identifier
```

### Assignment Variables
```
${ASSIGNMENT_ID}        - Assignment identifier (UUID)
${ASSIGNMENT_COUNT}     - Total assignments (int)
${ASSIGNED_COUNT}       - Filled assignments (int)
${OPEN_SLOTS}           - Open/unassigned slots (int)
${TOTAL_SLOTS}          - Total available slots (int)
```

### Rotation Variables
```
${ROTATION_TYPES}       - List of rotation types (array)
${ROTATION_TYPE}        - Specific rotation type (enum)
${ROTATION_COUNT}       - Number of rotations (int)
${ROTATION_VARIANCE}    - Variance in rotation distribution (percent)
${ROTATION_BALANCE}     - Balance quality score (0-100)
```

### Coverage Variables
```
${COVERAGE_PERCENT}     - Coverage percentage (0-100)
${COVERAGE_TARGET}      - Target coverage (0-100)
${COVERAGE_STATUS}      - Coverage status (GOOD, FAIR, POOR)
${COVERAGE_GAP}         - Coverage shortfall (int)
${COVERAGE_TREND}       - Trend direction (UP, DOWN, STABLE)
${OPEN_SLOTS}           - Number of open slots (int)
${COVERAGE_IMPACT}      - Impact of change on coverage (string)
```

### ACGME Variables
```
${COMPLIANCE_STATUS}    - Overall compliance (COMPLIANT, VIOLATIONS)
${COMPLIANCE_PERCENT}   - Compliance percentage (0-100)
${COMPLIANCE_REQUIRED}  - Required compliance level (typically 100)
${RULE_80H_PASS}        - 80-hour rule status (PASS, FAIL)
${RULE_1IN7_PASS}       - 1-in-7 rule status (PASS, FAIL)
${VIOLATION_COUNT}      - Number of violations (int)
${VIOLATION_TYPE}       - Type of violation (string)
${ACGME_RISK}           - Risk level (NONE, LOW, MEDIUM, HIGH)
${HOURS_PER_WEEK}       - Calculated hours per week (float)
${DAYS_TO_VIOLATION}    - Days until violation occurs (int)
```

### Resource Variables
```
${RESOURCE_COUNT}       - Resource count (int)
${RESOURCE_TYPE}        - Resource type (string)
${AVAILABLE_CAPACITY}   - Available capacity (int)
${UTILIZATION_PERCENT}  - Utilization percentage (0-100)
${CONSTRAINT_COUNT}     - Constraint count (int)
```

### Time Variables
```
${TODAY}                - Current date (YYYY-MM-DD)
${CURRENT_DATE}         - Current date (same as TODAY)
${CURRENT_TIME}         - Current time (HH:MM:SS)
${TIME_LIMIT}           - Time limit for operation (int minutes)
${TIME_BUDGET}          - Available time budget (int minutes)
${TIME_ELAPSED}         - Elapsed time (int minutes)
${TIME_REMAINING}       - Remaining time (int minutes)
${PERIOD}               - Reporting period (string)
${LAST_SYNC}            - Last synchronization time (datetime)
${LAST_SUCCESS}         - Last successful operation (datetime)
```

### Metric Variables
```
${METRIC_COVERAGE}      - Coverage metric (0-100)
${METRIC_BALANCE}       - Balance metric (0-100)
${METRIC_UTILIZATION}   - Utilization metric (0-100)
${METRIC_QUALITY}       - Quality metric (0-100)
${AVG_RESPONSE}         - Average response time (ms)
${P95_RESPONSE}         - 95th percentile response time (ms)
${ERROR_RATE}           - Error rate (percent)
${THROUGHPUT}           - Throughput (requests/sec)
```

### Alert Variables
```
${ALERT_LEVEL}          - Alert severity (GREEN, YELLOW, ORANGE, RED, BLACK)
${THREAT_LEVEL}         - Threat severity (NONE, LOW, MEDIUM, HIGH, CRITICAL)
${PRIORITY}             - Priority level (LOW, MEDIUM, HIGH, CRITICAL)
${SEVERITY_LEVEL}       - Severity classification
${ESCALATION_THRESHOLD} - When to escalate (numeric threshold)
${DAYS_TO_CRITICAL}     - Days until critical state (int)
```

### Status Variables
```
${STATUS}               - Current status (ACTIVE, PENDING, COMPLETE, FAILED)
${RESULT}               - Operation result (SUCCESS, FAILURE, PARTIAL)
${VERDICT}              - Validation verdict (PASS, FAIL, CONDITIONAL)
${FEASIBLE}             - Feasibility (TRUE, FALSE)
${COMPLIANT}            - Compliance status (TRUE, FALSE)
```

### Credential Variables
```
${CREDENTIAL_COUNT}     - Credential count (int)
${CREDENTIAL_GAPS}      - Missing credentials (int)
${CREDENTIAL_GAPS}      - Credential gaps count (int)
${CREDENTIAL_SHORTAGE}  - Shortage count (int)
${CREDENTIAL_REQUIREMENT}` - Required credential (string)
```

### Error Variables
```
${ERROR_MESSAGE}        - Error description (string)
${ERROR_CODE}           - Error code (string)
${ERROR_SEVERITY}       - Error severity (LOW, MEDIUM, HIGH, CRITICAL)
${ROOT_CAUSE}           - Root cause analysis (string)
${RECOVERY_STEPS}       - Recovery procedure (string)
```

---

## Variable Type Guide

| Type | Format | Example | Validation |
|------|--------|---------|-----------|
| `int` | Integer | `45`, `0`, `-1` | Numeric only |
| `float` | Decimal | `3.14`, `95.5` | Numeric with decimals |
| `percent` | 0-100 | `85`, `100`, `0` | Int 0-100 or "N/A" |
| `date` | YYYY-MM-DD | `2025-12-31` | ISO 8601 date |
| `datetime` | YYYY-MM-DD HH:MM:SS | `2025-12-31 14:30:00` | ISO 8601 datetime |
| `time` | HH:MM:SS | `14:30:00` | 24-hour format |
| `duration` | minutes | `45`, `120` | Integer minutes |
| `string` | Text | "Schedule status" | Max 200 chars |
| `uuid` | UUID format | `a1b2c3d4-...` | Valid UUID |
| `enum` | Fixed set | "ACTIVE" | Predefined values |
| `array` | List | `[item1, item2]` | JSON format |
| `json` | Object | `{"key": "value"}` | Valid JSON |
| `boolean` | True/False | `true`, `false` | Lowercase |

---

## Variable Initialization Checklist

Before executing any template:

- [ ] All `${VARIABLE}` placeholders identified
- [ ] All variables have actual values assigned
- [ ] Variable types match expected format
- [ ] Sensitive data sanitized (no real names)
- [ ] Dates in consistent format (YYYY-MM-DD)
- [ ] Percentages are 0-100
- [ ] Required variables present
- [ ] Variable consistency across related templates

---

## Security Considerations

### Sanitization Rules
- **Never include real person names** - Use ID only
- **No sensitive schedules in examples** - Use synthetic data
- **No OPSEC/PERSEC in logs** - Sanitize before output
- **No credential details** - Use credential type only
- **No system internals** - Use abstraction level

### Variable Masking
```
Real: John Smith (RESIDENT)
Mask: ${PERSON_ID} (RESIDENT)

Real: 2025-12-25 (Christmas deployment)
Mask: 2025-${MONTH}-${DAY}

Real: Air Force residency, Walter Reed
Mask: Medical residency program, institution
```

---

*This document is normative. All template variables must conform to this specification.*
