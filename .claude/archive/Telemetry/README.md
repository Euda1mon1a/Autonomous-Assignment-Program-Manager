# AI Infrastructure Telemetry System

> **Purpose**: Measure and improve Personal AI Infrastructure (PAI) effectiveness over time
> **Last Updated**: 2025-12-26
> **Owner**: META_UPDATER skill + Human maintainers

---

## Table of Contents

1. [Overview](#overview)
2. [Metrics Philosophy](#metrics-philosophy)
3. [Metric Categories](#metric-categories)
4. [Data Collection](#data-collection)
5. [Analysis Workflows](#analysis-workflows)
6. [Alerting & Anomaly Detection](#alerting--anomaly-detection)
7. [Privacy & Security](#privacy--security)
8. [Tool Integration](#tool-integration)

---

## Overview

The **Telemetry System** provides self-measurement capabilities for the AI infrastructure. Unlike traditional application monitoring (Prometheus, Grafana), this system focuses on **AI agent effectiveness metrics**:

- How often are skills used?
- Which agents are invoked most frequently?
- What's the error rate by skill?
- How long does it take to resolve issues?
- Are we capturing and implementing learnings?
- Is test coverage improving?
- Are incidents decreasing?

### Key Principles

1. **Self-Improving System**: Metrics drive META_UPDATER decisions
2. **Human-Readable**: Dashboards must be understandable by clinician administrators
3. **Actionable**: Every metric should trigger a clear action when anomalous
4. **Lightweight**: Minimal overhead, automated collection
5. **Privacy-Preserving**: No PHI, no PII in telemetry data

---

## Metrics Philosophy

### RED Metrics (Adapted for AI Infrastructure)

Traditional web service RED metrics adapted for AI agents:

| Metric | Traditional | AI Infrastructure Adaptation |
|--------|-------------|------------------------------|
| **Rate** | Requests per second | Skill invocations per day |
| **Errors** | HTTP 5xx rate | Skill execution failures |
| **Duration** | Response time | Time to task completion |

### Four Golden Signals (Site Reliability Engineering)

| Signal | AI Infrastructure Application |
|--------|-------------------------------|
| **Latency** | Median time from user request to agent response |
| **Traffic** | Number of agent invocations per hour |
| **Errors** | Skill execution failure rate, rollback rate |
| **Saturation** | Context window utilization, tool call limits |

### AI-Specific Metrics

Beyond traditional SRE metrics:

- **Learning Velocity**: New learning entries per week
- **Implementation Rate**: % of learnings converted to code changes
- **Skill Coverage**: % of codebase covered by specialized skills
- **Agent Coordination**: Multi-agent workflow success rate
- **Knowledge Drift**: How often skills become outdated
- **Meta-Learning Rate**: How quickly META_UPDATER adapts to new patterns

---

## Metric Categories

### 1. Skill Usage Metrics

**Purpose**: Understand which skills are most valuable

| Metric | Type | Description | Baseline |
|--------|------|-------------|----------|
| `skill_invocation_total` | Counter | Total invocations per skill | Track for 2 weeks |
| `skill_invocation_rate` | Gauge | Invocations per day (7-day rolling avg) | - |
| `skill_success_rate` | Gauge | % of successful completions | >90% |
| `skill_error_rate` | Gauge | % of executions with errors | <5% |
| `skill_duration_seconds` | Histogram | Time to complete skill task | p50, p95, p99 |
| `skill_context_tokens` | Histogram | Context window size during execution | Monitor saturation |

**Example Query**:
```
Top 5 skills by usage (last 7 days):
1. systematic-debugger: 47 invocations
2. constraint-preflight: 34 invocations
3. test-writer: 28 invocations
4. acgme-compliance: 19 invocations
5. code-review: 15 invocations
```

### 2. Agent Performance Metrics

**Purpose**: Track agent effectiveness and identify bottlenecks

| Metric | Type | Description | Target |
|--------|------|-------------|--------|
| `agent_invocation_total` | Counter | Agent starts (by name/type) | - |
| `agent_task_completion_rate` | Gauge | % of tasks completed successfully | >95% |
| `agent_rollback_rate` | Gauge | % of tasks requiring rollback | <2% |
| `agent_handoff_rate` | Gauge | % of tasks escalated to human | <10% |
| `agent_time_to_resolution` | Histogram | Time from start to task completion | p50 < 5 min |
| `agent_tool_call_count` | Histogram | Number of tool invocations per task | Monitor for loops |

**Example Dashboard**:
```
Agent Performance Summary (Week of 2025-12-20):
- Total Invocations: 143
- Completion Rate: 96.5%
- Rollback Rate: 1.4% (2 rollbacks)
- Median Time to Resolution: 4.2 minutes
- p95 Time to Resolution: 12.8 minutes
```

### 3. Learning Capture Metrics

**Purpose**: Measure knowledge accumulation and implementation

| Metric | Type | Description | Target |
|--------|------|-------------|--------|
| `learning_entries_total` | Counter | Total learning entries created | - |
| `learning_entries_per_week` | Gauge | New learnings captured weekly | Stable or increasing |
| `learning_implementation_rate` | Gauge | % of learnings converted to code | >70% |
| `learning_time_to_implementation` | Histogram | Days from learning to PR merge | p50 < 3 days |
| `learning_severity_distribution` | Gauge | Breakdown by severity (critical/warning/info) | - |
| `learning_source_distribution` | Gauge | Breakdown by source (incident/observation/etc) | - |

**Example Trend**:
```
Learning Velocity (Last 4 Weeks):
Week 1: 8 entries (3 critical, 3 warning, 2 info)
Week 2: 12 entries (1 critical, 5 warning, 6 info)
Week 3: 10 entries (2 critical, 4 warning, 4 info)
Week 4: 14 entries (1 critical, 6 warning, 7 info)

Trend: +75% increase in learning capture
Implementation Rate: 82% (36 of 44 learnings implemented)
```

### 4. Code Quality Metrics

**Purpose**: Track improvement in codebase health driven by AI infrastructure

| Metric | Type | Description | Target |
|--------|------|-------------|--------|
| `test_coverage_percent` | Gauge | Overall test coverage | >85% |
| `test_coverage_delta` | Gauge | Coverage change week-over-week | +0.5% per week |
| `lint_errors_total` | Gauge | Linting errors in codebase | Decreasing |
| `type_coverage_percent` | Gauge | % of functions with type hints | 100% |
| `doc_coverage_percent` | Gauge | % of public functions with docstrings | 100% |
| `security_findings_total` | Gauge | Open security findings | 0 |

**Example Report**:
```
Code Quality Scorecard (Month of December 2025):
- Test Coverage: 87.3% (+2.1% from November)
- Lint Errors: 0 (maintained clean state)
- Type Coverage: 98.7% (+1.2%)
- Docstring Coverage: 96.4% (+3.8%)
- Security Findings: 0 open, 3 resolved this month
```

### 5. Incident & Error Metrics

**Purpose**: Measure system reliability and learning effectiveness

| Metric | Type | Description | Target |
|--------|------|-------------|--------|
| `incidents_total` | Counter | Total incidents (by severity) | - |
| `incident_rate` | Gauge | Incidents per week | Decreasing |
| `incident_mttr_seconds` | Histogram | Mean time to resolution | p50 < 30 min |
| `incident_repeat_rate` | Gauge | % of incidents that are repeats | <5% |
| `skill_error_total` | Counter | Errors by skill name | - |
| `test_failure_rate` | Gauge | % of CI builds with test failures | <5% |

**Example Alert**:
```
🚨 ANOMALY DETECTED 🚨
Metric: incident_repeat_rate
Current Value: 12.5% (3 of 24 incidents this month are repeats)
Threshold: 5%
Analysis: LEARN-2025-087 (timezone handling) implemented but similar
          issues recurring. Requires META_UPDATER investigation.
Action: Review related learnings and skill effectiveness.
```

### 6. Context & Resource Utilization

**Purpose**: Monitor AI resource constraints and saturation

| Metric | Type | Description | Target |
|--------|------|-------------|--------|
| `context_window_utilization` | Histogram | % of context window used | p95 < 80% |
| `tool_call_limit_reached` | Counter | Times max tool calls hit | 0 |
| `session_length_minutes` | Histogram | Duration of agent sessions | Monitor long tails |
| `skill_load_time_seconds` | Histogram | Time to load skill prompts | p95 < 2s |
| `mcp_tool_latency_seconds` | Histogram | MCP tool response time | p95 < 1s |

---

## Data Collection

### Collection Methods

#### 1. Manual Entry (Learning Entries)
- AI agents create learning entries in `.claude/History/LEARN-*.md`
- META_UPDATER scans for new entries weekly
- Humans can create entries using template

#### 2. Automated Git Hooks
```bash
# .git/hooks/post-commit (example)
#!/bin/bash
# Log commit metadata for skill attribution
COMMIT_HASH=$(git rev-parse HEAD)
COMMIT_MSG=$(git log -1 --pretty=%B)

# Check for skill tags in commit message
if echo "$COMMIT_MSG" | grep -q "\[skill:"; then
  SKILL=$(echo "$COMMIT_MSG" | grep -oP '\[skill:\K[^\]]+')
  echo "$(date -Iseconds),commit,$SKILL,$COMMIT_HASH" >> .claude/Telemetry/events.log
fi
```

#### 3. CI/CD Pipeline Integration
```yaml
# .github/workflows/metrics-collector.yml
name: Collect AI Metrics
on: [push, pull_request]
jobs:
  collect:
    runs-on: ubuntu-latest
    steps:
      - name: Calculate test coverage delta
        run: |
          # Compare coverage to previous run
          # Log to telemetry

      - name: Count skill usage in commits
        run: |
          # Parse commit messages for [skill:name] tags
          # Aggregate counts
```

#### 4. Claude Code Session Logging
```python
# .claude/scripts/log_session.py
"""Log Claude Code session metadata for telemetry."""
import json
from datetime import datetime
from pathlib import Path

def log_session_end(skill_name: str, outcome: str, duration_seconds: float):
    """Log session completion to telemetry."""
    event = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": "skill_execution",
        "skill": skill_name,
        "outcome": outcome,  # success | error | rollback | handoff
        "duration_seconds": duration_seconds
    }

    log_file = Path(".claude/Telemetry/events.jsonl")
    with log_file.open("a") as f:
        f.write(json.dumps(event) + "\n")
```

#### 5. MCP Tool Call Logging
```python
# scheduler_mcp/telemetry.py
"""MCP tool call telemetry."""
from functools import wraps
import time

def track_tool_call(tool_name: str):
    """Decorator to track MCP tool execution metrics."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                outcome = "success"
                return result
            except Exception as e:
                outcome = "error"
                raise
            finally:
                duration = time.time() - start
                log_mcp_call(tool_name, outcome, duration)
        return wrapper
    return decorator
```

### Data Storage

```
.claude/Telemetry/
├── events.jsonl              # Raw event log (append-only)
├── metrics.json              # Aggregated metrics (updated weekly)
├── dashboards/
│   └── weekly-YYYY-MM-DD.md  # Weekly dashboard snapshots
├── alerts.log                # Anomaly alerts
└── archives/
    └── YYYY/                 # Historical data (yearly)
```

**Event Log Format** (`events.jsonl`):
```jsonl
{"timestamp":"2025-12-26T10:30:00Z","event_type":"skill_execution","skill":"systematic-debugger","outcome":"success","duration_seconds":247.3}
{"timestamp":"2025-12-26T11:15:00Z","event_type":"learning_created","id":"LEARN-2025-042","severity":"warning","source":"observation"}
{"timestamp":"2025-12-26T14:20:00Z","event_type":"test_coverage","coverage_percent":87.3,"delta_percent":0.4}
```

---

## Analysis Workflows

### Weekly Metrics Aggregation

**Automated Workflow** (run by META_UPDATER or cron):

```bash
#!/bin/bash
# .claude/scripts/aggregate_metrics.sh

# Parse events.jsonl for the past week
START_DATE=$(date -d '7 days ago' -Iseconds)
END_DATE=$(date -Iseconds)

# Aggregate metrics
python .claude/scripts/aggregate.py \
  --input .claude/Telemetry/events.jsonl \
  --start "$START_DATE" \
  --end "$END_DATE" \
  --output .claude/Telemetry/metrics.json

# Generate dashboard
python .claude/scripts/generate_dashboard.py \
  --metrics .claude/Telemetry/metrics.json \
  --output ".claude/Telemetry/dashboards/weekly-$(date +%Y-%m-%d).md"

# Check for anomalies
python .claude/scripts/detect_anomalies.py \
  --metrics .claude/Telemetry/metrics.json \
  --alert-threshold 2.0  # 2 standard deviations
```

### Monthly Learning Review

**Human-Guided Workflow**:

1. META_UPDATER generates learning summary:
   ```
   "Analyze all learning entries from the past month. Identify:
   1. Top 3 recurring themes
   2. Critical learnings not yet implemented
   3. Skills that need updates based on new patterns
   4. Gaps in test coverage revealed by incidents"
   ```

2. Program Director reviews summary
3. Prioritize skill updates and documentation improvements
4. Schedule implementation work

### Quarterly Skill Audit

**Comprehensive Review**:

1. For each skill:
   - Usage frequency
   - Success rate
   - Learnings associated with skill
   - Time since last update
   - Relevance to current needs

2. Decision matrix:
   - **Keep & Enhance**: High usage, high value
   - **Keep As-Is**: Low usage but specialized/rare events
   - **Deprecate**: Unused, functionality absorbed elsewhere
   - **Create New**: Gap identified, recurring pattern without skill

---

## Alerting & Anomaly Detection

### Alert Thresholds

| Alert | Condition | Severity | Action |
|-------|-----------|----------|--------|
| Skill Error Spike | Error rate >10% for any skill | Warning | Investigate skill implementation |
| Learning Stall | 0 new learnings in 2 weeks | Warning | Review workflow, ensure capture |
| Incident Repeat | Same root cause 3+ times | Critical | META_UPDATER priority update |
| Coverage Decline | Test coverage drops >2% | Warning | Block merges until recovered |
| Context Saturation | >90% context window usage | Info | Consider breaking into sub-agents |
| Tool Call Loop | >50 tool calls in single task | Critical | Kill switch, investigate agent logic |

### Anomaly Detection

**Statistical Process Control (SPC) Charts**:

Use Western Electric Rules (already in resilience framework) for telemetry:

```python
# .claude/scripts/detect_anomalies.py
from app.resilience.spc import SPCMonitor

def detect_skill_anomalies(skill_metrics: dict) -> list[str]:
    """Detect anomalies in skill performance using SPC."""
    monitor = SPCMonitor()
    alerts = []

    for skill_name, data in skill_metrics.items():
        # Check success rate
        success_rates = data["success_rate_history"]  # Last 20 data points
        if monitor.check_rule_violations(success_rates):
            alerts.append(
                f"SPC Alert: {skill_name} success rate showing "
                f"abnormal pattern (Rule {monitor.last_violation})"
            )

    return alerts
```

### Human Notification

**Escalation Ladder**:

1. **Info**: Log to `alerts.log`, include in weekly dashboard
2. **Warning**: Log + email to tech lead
3. **Critical**: Log + email + Slack notification + pause deployments

---

## Privacy & Security

### Data Minimization

**Never collect in telemetry**:
- ❌ Resident/faculty names
- ❌ Schedule assignments (dates, rotations)
- ❌ PHI (medical records, patient data)
- ❌ PII (emails, phone numbers, addresses)
- ❌ Credentials, API keys, secrets

**Safe to collect**:
- ✅ Skill names, agent names
- ✅ Error types (without sensitive details)
- ✅ Metric counts (invocations, duration)
- ✅ Code quality metrics (coverage %, lint counts)
- ✅ Commit hashes, PR numbers
- ✅ Timestamps (UTC only, no timezone inference)

### Access Control

```
Telemetry Data Access:
- META_UPDATER: Read/write (automated analysis)
- Program Director: Read (human oversight)
- Tech Lead: Read/write (manual investigation)
- External: None (no API exposure)
```

### Retention Policy

- **Raw Events**: 90 days, then archive
- **Aggregated Metrics**: 2 years
- **Weekly Dashboards**: Indefinite (small, human-readable)
- **Learning Entries**: Indefinite (core knowledge base)

---

## Tool Integration

### Prometheus Integration (Future)

Export AI metrics to existing Prometheus instance:

```python
# .claude/scripts/export_prometheus.py
"""Export AI metrics to Prometheus."""
from prometheus_client import Counter, Gauge, Histogram, CollectorRegistry, push_to_gateway

registry = CollectorRegistry()

# Define metrics
skill_invocations = Counter(
    'ai_skill_invocations_total',
    'Total skill invocations',
    ['skill_name', 'outcome'],
    registry=registry
)

# Push to gateway
push_to_gateway('localhost:9091', job='ai_infrastructure', registry=registry)
```

### Grafana Dashboards (Future)

Create Grafana dashboard for AI metrics:
- Top skills by usage (bar chart)
- Skill error rates over time (line chart)
- Learning velocity (area chart)
- Test coverage trend (line chart)

### Slack Notifications

```python
# .claude/scripts/notify_slack.py
"""Send telemetry alerts to Slack."""
import httpx

async def send_alert(webhook_url: str, message: str, severity: str):
    """Send alert to Slack channel."""
    color = {
        "info": "#36a64f",
        "warning": "#ff9800",
        "critical": "#f44336"
    }[severity]

    payload = {
        "attachments": [{
            "color": color,
            "title": f"AI Infrastructure Alert [{severity.upper()}]",
            "text": message,
            "footer": "Residency Scheduler Telemetry",
            "ts": int(time.time())
        }]
    }

    async with httpx.AsyncClient() as client:
        await client.post(webhook_url, json=payload)
```

---

## Getting Started

### 1. Enable Telemetry

```bash
# Create telemetry directory structure
mkdir -p .claude/Telemetry/dashboards
mkdir -p .claude/Telemetry/archives

# Initialize event log
touch .claude/Telemetry/events.jsonl

# Set up git hooks
cp .claude/scripts/post-commit .git/hooks/
chmod +x .git/hooks/post-commit
```

### 2. Configure Collection

```bash
# .env
AI_TELEMETRY_ENABLED=true
AI_TELEMETRY_LOG_PATH=.claude/Telemetry/events.jsonl
AI_TELEMETRY_ALERT_EMAIL=tech-lead@example.com
```

### 3. Run First Aggregation

```bash
# Manually run aggregation
.claude/scripts/aggregate_metrics.sh

# View generated dashboard
cat .claude/Telemetry/dashboards/weekly-$(date +%Y-%m-%d).md
```

### 4. Set Up Weekly Automation

```bash
# Add to crontab (run every Monday at 9 AM)
0 9 * * 1 cd /path/to/repo && .claude/scripts/aggregate_metrics.sh
```

---

## Example Telemetry Session

### Scenario: Debugging ACGME Validation Bug

**Event Sequence**:

```jsonl
{"timestamp":"2025-12-15T14:30:00Z","event_type":"skill_execution","skill":"systematic-debugger","outcome":"started","context_tokens":12500}
{"timestamp":"2025-12-15T14:35:00Z","event_type":"tool_call","tool":"Read","outcome":"success","duration_seconds":0.3}
{"timestamp":"2025-12-15T14:37:00Z","event_type":"tool_call","tool":"Grep","outcome":"success","duration_seconds":1.2}
{"timestamp":"2025-12-15T14:42:00Z","event_type":"learning_created","id":"LEARN-2025-001","severity":"critical","source":"incident"}
{"timestamp":"2025-12-15T14:50:00Z","event_type":"test_run","outcome":"failed","failed_count":3}
{"timestamp":"2025-12-15T15:10:00Z","event_type":"test_run","outcome":"passed","coverage_percent":87.3}
{"timestamp":"2025-12-15T15:15:00Z","event_type":"skill_execution","skill":"systematic-debugger","outcome":"success","duration_seconds":2700,"context_tokens":18900}
{"timestamp":"2025-12-15T15:20:00Z","event_type":"commit","skill":"systematic-debugger","commit_hash":"d0efcc5a"}
```

**Generated Metrics**:
```json
{
  "skill_metrics": {
    "systematic-debugger": {
      "invocations": 1,
      "success_rate": 1.0,
      "avg_duration_seconds": 2700,
      "avg_context_tokens": 15700
    }
  },
  "learning_metrics": {
    "total_entries": 1,
    "severity_breakdown": {"critical": 1},
    "source_breakdown": {"incident": 1}
  },
  "test_metrics": {
    "coverage_percent": 87.3,
    "delta_percent": 0.4
  }
}
```

---

## Future Enhancements

### Phase 1 (Current)
- [x] Manual event logging
- [x] Weekly aggregation scripts
- [x] Markdown dashboards

### Phase 2 (Next Quarter)
- [ ] Automated git hook collection
- [ ] Prometheus exporter
- [ ] Slack alert integration
- [ ] SPC anomaly detection

### Phase 3 (6 Months)
- [ ] Grafana dashboards
- [ ] ML-based anomaly detection
- [ ] Predictive skill recommendations
- [ ] Automated A/B testing for skill updates

### Phase 4 (Long-term)
- [ ] Cross-project telemetry aggregation
- [ ] Skill marketplace (shared learnings)
- [ ] Automated skill generation from patterns
- [ ] Self-healing infrastructure (META_UPDATER auto-implements fixes)

---

## Questions & Support

**For Questions**:
- Technical: See `docs/development/AGENT_SKILLS.md`
- Process: See `docs/guides/AI_AGENT_USER_GUIDE.md`
- Meta-learning: See `.claude/History/LEARNING_MINING.md`

**For Issues**:
- File learning entry: Use `.claude/History/LEARNING_ENTRY_TEMPLATE.md`
- Report telemetry bug: Create GitHub issue with tag `ai-infrastructure`

---

**Remember**: The goal of telemetry is not surveillance but **continuous improvement**. Every metric should answer: "How can we make the AI infrastructure more effective?"
