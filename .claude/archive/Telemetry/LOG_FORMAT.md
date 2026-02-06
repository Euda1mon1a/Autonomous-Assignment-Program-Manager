# Telemetry Log Format Specification

> **Purpose**: JSON schema for AI infrastructure telemetry events
> **Last Updated**: 2025-12-26
> **Format**: JSONL (JSON Lines: one JSON object per line)
> **Encoding**: UTF-8

---

## Table of Contents

1. [Format Overview](#format-overview)
2. [Base Event Schema](#base-event-schema)
3. [Event Type Schemas](#event-type-schemas)
4. [Validation Rules](#validation-rules)
5. [Examples](#examples)

---

## Format Overview

### File Format

**JSONL (JSON Lines)**:
- One JSON object per line
- No comma separators between objects
- Each line is independently parseable

**File Naming**:
```
.claude/Telemetry/logs/events-YYYY-MM.jsonl
```

**Example File**:
```jsonl
{"timestamp":"2025-12-26T10:30:00Z","event_type":"skill_execution","skill":"systematic-debugger","outcome":"success"}
{"timestamp":"2025-12-26T11:15:00Z","event_type":"safety_validation","violation_type":"duty_hours_80","outcome":"violation_prevented"}
{"timestamp":"2025-12-26T14:20:00Z","event_type":"schedule_generation","outcome":"success","duration_seconds":247.3}
```

---

## Base Event Schema

**All events** must include these required fields:

```typescript
interface BaseTelemetryEvent {
  // REQUIRED FIELDS
  timestamp: string;        // ISO 8601 UTC timestamp (YYYY-MM-DDTHH:MM:SSZ)
  event_type: EventType;    // Event category (see Event Types below)

  // OPTIONAL COMMON FIELDS
  environment?: "local" | "staging" | "production";
  session_id?: string;      // Agent session identifier
  metadata?: Record<string, any>;  // Additional context (use sparingly)
}
```

### Timestamp Format

**MUST** use ISO 8601 format with UTC timezone:
```
YYYY-MM-DDTHH:MM:SSZ
```

**Valid Examples**:
- ✅ `2025-12-26T10:30:00Z`
- ✅ `2025-12-26T14:22:15.123Z` (milliseconds optional)

**Invalid Examples**:
- ❌ `2025-12-26T10:30:00` (missing Z)
- ❌ `2025-12-26T10:30:00-05:00` (use UTC, not local timezone)
- ❌ `2025-12-26 10:30:00` (wrong separator)

---

## Event Type Schemas

### 1. Skill Execution

```typescript
interface SkillExecutionEvent extends BaseTelemetryEvent {
  event_type: "skill_execution";
  skill: string;                    // Skill name (e.g., "systematic-debugger")
  outcome: "success" | "error" | "rollback" | "handoff";
  duration_seconds: number;         // Time to complete (float)

  // Optional
  context_tokens?: number;          // Context window size used
  tool_calls?: number;              // Number of tool invocations
  error_type?: string;              // If outcome="error"
  error_message?: string;           // Sanitized error (no PII/PHI)
}
```

**Example**:
```json
{
  "timestamp": "2025-12-26T10:30:00Z",
  "event_type": "skill_execution",
  "skill": "acgme-compliance",
  "outcome": "success",
  "duration_seconds": 120.5,
  "context_tokens": 15000,
  "tool_calls": 8
}
```

---

### 2. Safety Validation

```typescript
interface SafetyValidationEvent extends BaseTelemetryEvent {
  event_type: "safety_validation";
  outcome: "violation_prevented" | "violation_deployed" | "compliant";
  violation_type?: "duty_hours_80" | "rest_period_1in7" | "supervision_ratio" | "shift_duration_24plus2";
  severity?: "critical" | "warning";
  source: "schedule_generation" | "swap_validation" | "manual_assignment" | "automated_monitoring";

  // Optional
  details?: {
    projected_hours?: number;
    limit?: number;
    rolling_period?: string;
    swap_blocked?: boolean;
  };
  action_taken?: string;            // What AI did in response
}
```

**Example**:
```json
{
  "timestamp": "2025-12-26T14:22:00Z",
  "event_type": "safety_validation",
  "outcome": "violation_prevented",
  "violation_type": "duty_hours_80",
  "severity": "critical",
  "source": "swap_validation",
  "details": {
    "projected_hours": 82.5,
    "limit": 80.0,
    "rolling_period": "4_weeks"
  },
  "action_taken": "reject_swap_request"
}
```

---

### 3. Schedule Generation

```typescript
interface ScheduleGenerationEvent extends BaseTelemetryEvent {
  event_type: "schedule_generation";
  outcome: "success" | "error" | "timeout" | "unsatisfiable";
  duration_seconds: number;

  // Optional
  block?: number;                   // Block number (1-10)
  academic_year?: string;           // e.g., "2025-2026"
  constraint_satisfaction?: {
    hard: number;                   // 0.0 to 1.0 (should be 1.0)
    soft: number;                   // 0.0 to 1.0
    preference: number;             // 0.0 to 1.0
  };
  optimality_score?: number;        // 0.0 to 100.0
  solver?: string;                  // e.g., "OR-Tools CP-SAT"
  iterations?: number;              // Solver iterations
  error_type?: string;              // If outcome != "success"
}
```

**Example**:
```json
{
  "timestamp": "2025-12-26T09:15:00Z",
  "event_type": "schedule_generation",
  "outcome": "success",
  "duration_seconds": 247.3,
  "block": 10,
  "academic_year": "2025-2026",
  "constraint_satisfaction": {
    "hard": 1.0,
    "soft": 0.873,
    "preference": 0.645
  },
  "optimality_score": 87.3,
  "solver": "OR-Tools CP-SAT",
  "iterations": 15000
}
```

---

### 4. Swap Processing

```typescript
interface SwapProcessingEvent extends BaseTelemetryEvent {
  event_type: "swap_suggestion" | "swap_validation" | "swap_execution";
  outcome: "accepted" | "rejected" | "error";
  swap_type: "one_to_one" | "absorb" | "multi_way";

  // For swap_suggestion
  match_confidence?: number;        // 0.0 to 1.0
  criteria_met?: string[];          // Matching criteria satisfied

  // For swap_execution
  swaps_affected?: number;          // Number of swaps in transaction
  rollback?: boolean;               // Was this swap rolled back?

  // Common
  processing_time_seconds?: number;
  error_type?: string;
}
```

**Example**:
```json
{
  "timestamp": "2025-12-26T11:30:00Z",
  "event_type": "swap_suggestion",
  "outcome": "accepted",
  "swap_type": "one_to_one",
  "match_confidence": 0.89,
  "criteria_met": [
    "credential_match",
    "availability_overlap",
    "acgme_safe"
  ],
  "processing_time_seconds": 1.8
}
```

---

### 5. MCP Tool Call

```typescript
interface MCPToolCallEvent extends BaseTelemetryEvent {
  event_type: "mcp_tool_call";
  tool_name: string;                // e.g., "validate_schedule", "suggest_swaps"
  outcome: "success" | "error";
  duration_seconds: number;

  // Optional
  parameters?: Record<string, any>; // Tool input params (sanitized)
  error_type?: string;              // e.g., "TimeoutError", "ValidationError"
  retry_count?: number;             // Number of retries attempted
  recovery?: string;                // Recovery action taken
}
```

**Example**:
```json
{
  "timestamp": "2025-12-26T10:12:00Z",
  "event_type": "mcp_tool_call",
  "tool_name": "suggest_swaps",
  "outcome": "error",
  "error_type": "TimeoutError",
  "duration_seconds": 30.0,
  "parameters": {
    "date_range": "2025-01-01_to_2025-03-31",
    "rotation": "inpatient"
  },
  "retry_count": 2,
  "recovery": "cache_stale_result"
}
```

---

### 6. Compliance Warning

```typescript
interface ComplianceWarningEvent extends BaseTelemetryEvent {
  event_type: "compliance_warning";
  warning_type: "approaching_80hrs" | "consecutive_shifts" | "n1_failure" | "coverage_gap" | "credential_expiring";
  severity: "info" | "warning" | "critical";
  response: "acknowledged" | "ignored" | "auto_resolved";

  // Optional
  details?: {
    current_hours?: number;
    limit?: number;
    remaining_capacity?: number;
    days_until_reset?: number;
  };
  notification_sent?: boolean;
}
```

**Example**:
```json
{
  "timestamp": "2025-12-26T08:00:00Z",
  "event_type": "compliance_warning",
  "warning_type": "approaching_80hrs",
  "severity": "warning",
  "details": {
    "current_hours": 76.5,
    "limit": 80.0,
    "remaining_capacity": 3.5,
    "days_until_reset": 4
  },
  "response": "acknowledged",
  "notification_sent": true
}
```

---

### 7. Agent Task

```typescript
interface AgentTaskEvent extends BaseTelemetryEvent {
  event_type: "agent_task";
  skill?: string;                   // Skill used (if any)
  task_type: "debugging" | "testing" | "validation" | "generation" | "optimization";
  outcome: "success" | "error" | "rollback" | "handoff";
  duration_seconds: number;

  // Optional
  context_tokens?: number;
  tool_calls?: number;
  error_type?: string;
  error_message?: string;           // Sanitized
  recovery_action?: string;         // e.g., "escalate_to_human", "retry"
}
```

**Example**:
```json
{
  "timestamp": "2025-12-26T16:45:00Z",
  "event_type": "agent_task",
  "skill": "schedule-optimization",
  "task_type": "generation",
  "outcome": "error",
  "duration_seconds": 320.5,
  "error_type": "ConstraintUnsatisfiable",
  "error_message": "Cannot satisfy hard constraint: supervision_ratio for Block 10",
  "context_tokens": 45000,
  "tool_calls": 18,
  "recovery_action": "escalate_to_human"
}
```

---

### 8. Rollback

```typescript
interface RollbackEvent extends BaseTelemetryEvent {
  event_type: "rollback";
  reason: "validation_failure" | "acgme_violation" | "user_rejection" | "system_error";
  severity: "minor" | "major" | "critical";

  // Optional
  details?: {
    original_operation?: string;
    swaps_affected?: number;
    validation_error?: string;
    rollback_duration_seconds?: number;
    database_state?: string;
  };
  learning_entry?: string;          // e.g., "LEARN-2025-094"
}
```

**Example**:
```json
{
  "timestamp": "2025-12-26T13:50:00Z",
  "event_type": "rollback",
  "reason": "validation_failure",
  "severity": "minor",
  "details": {
    "original_operation": "bulk_swap_execution",
    "swaps_affected": 3,
    "validation_error": "credential_expiration_detected",
    "rollback_duration_seconds": 2.1,
    "database_state": "restored"
  },
  "learning_entry": "LEARN-2025-094"
}
```

---

### 9. Commit

```typescript
interface CommitEvent extends BaseTelemetryEvent {
  event_type: "commit";
  commit_hash: string;              // Git commit SHA
  skill?: string;                   // Skill that assisted (if any)

  // Optional
  pr_number?: number;               // GitHub PR number
  files_changed?: number;
  lines_added?: number;
  lines_deleted?: number;
}
```

**Example**:
```json
{
  "timestamp": "2025-12-26T16:00:00Z",
  "event_type": "commit",
  "commit_hash": "d0efcc5a",
  "skill": "systematic-debugger",
  "pr_number": 248,
  "files_changed": 3,
  "lines_added": 87,
  "lines_deleted": 12
}
```

---

### 10. Learning Entry

```typescript
interface LearningEntryEvent extends BaseTelemetryEvent {
  event_type: "learning_created";
  learning_id: string;              // e.g., "LEARN-2025-042"
  severity: "info" | "warning" | "critical";
  source: "incident" | "observation" | "experiment" | "user_feedback";

  // Optional
  implemented?: boolean;            // Has learning been implemented?
  time_to_implementation_seconds?: number;  // If implemented
}
```

**Example**:
```json
{
  "timestamp": "2025-12-26T11:15:00Z",
  "event_type": "learning_created",
  "learning_id": "LEARN-2025-042",
  "severity": "warning",
  "source": "observation"
}
```

---

## Validation Rules

### Required Field Rules

1. **timestamp**: MUST be valid ISO 8601 UTC format
2. **event_type**: MUST be one of the defined event types
3. **outcome** (if present): MUST be one of the allowed values
4. **duration_seconds** (if present): MUST be positive number

### Data Type Rules

```typescript
// Numbers
duration_seconds: number       // Positive float (e.g., 120.5)
context_tokens: number         // Positive integer (e.g., 15000)
tool_calls: number             // Non-negative integer (e.g., 0, 8, 23)
constraint_satisfaction: number // Float 0.0 to 1.0
optimality_score: number       // Float 0.0 to 100.0

// Strings
skill: string                  // Lowercase with hyphens (e.g., "systematic-debugger")
event_type: string             // Snake_case (e.g., "skill_execution")
outcome: string                // Lowercase (e.g., "success", "error")

// Booleans
rollback: boolean              // true or false (not "true" or "false" strings)
```

### Privacy Rules

**NEVER include**:
- Resident/faculty names
- Personal identifiers (emails, SSN, etc.)
- Schedule assignments (specific dates with person IDs)
- PHI or PII
- Credentials or secrets

**Sanitization Examples**:

❌ **Bad** (leaks data):
```json
{"event_type": "swap_rejected", "person": "Dr. John Smith", "email": "john.smith@example.mil"}
```

✅ **Good** (sanitized):
```json
{"event_type": "swap_rejected", "person_id_hash": "a3f2c8", "violation_type": "duty_hours_80"}
```

---

## Examples

### Complete Event Log Session

```jsonl
{"timestamp":"2025-12-26T08:00:00Z","event_type":"compliance_warning","warning_type":"approaching_80hrs","severity":"warning","details":{"current_hours":76.5,"limit":80.0},"response":"acknowledged"}
{"timestamp":"2025-12-26T09:15:00Z","event_type":"schedule_generation","outcome":"success","duration_seconds":247.3,"block":10,"constraint_satisfaction":{"hard":1.0,"soft":0.873}}
{"timestamp":"2025-12-26T10:12:00Z","event_type":"mcp_tool_call","tool_name":"validate_schedule","outcome":"success","duration_seconds":1.8}
{"timestamp":"2025-12-26T10:30:00Z","event_type":"skill_execution","skill":"acgme-compliance","outcome":"success","duration_seconds":120.5,"context_tokens":15000}
{"timestamp":"2025-12-26T11:15:00Z","event_type":"learning_created","learning_id":"LEARN-2025-042","severity":"warning","source":"observation"}
{"timestamp":"2025-12-26T11:30:00Z","event_type":"swap_suggestion","outcome":"accepted","swap_type":"one_to_one","match_confidence":0.89}
{"timestamp":"2025-12-26T13:50:00Z","event_type":"rollback","reason":"validation_failure","severity":"minor","learning_entry":"LEARN-2025-094"}
{"timestamp":"2025-12-26T14:22:00Z","event_type":"safety_validation","outcome":"violation_prevented","violation_type":"duty_hours_80","severity":"critical","source":"swap_validation"}
{"timestamp":"2025-12-26T16:00:00Z","event_type":"commit","commit_hash":"d0efcc5a","skill":"systematic-debugger","pr_number":248}
{"timestamp":"2025-12-26T16:45:00Z","event_type":"agent_task","skill":"schedule-optimization","task_type":"generation","outcome":"error","duration_seconds":320.5}
```

---

## Parsing & Querying

### Reading JSONL Files

**Python**:
```python
import json
from pathlib import Path

def read_events(log_file: Path):
    """Read all events from JSONL file."""
    events = []
    with log_file.open() as f:
        for line in f:
            events.append(json.loads(line))
    return events
```

**Bash (jq)**:
```bash
# Count events by type
jq -r '.event_type' events.jsonl | sort | uniq -c

# Filter by date range
jq 'select(.timestamp >= "2025-12-20T00:00:00Z" and .timestamp < "2025-12-27T00:00:00Z")' events.jsonl

# Get all violations prevented
jq 'select(.event_type == "safety_validation" and .outcome == "violation_prevented")' events.jsonl
```

---

**Remember**: Logs are for machines AND humans. Keep them structured for parsing, but readable for debugging.
