# Telemetry Metrics Schema

> **Purpose**: Standardized metric definitions for AI infrastructure telemetry
> **Last Updated**: 2025-12-26
> **Format**: Prometheus-style metrics with AI-specific extensions

---

## Table of Contents

1. [Metric Types](#metric-types)
2. [Naming Conventions](#naming-conventions)
3. [Label Standards](#label-standards)
4. [Core Metrics](#core-metrics)
5. [Event Schema](#event-schema)
6. [Aggregation Rules](#aggregation-rules)
7. [Example Queries](#example-queries)

---

## Metric Types

### Prometheus Metric Types

| Type | Description | Use Case | Example |
|------|-------------|----------|---------|
| **Counter** | Monotonically increasing value | Cumulative counts | Total skill invocations |
| **Gauge** | Value that can go up or down | Point-in-time measurements | Current test coverage % |
| **Histogram** | Distribution of values | Latency, duration | Skill execution time |
| **Summary** | Similar to histogram, quantiles | Client-side quantiles | N/A (use Histogram) |

### AI Infrastructure Extensions

| Type | Description | Use Case | Example |
|------|-------------|----------|---------|
| **Trend** | Gauge + historical delta | Week-over-week changes | Coverage delta |
| **Ratio** | Derived metric (A/B) | Success rates, percentages | Learning implementation rate |
| **Event** | Discrete occurrence | Incidents, deployments | ACGME violation detected |

---

## Naming Conventions

### Format

```
{namespace}_{subsystem}_{metric_name}_{unit}
```

**Examples**:
- `ai_skill_invocations_total` (counter)
- `ai_agent_duration_seconds` (histogram)
- `ai_learning_rate_per_week` (gauge)
- `ai_test_coverage_percent` (gauge)

### Rules

1. **Lowercase with underscores**: `skill_invocations_total` ✅ not `SkillInvocationsTotal` ❌
2. **Namespace first**: Always start with `ai_` for AI infrastructure metrics
3. **Unit suffix**: Add `_seconds`, `_bytes`, `_percent`, `_total` as appropriate
4. **Pluralize for totals**: `invocations_total` not `invocation_total`
5. **Avoid redundancy**: `ai_skill_duration_seconds` ✅ not `ai_skill_skill_duration_seconds` ❌

---

## Label Standards

### Common Labels

Apply consistently across all metrics:

| Label | Description | Example Values | Required? |
|-------|-------------|----------------|-----------|
| `skill_name` | Name of skill | `systematic-debugger`, `test-writer` | For skill metrics |
| `agent_name` | Agent identifier | `claude-sonnet-4.5`, `o1-pro` | For agent metrics |
| `outcome` | Result of operation | `success`, `error`, `rollback`, `handoff` | For execution metrics |
| `severity` | Importance level | `info`, `warning`, `critical` | For incidents/learnings |
| `source` | Origin of event | `incident`, `observation`, `experiment` | For learnings |
| `component` | System component | `scheduler`, `validator`, `api`, `frontend` | For error metrics |
| `environment` | Deployment env | `local`, `staging`, `production` | For all metrics |

### Label Cardinality Guidelines

**Low Cardinality** (✅ Safe):
- `skill_name`: ~30 unique values (number of skills)
- `outcome`: 4-5 values
- `severity`: 3 values

**Medium Cardinality** (⚠️ Monitor):
- `component`: ~20 values
- `error_type`: ~50 values

**High Cardinality** (❌ Avoid):
- ❌ `user_id`: Unique per user (PII risk)
- ❌ `commit_hash`: Unique per commit (explosion)
- ❌ `timestamp`: Continuous value

**Workaround for High Cardinality**:
Use events log for high-cardinality data, aggregate to low-cardinality metrics.

---

## Core Metrics

### 1. Skill Execution Metrics

#### `ai_skill_invocations_total`
```yaml
metric:
  name: ai_skill_invocations_total
  type: counter
  description: Total number of times each skill has been invoked
  unit: invocations
  labels:
    - skill_name
    - outcome
    - environment
  example:
    ai_skill_invocations_total{skill_name="systematic-debugger",outcome="success",environment="local"} 47
    ai_skill_invocations_total{skill_name="test-writer",outcome="error",environment="local"} 2
```

#### `ai_skill_duration_seconds`
```yaml
metric:
  name: ai_skill_duration_seconds
  type: histogram
  description: Time taken to complete skill execution
  unit: seconds
  buckets: [1, 5, 10, 30, 60, 120, 300, 600, 1800, 3600]  # 1s to 1hr
  labels:
    - skill_name
    - outcome
  example:
    ai_skill_duration_seconds_bucket{skill_name="systematic-debugger",outcome="success",le="300"} 42
    ai_skill_duration_seconds_sum{skill_name="systematic-debugger",outcome="success"} 10450.3
    ai_skill_duration_seconds_count{skill_name="systematic-debugger",outcome="success"} 47
  derived_metrics:
    p50: histogram_quantile(0.50, ai_skill_duration_seconds_bucket)
    p95: histogram_quantile(0.95, ai_skill_duration_seconds_bucket)
    p99: histogram_quantile(0.99, ai_skill_duration_seconds_bucket)
```

#### `ai_skill_success_rate`
```yaml
metric:
  name: ai_skill_success_rate
  type: gauge (derived from counter)
  description: Success rate for each skill (successful invocations / total invocations)
  unit: ratio (0.0 to 1.0)
  labels:
    - skill_name
  calculation: |
    sum(rate(ai_skill_invocations_total{outcome="success"}[7d])) by (skill_name)
    /
    sum(rate(ai_skill_invocations_total[7d])) by (skill_name)
  example:
    ai_skill_success_rate{skill_name="systematic-debugger"} 0.957  # 95.7%
    ai_skill_success_rate{skill_name="test-writer"} 0.928  # 92.8%
  alert_threshold: < 0.90  # Alert if success rate drops below 90%
```

#### `ai_skill_context_tokens`
```yaml
metric:
  name: ai_skill_context_tokens
  type: histogram
  description: Context window size (in tokens) during skill execution
  unit: tokens
  buckets: [1000, 5000, 10000, 20000, 50000, 100000, 150000, 200000]
  labels:
    - skill_name
  example:
    ai_skill_context_tokens_bucket{skill_name="systematic-debugger",le="50000"} 38
    ai_skill_context_tokens_sum{skill_name="systematic-debugger"} 1847500
    ai_skill_context_tokens_count{skill_name="systematic-debugger"} 47
  alert_threshold: p95 > 160000  # Alert if 95th percentile exceeds 160K tokens (80% of 200K limit)
```

### 2. Agent Performance Metrics

#### `ai_agent_invocations_total`
```yaml
metric:
  name: ai_agent_invocations_total
  type: counter
  description: Total agent invocations (any agent type)
  unit: invocations
  labels:
    - agent_name
    - task_type
    - outcome
  example:
    ai_agent_invocations_total{agent_name="claude-sonnet-4.5",task_type="debugging",outcome="success"} 143
    ai_agent_invocations_total{agent_name="o1-pro",task_type="planning",outcome="success"} 12
```

#### `ai_agent_time_to_resolution_seconds`
```yaml
metric:
  name: ai_agent_time_to_resolution_seconds
  type: histogram
  description: Time from agent invocation to task completion
  unit: seconds
  buckets: [10, 30, 60, 180, 300, 600, 1800, 3600]  # 10s to 1hr
  labels:
    - agent_name
    - task_type
  example:
    ai_agent_time_to_resolution_seconds_sum{agent_name="claude-sonnet-4.5",task_type="debugging"} 36000
    ai_agent_time_to_resolution_seconds_count{agent_name="claude-sonnet-4.5",task_type="debugging"} 143
  derived_metrics:
    median: histogram_quantile(0.50, ai_agent_time_to_resolution_seconds_bucket)  # p50 < 5 min target
```

#### `ai_agent_rollback_rate`
```yaml
metric:
  name: ai_agent_rollback_rate
  type: gauge (derived)
  description: Percentage of agent tasks that required rollback
  unit: ratio (0.0 to 1.0)
  labels:
    - agent_name
  calculation: |
    sum(rate(ai_agent_invocations_total{outcome="rollback"}[7d])) by (agent_name)
    /
    sum(rate(ai_agent_invocations_total[7d])) by (agent_name)
  example:
    ai_agent_rollback_rate{agent_name="claude-sonnet-4.5"} 0.014  # 1.4%
  alert_threshold: > 0.05  # Alert if rollback rate exceeds 5%
```

#### `ai_agent_tool_calls_per_task`
```yaml
metric:
  name: ai_agent_tool_calls_per_task
  type: histogram
  description: Number of tool invocations per agent task
  unit: calls
  buckets: [1, 5, 10, 20, 50, 100, 200, 500]
  labels:
    - agent_name
    - task_type
  example:
    ai_agent_tool_calls_per_task_sum{agent_name="claude-sonnet-4.5",task_type="debugging"} 1820
    ai_agent_tool_calls_per_task_count{agent_name="claude-sonnet-4.5",task_type="debugging"} 143
  alert_threshold: max > 500  # Alert if any task uses >500 tool calls (possible loop)
```

### 3. Learning Metrics

#### `ai_learning_entries_total`
```yaml
metric:
  name: ai_learning_entries_total
  type: counter
  description: Total learning entries created
  unit: entries
  labels:
    - severity
    - source
    - status
  example:
    ai_learning_entries_total{severity="critical",source="incident",status="implemented"} 8
    ai_learning_entries_total{severity="warning",source="observation",status="draft"} 15
```

#### `ai_learning_rate_per_week`
```yaml
metric:
  name: ai_learning_rate_per_week
  type: gauge (derived)
  description: Number of new learning entries per week (7-day rolling average)
  unit: entries per week
  calculation: |
    sum(rate(ai_learning_entries_total[7d])) * 7 * 24 * 3600
  example:
    ai_learning_rate_per_week 12.5
  alert_threshold: < 3.0  # Alert if learning velocity drops below 3 entries/week
```

#### `ai_learning_implementation_rate`
```yaml
metric:
  name: ai_learning_implementation_rate
  type: gauge (derived)
  description: Percentage of learnings converted to code changes
  unit: ratio (0.0 to 1.0)
  calculation: |
    sum(ai_learning_entries_total{status="implemented"})
    /
    sum(ai_learning_entries_total)
  example:
    ai_learning_implementation_rate 0.82  # 82%
  alert_threshold: < 0.70  # Alert if implementation rate drops below 70%
```

#### `ai_learning_time_to_implementation_seconds`
```yaml
metric:
  name: ai_learning_time_to_implementation_seconds
  type: histogram
  description: Time from learning entry creation to implementation (PR merge)
  unit: seconds
  buckets: [3600, 86400, 259200, 604800, 1209600, 2592000]  # 1hr to 30 days
  labels:
    - severity
  example:
    ai_learning_time_to_implementation_seconds_sum{severity="critical"} 432000  # 5 days total
    ai_learning_time_to_implementation_seconds_count{severity="critical"} 8
  derived_metrics:
    median_days: histogram_quantile(0.50, ai_learning_time_to_implementation_seconds_bucket) / 86400
  target: median < 3 days for critical learnings
```

### 4. Code Quality Metrics

#### `ai_test_coverage_percent`
```yaml
metric:
  name: ai_test_coverage_percent
  type: gauge
  description: Overall test coverage percentage
  unit: percent (0.0 to 100.0)
  labels:
    - subsystem  # backend, frontend, mcp-server
  example:
    ai_test_coverage_percent{subsystem="backend"} 87.3
    ai_test_coverage_percent{subsystem="frontend"} 78.5
  target: > 85%
```

#### `ai_test_coverage_delta_percent`
```yaml
metric:
  name: ai_test_coverage_delta_percent
  type: gauge (trend)
  description: Week-over-week change in test coverage
  unit: percent delta (-100.0 to +100.0)
  labels:
    - subsystem
  calculation: |
    ai_test_coverage_percent - ai_test_coverage_percent offset 7d
  example:
    ai_test_coverage_delta_percent{subsystem="backend"} +2.1
  alert_threshold: < -2.0  # Alert if coverage drops by 2% or more
```

#### `ai_lint_errors_total`
```yaml
metric:
  name: ai_lint_errors_total
  type: gauge
  description: Total linting errors in codebase
  unit: errors
  labels:
    - subsystem
    - severity  # error, warning
  example:
    ai_lint_errors_total{subsystem="backend",severity="error"} 0
    ai_lint_errors_total{subsystem="backend",severity="warning"} 5
  target: 0 errors, <10 warnings
```

#### `ai_type_coverage_percent`
```yaml
metric:
  name: ai_type_coverage_percent
  type: gauge
  description: Percentage of functions with type hints (Python) or strict typing (TypeScript)
  unit: percent (0.0 to 100.0)
  labels:
    - subsystem
  example:
    ai_type_coverage_percent{subsystem="backend"} 98.7
  target: 100%
```

### 5. Incident & Error Metrics

#### `ai_incidents_total`
```yaml
metric:
  name: ai_incidents_total
  type: counter
  description: Total incidents (bugs, outages, compliance violations)
  unit: incidents
  labels:
    - severity
    - component
    - resolved  # true, false
  example:
    ai_incidents_total{severity="critical",component="scheduler",resolved="true"} 3
    ai_incidents_total{severity="warning",component="api",resolved="false"} 1
```

#### `ai_incident_rate_per_week`
```yaml
metric:
  name: ai_incident_rate_per_week
  type: gauge (derived)
  description: Incident rate per week (7-day rolling average)
  unit: incidents per week
  calculation: |
    sum(rate(ai_incidents_total[7d])) * 7 * 24 * 3600
  example:
    ai_incident_rate_per_week 2.3
  target: Decreasing over time
```

#### `ai_incident_mttr_seconds`
```yaml
metric:
  name: ai_incident_mttr_seconds
  type: histogram
  description: Mean time to resolution for incidents
  unit: seconds
  buckets: [300, 1800, 3600, 7200, 14400, 28800, 86400]  # 5min to 1 day
  labels:
    - severity
  example:
    ai_incident_mttr_seconds_sum{severity="critical"} 5400  # 90 minutes total
    ai_incident_mttr_seconds_count{severity="critical"} 3
  derived_metrics:
    median_minutes: histogram_quantile(0.50, ai_incident_mttr_seconds_bucket) / 60
  target: median < 30 minutes for critical incidents
```

#### `ai_incident_repeat_rate`
```yaml
metric:
  name: ai_incident_repeat_rate
  type: gauge (derived)
  description: Percentage of incidents that are repeats (same root cause)
  unit: ratio (0.0 to 1.0)
  calculation: |
    # Manual calculation based on incident tagging
    sum(ai_incidents_total{is_repeat="true"}) by (component)
    /
    sum(ai_incidents_total) by (component)
  example:
    ai_incident_repeat_rate{component="scheduler"} 0.125  # 12.5%
  alert_threshold: > 0.10  # Alert if >10% of incidents are repeats
```

### 6. Context & Resource Metrics

#### `ai_context_window_utilization_percent`
```yaml
metric:
  name: ai_context_window_utilization_percent
  type: histogram
  description: Percentage of context window used during task execution
  unit: percent (0.0 to 100.0)
  buckets: [10, 25, 50, 70, 80, 90, 95, 100]
  labels:
    - agent_name
    - skill_name
  example:
    ai_context_window_utilization_percent_bucket{agent_name="claude-sonnet-4.5",skill_name="systematic-debugger",le="80"} 42
  alert_threshold: p95 > 90%  # Alert if 95th percentile exceeds 90% utilization
```

#### `ai_tool_call_limit_reached_total`
```yaml
metric:
  name: ai_tool_call_limit_reached_total
  type: counter
  description: Number of times max tool call limit was reached (potential infinite loop)
  unit: occurrences
  labels:
    - agent_name
    - skill_name
  example:
    ai_tool_call_limit_reached_total{agent_name="claude-sonnet-4.5",skill_name="systematic-debugger"} 0
  alert_threshold: > 0  # Alert on any occurrence (critical safety issue)
```

#### `ai_mcp_tool_latency_seconds`
```yaml
metric:
  name: ai_mcp_tool_latency_seconds
  type: histogram
  description: Latency of MCP tool calls
  unit: seconds
  buckets: [0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
  labels:
    - tool_name
    - outcome
  example:
    ai_mcp_tool_latency_seconds_sum{tool_name="validate_schedule",outcome="success"} 45.3
    ai_mcp_tool_latency_seconds_count{tool_name="validate_schedule",outcome="success"} 28
  derived_metrics:
    p95: histogram_quantile(0.95, ai_mcp_tool_latency_seconds_bucket)
  target: p95 < 2 seconds
```

---

## Event Schema

### Raw Event Format (JSONL)

All events logged to `.claude/Telemetry/events.jsonl`:

```typescript
interface TelemetryEvent {
  // Required fields
  timestamp: string;        // ISO 8601 UTC timestamp
  event_type: string;       // Event category (see Event Types below)

  // Optional fields (depends on event type)
  skill?: string;           // Skill name
  agent?: string;           // Agent identifier
  outcome?: "success" | "error" | "rollback" | "handoff";
  duration_seconds?: number;
  context_tokens?: number;
  tool_calls?: number;

  // Error tracking
  error_type?: string;
  error_message?: string;   // Sanitized, no PII
  component?: string;

  // Learning tracking
  learning_id?: string;     // e.g., LEARN-2025-042
  severity?: "info" | "warning" | "critical";
  source?: "incident" | "observation" | "experiment" | "user_feedback";

  // Code quality
  coverage_percent?: number;
  delta_percent?: number;
  lint_errors?: number;

  // References
  commit_hash?: string;
  pr_number?: number;
  issue_number?: number;

  // Metadata
  environment?: "local" | "staging" | "production";
  metadata?: Record<string, any>;  // Additional context
}
```

### Event Types

| Event Type | Description | Required Fields |
|------------|-------------|-----------------|
| `skill_execution` | Skill invoked and completed | `skill`, `outcome`, `duration_seconds` |
| `agent_invocation` | Agent started task | `agent`, `task_type` |
| `learning_created` | New learning entry | `learning_id`, `severity`, `source` |
| `test_coverage` | Test coverage measured | `coverage_percent`, `delta_percent` |
| `incident` | Incident occurred | `severity`, `component`, `error_type` |
| `commit` | Code committed | `commit_hash`, `skill` (if skill-assisted) |
| `tool_call` | MCP tool invoked | `tool_name`, `outcome`, `duration_seconds` |
| `deployment` | Code deployed | `environment`, `commit_hash` |

### Example Events

```jsonl
{"timestamp":"2025-12-26T10:30:00Z","event_type":"skill_execution","skill":"systematic-debugger","outcome":"success","duration_seconds":247.3,"context_tokens":18900,"tool_calls":23}
{"timestamp":"2025-12-26T11:15:00Z","event_type":"learning_created","learning_id":"LEARN-2025-042","severity":"warning","source":"observation"}
{"timestamp":"2025-12-26T14:20:00Z","event_type":"test_coverage","coverage_percent":87.3,"delta_percent":0.4,"subsystem":"backend"}
{"timestamp":"2025-12-26T15:45:00Z","event_type":"incident","severity":"critical","component":"scheduler","error_type":"ACGMEViolation","resolved":true,"mttr_seconds":1800}
{"timestamp":"2025-12-26T16:00:00Z","event_type":"commit","commit_hash":"d0efcc5a","skill":"systematic-debugger","pr_number":248}
```

---

## Aggregation Rules

### Time Windows

| Window | Use Case | Example Query |
|--------|----------|---------------|
| **1 minute** | Real-time monitoring | `rate(ai_skill_invocations_total[1m])` |
| **5 minutes** | Alerting | `rate(ai_incidents_total[5m]) > 0.01` |
| **1 hour** | Operational dashboards | `avg_over_time(ai_test_coverage_percent[1h])` |
| **1 day** | Daily reports | `increase(ai_learning_entries_total[1d])` |
| **7 days** | Weekly trends | `rate(ai_skill_invocations_total[7d])` |
| **30 days** | Monthly reviews | `avg_over_time(ai_incident_rate_per_week[30d])` |

### Aggregation Functions

```promql
# Sum across labels (total invocations for all skills)
sum(ai_skill_invocations_total)

# Sum by label (invocations per skill)
sum(ai_skill_invocations_total) by (skill_name)

# Average
avg(ai_test_coverage_percent) by (subsystem)

# Rate (per-second rate over time window)
rate(ai_skill_invocations_total[5m])

# Increase (total increase over time window)
increase(ai_learning_entries_total[7d])

# Histogram quantiles
histogram_quantile(0.95, ai_skill_duration_seconds_bucket)
```

---

## Example Queries

### Skill Performance

```promql
# Top 5 skills by usage (last 7 days)
topk(5, sum(rate(ai_skill_invocations_total[7d])) by (skill_name))

# Skills with error rate > 10%
(
  sum(rate(ai_skill_invocations_total{outcome="error"}[7d])) by (skill_name)
  /
  sum(rate(ai_skill_invocations_total[7d])) by (skill_name)
) > 0.10

# Slowest skills (p95 duration)
topk(5, histogram_quantile(0.95, sum(rate(ai_skill_duration_seconds_bucket[7d])) by (skill_name, le)))
```

### Learning Velocity

```promql
# Learning entries created this week
sum(increase(ai_learning_entries_total[7d]))

# Critical learnings not yet implemented
sum(ai_learning_entries_total{severity="critical",status!="implemented"})

# Average time to implement critical learnings (in days)
histogram_quantile(0.50, sum(rate(ai_learning_time_to_implementation_seconds_bucket{severity="critical"}[30d])) by (le)) / 86400
```

### Incident Analysis

```promql
# Incident rate trending up? (compare this week to last week)
sum(rate(ai_incidents_total[7d])) / sum(rate(ai_incidents_total[7d] offset 7d))

# Components with highest incident rate
topk(3, sum(rate(ai_incidents_total[7d])) by (component))

# MTTR for critical incidents (median in minutes)
histogram_quantile(0.50, sum(rate(ai_incident_mttr_seconds_bucket{severity="critical"}[30d])) by (le)) / 60
```

### Code Quality Trends

```promql
# Test coverage change over last 4 weeks
ai_test_coverage_percent{subsystem="backend"} - ai_test_coverage_percent{subsystem="backend"} offset 28d

# Lint errors trending
sum(ai_lint_errors_total) by (subsystem)
```

### Anomaly Detection

```promql
# Skill success rate 2 standard deviations below normal
(
  sum(rate(ai_skill_invocations_total{outcome="success"}[7d])) by (skill_name)
  /
  sum(rate(ai_skill_invocations_total[7d])) by (skill_name)
) < (
  avg_over_time((sum(rate(ai_skill_invocations_total{outcome="success"}[7d])) by (skill_name) / sum(rate(ai_skill_invocations_total[7d])) by (skill_name))[30d:7d])
  - 2 * stddev_over_time((sum(rate(ai_skill_invocations_total{outcome="success"}[7d])) by (skill_name) / sum(rate(ai_skill_invocations_total[7d])) by (skill_name))[30d:7d])
)
```

---

## Validation

### Metric Checklist

Before adding a new metric, verify:

- [ ] **Name follows convention**: `ai_{subsystem}_{metric}_{unit}`
- [ ] **Type is appropriate**: Counter for cumulative, Gauge for point-in-time, Histogram for distributions
- [ ] **Labels are low-cardinality**: Each label has <100 unique values
- [ ] **Description is clear**: Someone unfamiliar with the metric can understand it
- [ ] **Unit is specified**: seconds, bytes, percent, total, etc.
- [ ] **Baseline is defined**: What's the target value or acceptable range?
- [ ] **Alert threshold exists**: When should this metric trigger action?
- [ ] **Query example provided**: How to use this metric in practice
- [ ] **Privacy-safe**: No PII, PHI, or sensitive data in labels/values

---

## Future Extensions

### Phase 2 Metrics (Next Quarter)

- `ai_skill_token_efficiency`: Output quality per token used
- `ai_agent_learning_transfer`: Cross-agent knowledge sharing effectiveness
- `ai_meta_updater_accuracy`: % of META_UPDATER proposed changes that are accepted
- `ai_skill_staleness_days`: Days since skill was last updated vs. usage frequency

### Phase 3 Metrics (6 Months)

- `ai_predictive_skill_recommendation_accuracy`: How often recommended skills are used
- `ai_automated_fix_success_rate`: % of issues resolved without human intervention
- `ai_cross_project_learning_adoption`: Learnings shared across projects

---

**Remember**: Metrics should drive action, not just satisfy curiosity. Every metric should answer: "What decision will this help me make?"
