# AI Infrastructure Performance Metrics

> **Purpose**: Measure AI infrastructure effectiveness in medical residency scheduling
> **Last Updated**: 2025-12-26
> **Owner**: META_UPDATER skill + Program Director
> **Domain**: ACGME-compliant residency program scheduling

---

## Table of Contents

1. [Purpose](#purpose)
2. [Why Measure AI Infrastructure](#why-measure-ai-infrastructure)
3. [Metric Categories](#metric-categories)
   - [Safety Metrics](#safety-metrics)
   - [Quality Metrics](#quality-metrics)
   - [Efficiency Metrics](#efficiency-metrics)
   - [Reliability Metrics](#reliability-metrics)
4. [Collection Methods](#collection-methods)
5. [Aggregation and Reporting](#aggregation-and-reporting)
6. [Example Log Entries](#example-log-entries)
7. [Dashboard Integration](#dashboard-integration)
8. [Privacy Considerations](#privacy-considerations)
9. [Getting Started](#getting-started)

---

## Purpose

This document defines **how we measure AI infrastructure performance** in the context of medical residency scheduling. Unlike traditional application monitoring (Prometheus, Grafana for uptime and latency), these metrics focus on **AI agent effectiveness** in maintaining ACGME compliance, preventing violations, and improving scheduling quality.

### Key Questions We Answer

- **Safety**: How many ACGME violations did AI prevent this week?
- **Quality**: What percentage of generated schedules meet all constraints?
- **Efficiency**: How much time did AI save vs. manual scheduling?
- **Reliability**: How often do AI agents fail or require rollback?

---

## Why Measure AI Infrastructure

### 1. Continuous Improvement

Track AI performance over time to identify:
- Skills that need enhancement
- Patterns in failures
- Opportunities for automation
- Learning velocity

### 2. Safety Validation

In a medical residency scheduling system, AI mistakes can lead to:
- **ACGME violations**: Duty hour limits exceeded, insufficient rest periods
- **Coverage gaps**: Emergency departments understaffed
- **Compliance failures**: Supervision ratios not met
- **Burnout risk**: Residents overworked, N-1 contingency failures

**Metrics validate AI is making scheduling safer, not riskier.**

### 3. ROI Demonstration

Quantify value delivered by AI infrastructure:
- Time saved per schedule generation
- Violations caught before deployment
- Swap conflicts prevented
- Manual interventions reduced

### 4. Operational Transparency

Program Directors and administrators need visibility into:
- What AI is doing (skill usage patterns)
- How well it's working (success rates)
- When it needs help (handoff frequency)
- Where to invest in improvements (skill gaps)

---

## Metric Categories

### Safety Metrics

**Purpose**: Measure AI's effectiveness at preventing harm and maintaining ACGME compliance.

#### `safety_violations_prevented_total`

**Description**: Number of ACGME violations prevented by AI validation before schedule deployment.

**Type**: Counter

**Labels**:
- `violation_type`: `duty_hours_80`, `rest_period_1in7`, `supervision_ratio`, `shift_duration_24plus2`
- `severity`: `critical`, `warning`
- `source`: `schedule_generation`, `swap_validation`, `manual_assignment`

**Example Values**:
```
safety_violations_prevented_total{violation_type="duty_hours_80",severity="critical",source="swap_validation"} 12
safety_violations_prevented_total{violation_type="rest_period_1in7",severity="warning",source="schedule_generation"} 8
```

**Target**: Maximize (more prevented = AI working correctly)

**Alert**: If this drops significantly week-over-week, AI validation may be regressing

---

#### `safety_violations_deployed_total`

**Description**: Number of ACGME violations that made it into production schedules (AI missed them).

**Type**: Counter

**Labels**:
- `violation_type`: Same as above
- `severity`: `critical`, `warning`
- `detection_method`: `manual_audit`, `resident_report`, `automated_monitoring`

**Example Values**:
```
safety_violations_deployed_total{violation_type="duty_hours_80",severity="critical",detection_method="automated_monitoring"} 0
safety_violations_deployed_total{violation_type="supervision_ratio",severity="warning",detection_method="manual_audit"} 1
```

**Target**: 0 critical violations, <3 warnings per month

**Alert**: Any critical violation triggers immediate investigation

---

#### `safety_compliance_warnings_total`

**Description**: Proactive warnings issued before violations occur (early warning system).

**Type**: Counter

**Labels**:
- `warning_type`: `approaching_80hrs`, `consecutive_shifts`, `n1_failure`, `coverage_gap`
- `response`: `acknowledged`, `ignored`, `auto_resolved`

**Example Values**:
```
safety_compliance_warnings_total{warning_type="approaching_80hrs",response="acknowledged"} 34
safety_compliance_warnings_total{warning_type="n1_failure",response="auto_resolved"} 5
```

**Target**: High warning rate with high acknowledgment rate = proactive safety culture

---

#### `safety_emergency_overrides_total`

**Description**: Number of times safety rules were manually overridden (requires admin approval).

**Type**: Counter

**Labels**:
- `override_type`: `emergency_coverage`, `training_requirement`, `military_deployment`
- `approved_by`: `program_director`, `coordinator`, `emergency_protocol`

**Example Values**:
```
safety_emergency_overrides_total{override_type="emergency_coverage",approved_by="program_director"} 3
safety_emergency_overrides_total{override_type="military_deployment",approved_by="emergency_protocol"} 1
```

**Target**: Minimize (each override is a deviation from policy)

**Alert**: Spike in overrides may indicate systemic scheduling problem

---

### Quality Metrics

**Purpose**: Measure AI's ability to generate high-quality, constraint-satisfying schedules.

#### `quality_schedule_generation_success_rate`

**Description**: Percentage of schedule generation attempts that produce valid schedules.

**Type**: Gauge (derived from counter)

**Calculation**:
```
sum(schedule_generation_total{outcome="success"})
/
sum(schedule_generation_total)
```

**Example Values**:
```
quality_schedule_generation_success_rate 0.957  # 95.7% success
```

**Target**: >95%

**Alert**: <90% indicates constraint conflicts or solver issues

---

#### `quality_constraint_satisfaction_percent`

**Description**: Percentage of constraints satisfied in generated schedules (hard + soft).

**Type**: Histogram

**Buckets**: [80, 85, 90, 95, 98, 100]

**Labels**:
- `constraint_type`: `hard`, `soft`, `preference`
- `block`: Block number (1-10) for academic year

**Example Values**:
```
quality_constraint_satisfaction_percent{constraint_type="hard",block="10"} 100.0  # All hard constraints met
quality_constraint_satisfaction_percent{constraint_type="soft",block="10"} 87.3   # 87.3% soft constraints
```

**Target**: 100% hard, >85% soft

---

#### `quality_swap_auto_match_accuracy`

**Description**: How often auto-matched swaps are actually feasible and accepted.

**Type**: Gauge (derived)

**Calculation**:
```
sum(swap_suggestions_total{outcome="accepted"})
/
sum(swap_suggestions_total)
```

**Example Values**:
```
quality_swap_auto_match_accuracy 0.823  # 82.3% of suggestions accepted
```

**Target**: >75%

**Alert**: <60% means auto-matcher is suggesting too many infeasible swaps

---

#### `quality_conflict_detection_false_positive_rate`

**Description**: Percentage of flagged conflicts that were actually valid (false alarms).

**Type**: Gauge (derived)

**Labels**:
- `conflict_type`: `time_overlap`, `credential_missing`, `rest_period`, `supervision`

**Example Values**:
```
quality_conflict_detection_false_positive_rate{conflict_type="time_overlap"} 0.05  # 5% false positives
quality_conflict_detection_false_positive_rate{conflict_type="credential_missing"} 0.12  # 12% false positives
```

**Target**: <10%

**Alert**: >20% means conflict detector is too sensitive

---

#### `quality_schedule_optimality_score`

**Description**: Objective score for schedule quality (multi-objective optimization).

**Type**: Gauge

**Components**:
- Coverage adequacy (0-100)
- Workload balance (0-100)
- Preference satisfaction (0-100)
- Credential utilization (0-100)

**Example Values**:
```
quality_schedule_optimality_score{component="coverage_adequacy"} 98.5
quality_schedule_optimality_score{component="workload_balance"} 87.2
quality_schedule_optimality_score{component="preference_satisfaction"} 72.3
```

**Target**: All components >80

---

### Efficiency Metrics

**Purpose**: Measure time and resource savings from AI automation.

#### `efficiency_time_saved_seconds`

**Description**: Time saved by AI vs. manual scheduling process.

**Type**: Histogram

**Buckets**: [600, 1800, 3600, 7200, 14400, 28800, 86400]  # 10min to 1 day

**Labels**:
- `task`: `schedule_generation`, `swap_processing`, `conflict_resolution`, `coverage_check`

**Example Values**:
```
efficiency_time_saved_seconds_sum{task="schedule_generation"} 172800  # 48 hours saved
efficiency_time_saved_seconds_count{task="schedule_generation"} 4  # 4 schedules generated
# Average: 12 hours saved per schedule generation
```

**Target**: Median >2 hours saved for schedule generation

---

#### `efficiency_agent_task_completion_time_seconds`

**Description**: Time from agent invocation to task completion.

**Type**: Histogram

**Buckets**: [10, 30, 60, 180, 300, 600, 1800, 3600]

**Labels**:
- `skill`: Skill name
- `task_type`: `debugging`, `testing`, `validation`, `generation`

**Example Values**:
```
efficiency_agent_task_completion_time_seconds_sum{skill="schedule-optimization",task_type="generation"} 2700
efficiency_agent_task_completion_time_seconds_count{skill="schedule-optimization",task_type="generation"} 4
# Median: ~11 minutes per schedule generation task
```

**Target**: p50 <5 min for most tasks, p95 <30 min

---

#### `efficiency_context_reuse_rate`

**Description**: How often agents reuse context from previous tasks (reduces recomputation).

**Type**: Gauge (derived)

**Calculation**:
```
sum(agent_tasks_total{context_source="reused"})
/
sum(agent_tasks_total)
```

**Example Values**:
```
efficiency_context_reuse_rate 0.67  # 67% of tasks reuse context
```

**Target**: >60%

**Interpretation**: Higher is better (less redundant work)

---

#### `efficiency_skill_cache_hit_rate`

**Description**: Percentage of skill invocations that use cached prompts vs. loading from disk.

**Type**: Gauge (derived)

**Example Values**:
```
efficiency_skill_cache_hit_rate 0.89  # 89% cache hits
```

**Target**: >80%

---

#### `efficiency_manual_intervention_rate`

**Description**: Percentage of AI-generated outputs requiring human correction.

**Type**: Gauge (derived)

**Labels**:
- `task_type`: `schedule`, `swap`, `coverage`, `validation`

**Example Values**:
```
efficiency_manual_intervention_rate{task_type="schedule"} 0.12  # 12% need manual fixes
efficiency_manual_intervention_rate{task_type="swap"} 0.05     # 5% need manual fixes
```

**Target**: <10%

**Alert**: >20% means AI is creating more work, not saving time

---

### Reliability Metrics

**Purpose**: Measure AI system dependability and error recovery.

#### `reliability_agent_task_failure_rate`

**Description**: Percentage of agent tasks that fail to complete.

**Type**: Gauge (derived)

**Calculation**:
```
sum(agent_tasks_total{outcome="error"})
/
sum(agent_tasks_total)
```

**Example Values**:
```
reliability_agent_task_failure_rate 0.043  # 4.3% failure rate
```

**Target**: <5%

**Alert**: >10% indicates systemic reliability issue

---

#### `reliability_mcp_tool_error_rate`

**Description**: Percentage of MCP tool calls that return errors.

**Type**: Gauge (derived)

**Labels**:
- `tool_name`: MCP tool (e.g., `validate_schedule`, `find_conflicts`, `suggest_swaps`)
- `error_type`: `timeout`, `validation_error`, `database_error`, `constraint_error`

**Example Values**:
```
reliability_mcp_tool_error_rate{tool_name="validate_schedule",error_type="constraint_error"} 0.02  # 2%
reliability_mcp_tool_error_rate{tool_name="suggest_swaps",error_type="timeout"} 0.08  # 8%
```

**Target**: <3%

**Alert**: >10% for any tool triggers investigation

---

#### `reliability_rollback_frequency`

**Description**: How often AI-generated changes are rolled back.

**Type**: Counter

**Labels**:
- `reason`: `validation_failure`, `acgme_violation`, `user_rejection`, `system_error`
- `severity`: `minor`, `major`, `critical`

**Example Values**:
```
reliability_rollback_frequency{reason="validation_failure",severity="minor"} 3
reliability_rollback_frequency{reason="acgme_violation",severity="critical"} 1
```

**Target**: <2 per month, 0 critical rollbacks

---

#### `reliability_recovery_time_seconds`

**Description**: Time from failure detection to recovery (MTTR).

**Type**: Histogram

**Buckets**: [60, 300, 600, 1800, 3600, 7200, 14400]  # 1min to 4 hours

**Labels**:
- `failure_type`: `skill_error`, `mcp_timeout`, `constraint_unsatisfiable`, `database_deadlock`

**Example Values**:
```
reliability_recovery_time_seconds_sum{failure_type="constraint_unsatisfiable"} 2400  # 40 min total
reliability_recovery_time_seconds_count{failure_type="constraint_unsatisfiable"} 3
# Median recovery: ~13 minutes
```

**Target**: p50 <10 min, p95 <30 min

---

#### `reliability_uptime_percent`

**Description**: Percentage of time AI infrastructure is operational (24/7 availability).

**Type**: Gauge

**Components**:
- MCP server uptime
- Agent availability
- Database connectivity

**Example Values**:
```
reliability_uptime_percent{component="mcp_server"} 99.8
reliability_uptime_percent{component="agent"} 99.95
reliability_uptime_percent{component="database"} 99.99
```

**Target**: >99.5% (3.6 hours downtime per month max)

---

## Collection Methods

### Where to Log

All telemetry events are logged to:
```
.claude/Telemetry/logs/
├── events-YYYY-MM.jsonl      # Raw events (monthly files)
├── daily/
│   └── YYYY-MM-DD.jsonl      # Daily rollup for quick access
└── archives/
    └── YYYY/                  # Historical data (yearly)
```

**File Rotation**:
- Raw events: Monthly files, keep 90 days, then archive
- Daily rollups: Keep 1 year
- Archives: Keep indefinitely (compressed)

---

### Log Format

**All logs use structured JSON** (JSONL format: one JSON object per line).

See `.claude/Telemetry/LOG_FORMAT.md` for complete schema.

**Example**:
```jsonl
{"timestamp":"2025-12-26T10:30:00Z","event_type":"safety_validation","violation_prevented":"duty_hours_80","severity":"critical","source":"swap_validation"}
{"timestamp":"2025-12-26T11:15:00Z","event_type":"schedule_generation","outcome":"success","duration_seconds":247.3,"constraint_satisfaction":0.873}
```

---

### Sampling Strategy

#### Full Logging (100% capture)

Log every occurrence for:
- ✅ Safety violations (prevented or deployed)
- ✅ Emergency overrides
- ✅ Rollbacks
- ✅ Critical errors

#### Sampled Logging (statistical sampling)

For high-frequency events, sample at:
- **10%**: MCP tool calls (except errors, log 100%)
- **25%**: Context reuse events
- **50%**: Skill cache hits

**Why sample?**: Reduce log volume while maintaining statistical validity.

---

### Privacy Considerations

**NEVER log**:
- ❌ Resident/faculty names
- ❌ Personal identifiers (emails, phone numbers)
- ❌ Schedule assignments (specific dates, rotations)
- ❌ PHI (medical records, patient data)
- ❌ Credentials, API keys, secrets

**Safe to log**:
- ✅ Skill names, agent names
- ✅ Error types (sanitized messages)
- ✅ Metric counts and durations
- ✅ Violation types (without person data)
- ✅ Constraint satisfaction percentages
- ✅ Timestamps (UTC only)

**Sanitization Example**:
```python
# BAD - leaks name
log_event("swap_rejected", person="Dr. John Smith", reason="duty_hours_80")

# GOOD - sanitized
log_event("swap_rejected", person_id_hash="a3f2c8", reason="duty_hours_80")
```

---

### Automated Collection

#### 1. Git Hooks

```bash
# .git/hooks/post-commit
#!/bin/bash
# Log commits with skill attribution

COMMIT_HASH=$(git rev-parse HEAD)
COMMIT_MSG=$(git log -1 --pretty=%B)

if echo "$COMMIT_MSG" | grep -q "\[skill:"; then
  SKILL=$(echo "$COMMIT_MSG" | grep -oP '\[skill:\K[^\]]+')

  jq -n \
    --arg ts "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    --arg skill "$SKILL" \
    --arg hash "$COMMIT_HASH" \
    '{timestamp: $ts, event_type: "commit", skill: $skill, commit_hash: $hash}' \
    >> .claude/Telemetry/logs/events-$(date +%Y-%m).jsonl
fi
```

---

#### 2. MCP Tool Instrumentation

```python
# scheduler_mcp/telemetry.py
"""Telemetry wrapper for MCP tools."""
import time
import json
from datetime import datetime
from pathlib import Path
from functools import wraps

TELEMETRY_LOG = Path(".claude/Telemetry/logs/events-{date}.jsonl")

def track_mcp_tool(tool_name: str):
    """Decorator to track MCP tool execution."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start = time.time()
            outcome = "success"
            error_type = None

            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                outcome = "error"
                error_type = type(e).__name__
                raise
            finally:
                duration = time.time() - start

                event = {
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "event_type": "mcp_tool_call",
                    "tool_name": tool_name,
                    "outcome": outcome,
                    "duration_seconds": round(duration, 3),
                    "error_type": error_type
                }

                log_file = TELEMETRY_LOG.format(
                    date=datetime.utcnow().strftime("%Y-%m")
                )
                Path(log_file).parent.mkdir(parents=True, exist_ok=True)

                with open(log_file, "a") as f:
                    f.write(json.dumps(event) + "\n")

        return wrapper
    return decorator

# Usage in MCP tools
@track_mcp_tool("validate_schedule")
async def validate_schedule(schedule_id: str) -> dict:
    """Validate schedule against ACGME rules."""
    # ... implementation ...
```

---

#### 3. Skill Execution Logging

```python
# .claude/scripts/log_skill_execution.py
"""Log skill execution metrics."""
import json
from datetime import datetime
from pathlib import Path

def log_skill_execution(
    skill_name: str,
    outcome: str,
    duration_seconds: float,
    context_tokens: int = None,
    tool_calls: int = None
):
    """
    Log skill execution event.

    Args:
        skill_name: Name of skill executed
        outcome: success | error | rollback | handoff
        duration_seconds: Time to complete task
        context_tokens: Context window size used
        tool_calls: Number of tool invocations
    """
    event = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "event_type": "skill_execution",
        "skill": skill_name,
        "outcome": outcome,
        "duration_seconds": round(duration_seconds, 1)
    }

    if context_tokens:
        event["context_tokens"] = context_tokens
    if tool_calls:
        event["tool_calls"] = tool_calls

    log_file = Path(f".claude/Telemetry/logs/events-{datetime.utcnow():%Y-%m}.jsonl")
    log_file.parent.mkdir(parents=True, exist_ok=True)

    with log_file.open("a") as f:
        f.write(json.dumps(event) + "\n")

# Example usage (add to skill epilogue)
# log_skill_execution("acgme-compliance", "success", 120.5, 15000, 8)
```

---

## Aggregation and Reporting

### Weekly Digest

**Automated Report** (generated every Monday by META_UPDATER or cron):

```markdown
# AI Infrastructure Weekly Digest
**Week of**: 2025-12-22 to 2025-12-28

## Safety Metrics
- **Violations Prevented**: 47 total (12 critical, 35 warnings)
  - Duty hours (80-hour rule): 28
  - Rest periods (1-in-7): 12
  - Supervision ratios: 7
- **Violations Deployed**: 0 critical, 1 warning (manual audit catch)
- **Emergency Overrides**: 2 (both approved by Program Director)

## Quality Metrics
- **Schedule Generation Success**: 95.7% (4 of 4 attempts succeeded)
- **Constraint Satisfaction**: 100% hard, 87.3% soft
- **Swap Auto-Match Accuracy**: 82.3% (14 of 17 suggestions accepted)

## Efficiency Metrics
- **Time Saved**: 48 hours total (12 hrs per schedule generation)
- **Manual Intervention Rate**: 8% (1 of 12 AI outputs needed fixes)
- **Agent Task Completion Time**: Median 4.2 min (p95: 12.8 min)

## Reliability Metrics
- **Agent Failure Rate**: 4.3% (2 of 47 tasks failed)
- **MCP Tool Errors**: 2.1% average (suggest_swaps: 8% timeout rate ⚠️)
- **Rollbacks**: 1 (minor validation failure)
- **Uptime**: 99.9% (all systems operational)

## Alerts
⚠️ **Warning**: suggest_swaps MCP tool timeout rate elevated (8%, threshold 3%)
   - Action: Investigate database query performance
   - Owner: Tech Lead

## Top Skills Used
1. systematic-debugger: 12 invocations
2. acgme-compliance: 8 invocations
3. schedule-optimization: 4 invocations
```

---

### Monthly Trend Analysis

**Generated by META_UPDATER** (first Monday of each month):

```markdown
# AI Infrastructure Monthly Report
**Month**: December 2025

## Trends (vs. November 2025)

### Safety
- Violations Prevented: 182 (+23% ↑)
- Violations Deployed: 1 critical, 4 warnings (-50% ↓ from Nov)
- Safety Score: 98.7% (+1.2% ↑)

### Quality
- Schedule Success Rate: 96.2% (+0.8% ↑)
- Constraint Satisfaction: 88.1% (+3.2% ↑)
- False Positive Rate: 7.3% (-2.1% ↓)

### Efficiency
- Total Time Saved: 192 hours (+15% ↑)
- Manual Intervention: 9.2% (-3.4% ↓)
- Median Task Time: 4.5 min (+0.3 min, stable)

### Reliability
- Agent Failure Rate: 4.1% (-0.7% ↓)
- MCP Error Rate: 2.8% (+0.5% ↑ ⚠️)
- Uptime: 99.8% (target met)

## Key Learnings This Month
- 14 new learning entries created
- 12 implemented (86% implementation rate)
- 2 pending (both low priority)

## Recommendations
1. **Investigate MCP timeout increase**: suggest_swaps tool needs optimization
2. **Enhance swap auto-matcher**: 82% accuracy good, aim for 90%
3. **Add soft constraint for clinic preferences**: Would improve satisfaction by ~5%
```

---

### Alert Thresholds

| Metric | Warning | Critical | Action |
|--------|---------|----------|--------|
| **Violations Deployed (critical)** | 1 per month | 2 per month | Immediate investigation + rollback |
| **Schedule Success Rate** | <90% | <80% | Review constraint conflicts |
| **Agent Failure Rate** | >8% | >15% | Skill debugging session |
| **MCP Error Rate** | >5% | >10% | Database/API investigation |
| **Rollback Frequency** | >3 per month | >5 per month | Validation process review |
| **Manual Intervention** | >15% | >25% | AI creating more work than saving |

---

### Dashboard Integration

**Grafana Panels** (future integration):

1. **Safety Overview**
   - Violations prevented (bar chart, by type)
   - Violations deployed (time series, alert on non-zero)
   - Emergency overrides (count by week)

2. **Quality Dashboard**
   - Schedule success rate (gauge: 0-100%)
   - Constraint satisfaction (stacked area: hard vs soft)
   - Swap match accuracy (line chart, trending)

3. **Efficiency Monitor**
   - Time saved cumulative (area chart)
   - Task completion time distribution (heatmap)
   - Manual intervention rate (line chart)

4. **Reliability Status**
   - Agent failure rate (gauge with thresholds)
   - MCP tool errors (table, sorted by error rate)
   - System uptime (gauge: 99-100%)

---

## Example Log Entries

### Schedule Generation Success

```json
{
  "timestamp": "2025-12-26T09:15:00Z",
  "event_type": "schedule_generation",
  "outcome": "success",
  "duration_seconds": 247.3,
  "constraint_satisfaction": {
    "hard": 1.0,
    "soft": 0.873,
    "preference": 0.645
  },
  "block": 10,
  "academic_year": "2025-2026",
  "optimality_score": 87.3,
  "solver": "OR-Tools CP-SAT",
  "iterations": 15000
}
```

---

### ACGME Violation Prevented

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
    "rolling_period": "4_weeks",
    "swap_blocked": true
  },
  "action_taken": "reject_swap_request"
}
```

---

### Swap Auto-Match Accepted

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
    "acgme_safe",
    "preference_compatible"
  ],
  "processing_time_seconds": 1.8
}
```

---

### Agent Task Failure

```json
{
  "timestamp": "2025-12-26T16:45:00Z",
  "event_type": "agent_task",
  "skill": "schedule-optimization",
  "outcome": "error",
  "duration_seconds": 320.5,
  "error_type": "ConstraintUnsatisfiable",
  "error_message": "Cannot satisfy hard constraint: supervision_ratio for Block 10, PGY-1",
  "context_tokens": 45000,
  "tool_calls": 18,
  "recovery_action": "escalate_to_human"
}
```

---

### MCP Tool Timeout

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

### Compliance Warning Issued

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
    "rolling_period": "4_weeks",
    "days_until_reset": 4
  },
  "response": "acknowledged",
  "notification_sent": true
}
```

---

### Rollback Executed

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

## Getting Started

### 1. Enable Telemetry Logging

```bash
# Create directory structure
mkdir -p .claude/Telemetry/logs/{daily,archives}

# Set permissions
chmod 700 .claude/Telemetry/logs

# Initialize current month log
touch .claude/Telemetry/logs/events-$(date +%Y-%m).jsonl
```

---

### 2. Configure Environment

```bash
# .env
AI_TELEMETRY_ENABLED=true
AI_TELEMETRY_LOG_DIR=.claude/Telemetry/logs
AI_TELEMETRY_SAMPLING_RATE=0.1  # 10% sampling for high-frequency events
AI_TELEMETRY_ALERT_EMAIL=program-director@example.mil
```

---

### 3. Install Git Hooks

```bash
# Copy telemetry hooks
cp .claude/scripts/hooks/post-commit .git/hooks/
chmod +x .git/hooks/post-commit

# Verify
.git/hooks/post-commit --test
```

---

### 4. Run First Aggregation

```bash
# Manual aggregation (test run)
python .claude/scripts/aggregate_telemetry.py \
  --input .claude/Telemetry/logs/events-$(date +%Y-%m).jsonl \
  --output .claude/Telemetry/dashboards/weekly-$(date +%Y-%m-%d).md

# View report
cat .claude/Telemetry/dashboards/weekly-$(date +%Y-%m-%d).md
```

---

### 5. Schedule Weekly Reports

```bash
# Add to crontab (every Monday at 9 AM)
crontab -e

# Add line:
0 9 * * 1 cd /path/to/repo && .claude/scripts/aggregate_telemetry.py --weekly
```

---

## Questions & Support

### Documentation

- **Log Format**: `.claude/Telemetry/LOG_FORMAT.md`
- **Metrics Schema**: `.claude/Telemetry/METRICS_SCHEMA.md`
- **Dashboard Templates**: `.claude/Telemetry/DASHBOARD.md`
- **General Telemetry**: `.claude/Telemetry/README.md`

### Troubleshooting

**Q: Logs not being written**
- Check `.env` has `AI_TELEMETRY_ENABLED=true`
- Verify directory permissions: `ls -la .claude/Telemetry/logs`
- Check disk space: `df -h`

**Q: Too much log volume**
- Increase sampling rate: `AI_TELEMETRY_SAMPLING_RATE=0.05` (5%)
- Enable log rotation: `logrotate` config in `.claude/scripts/`

**Q: How to query logs manually**
```bash
# Count events by type (last 7 days)
jq -r '.event_type' .claude/Telemetry/logs/events-$(date +%Y-%m).jsonl | sort | uniq -c

# Find all violations prevented
jq 'select(.event_type == "safety_validation" and .outcome == "violation_prevented")' \
  .claude/Telemetry/logs/events-$(date +%Y-%m).jsonl

# Average schedule generation time
jq -r 'select(.event_type == "schedule_generation") | .duration_seconds' \
  .claude/Telemetry/logs/events-$(date +%Y-%m).jsonl | \
  awk '{sum+=$1; count++} END {print sum/count}'
```

---

**Remember**: Telemetry is not surveillance. It's **self-measurement for continuous improvement**. Every metric should answer: "How can we make scheduling safer, faster, and better?"
