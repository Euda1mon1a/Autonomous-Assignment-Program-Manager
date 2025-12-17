***REMOVED*** Resilience Framework

The Residency Scheduler implements a comprehensive resilience framework based on cross-industry best practices. This document describes the concepts, implementation, and configuration of the resilience system.

---

***REMOVED******REMOVED*** Overview

The resilience framework ensures the scheduling system remains operational and effective even under stress conditions such as:

- Staff shortages (illness, emergencies, deployments)
- Unexpected demand spikes
- System failures
- Natural disasters or emergencies

***REMOVED******REMOVED******REMOVED*** Design Principles

1. **Proactive monitoring** - Detect issues before they become critical
2. **Graceful degradation** - Maintain core functionality under stress
3. **Automated response** - Reduce manual intervention requirements
4. **Transparency** - Clear visibility into system health

---

***REMOVED******REMOVED*** Defense in Depth

The system implements five defense levels, each with escalating responses:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Defense Level Hierarchy                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────┐                                                   │
│  │  BLACK  │  > 95% utilization - Crisis Management             │
│  ├─────────┤                                                   │
│  │   RED   │  90-95% - Emergency Protocols                     │
│  ├─────────┤                                                   │
│  │ ORANGE  │  80-90% - Active Mitigation                       │
│  ├─────────┤                                                   │
│  │ YELLOW  │  70-80% - Warning & Preparation                   │
│  ├─────────┤                                                   │
│  │  GREEN  │  < 70% - Normal Operations                        │
│  └─────────┘                                                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

***REMOVED******REMOVED******REMOVED*** Level Details

***REMOVED******REMOVED******REMOVED******REMOVED*** GREEN (< 70% utilization)

**Status**: Normal operations

**Actions**:
- Standard monitoring
- Regular health checks
- Background optimization

**Indicators**:
- Adequate staffing coverage
- No compliance violations
- All positions filled

---

***REMOVED******REMOVED******REMOVED******REMOVED*** YELLOW (70-80% utilization)

**Status**: Warning level

**Actions**:
- Increased monitoring frequency
- Alert notifications sent
- Pre-position backup resources
- Review upcoming absences

**Triggers**:
- Utilization crosses 70%
- Multiple upcoming absences
- Certification expirations approaching

**Automated Response**:
```python
***REMOVED*** Example yellow level response
if defense_level == DefenseLevel.YELLOW:
    await increase_monitoring_frequency()
    await notify_coordinators("utilization_warning")
    await prepare_backup_roster()
```

---

***REMOVED******REMOVED******REMOVED******REMOVED*** ORANGE (80-90% utilization)

**Status**: Active mitigation required

**Actions**:
- Activate contingency plans
- Request voluntary overtime
- Defer non-essential activities
- Enable fallback schedules

**Triggers**:
- Utilization crosses 80%
- Critical role unfilled
- Multiple simultaneous absences

**Automated Response**:
```python
***REMOVED*** Example orange level response
if defense_level == DefenseLevel.ORANGE:
    await activate_contingency_schedules()
    await request_voluntary_coverage()
    await defer_elective_rotations()
    await notify_administration()
```

---

***REMOVED******REMOVED******REMOVED******REMOVED*** RED (90-95% utilization)

**Status**: Emergency protocols

**Actions**:
- Mandatory overtime authorization
- Cancel non-essential activities
- Redistribute workload
- Executive notification

**Triggers**:
- Utilization crosses 90%
- Critical coverage gap imminent
- N-1 contingency failed

**Automated Response**:
```python
***REMOVED*** Example red level response
if defense_level == DefenseLevel.RED:
    await authorize_mandatory_overtime()
    await cancel_nonessential_activities()
    await redistribute_workload()
    await notify_executives()
    await activate_sacrifice_hierarchy()
```

---

***REMOVED******REMOVED******REMOVED******REMOVED*** BLACK (> 95% utilization)

**Status**: Crisis management

**Actions**:
- Crisis team activation
- External resource requests
- Essential services only
- Executive decision required

**Triggers**:
- Utilization crosses 95%
- Multiple critical failures
- System degradation detected

**Automated Response**:
```python
***REMOVED*** Example black level response
if defense_level == DefenseLevel.BLACK:
    await activate_crisis_team()
    await request_external_resources()
    await reduce_to_essential_services()
    await require_executive_approval()
    await implement_full_load_shedding()
```

---

***REMOVED******REMOVED*** Utilization Monitoring

***REMOVED******REMOVED******REMOVED*** 80% Utilization Threshold

Based on queuing theory and operations research, the 80% utilization threshold is critical:

```
              Response Time vs Utilization
                    │
Response            │                    ╱
Time                │                   ╱
                    │                  ╱
                    │                ╱
                    │              ╱
                    │           ╱
                    │        ╱
                    │    ╱
                    │╱
                    └──────────────────────────
                         50%   70%  80%  90%  100%
                              Utilization
```

At 80%+ utilization:
- Response times increase exponentially
- System becomes fragile to disruptions
- Small changes cause large impacts

***REMOVED******REMOVED******REMOVED*** Utilization Calculation

```python
def calculate_utilization(schedule, date_range):
    """Calculate system utilization for a date range."""

    total_capacity = sum(
        person.available_hours
        for person in active_personnel
    )

    total_assigned = sum(
        assignment.hours
        for assignment in assignments
    )

    utilization = total_assigned / total_capacity

    return {
        "utilization": utilization,
        "capacity": total_capacity,
        "assigned": total_assigned,
        "buffer": total_capacity - total_assigned
    }
```

---

***REMOVED******REMOVED*** Contingency Analysis

***REMOVED******REMOVED******REMOVED*** N-1 Analysis

Tests if the system can handle any single person becoming unavailable:

```
┌─────────────────────────────────────────────────────────────────┐
│                      N-1 Analysis                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  For each person P in roster:                                   │
│    1. Temporarily remove P from availability                    │
│    2. Attempt to fill all assignments                           │
│    3. Check if all critical roles covered                       │
│    4. Record result                                             │
│                                                                 │
│  Result: List of "single points of failure"                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

***REMOVED******REMOVED******REMOVED*** N-2 Analysis

Tests if the system can handle any two people becoming unavailable:

```python
def n2_analysis(schedule):
    """Perform N-2 contingency analysis."""

    personnel = get_active_personnel()
    failures = []

    for i, person1 in enumerate(personnel):
        for person2 in personnel[i+1:]:
            ***REMOVED*** Remove both people
            modified_schedule = remove_people(
                schedule, [person1, person2]
            )

            ***REMOVED*** Check if schedule still valid
            if not can_maintain_coverage(modified_schedule):
                failures.append({
                    "persons": [person1, person2],
                    "impact": calculate_impact(modified_schedule)
                })

    return {
        "n2_resilient": len(failures) == 0,
        "failure_scenarios": failures
    }
```

***REMOVED******REMOVED******REMOVED*** NetworkX Graph Analysis

The system uses NetworkX for dependency analysis:

```python
import networkx as nx

def build_dependency_graph(schedule):
    """Build graph of personnel dependencies."""

    G = nx.DiGraph()

    ***REMOVED*** Add nodes for each person
    for person in personnel:
        G.add_node(person.id, role=person.role)

    ***REMOVED*** Add edges for coverage dependencies
    for assignment in schedule.assignments:
        for backup in assignment.potential_backups:
            G.add_edge(
                assignment.person_id,
                backup.id,
                weight=backup.suitability_score
            )

    return G

def identify_critical_hubs(G):
    """Find critical personnel using centrality analysis."""

    betweenness = nx.betweenness_centrality(G)
    critical = [
        node for node, score in betweenness.items()
        if score > threshold
    ]

    return critical
```

---

***REMOVED******REMOVED*** Static Stability

***REMOVED******REMOVED******REMOVED*** Pre-computed Fallback Schedules

The system maintains fallback schedules for rapid activation:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Fallback Schedule Hierarchy                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Level 0: Current active schedule                               │
│     │                                                           │
│     ▼                                                           │
│  Level 1: Minor adjustments fallback                            │
│     │      - Swap non-critical assignments                      │
│     │      - Redistribute electives                             │
│     │                                                           │
│     ▼                                                           │
│  Level 2: Significant restructure fallback                      │
│     │      - Cancel electives                                   │
│     │      - Overtime activation                                │
│     │                                                           │
│     ▼                                                           │
│  Level 3: Emergency minimum coverage                            │
│           - Essential services only                             │
│           - External resources                                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

***REMOVED******REMOVED******REMOVED*** Fallback Generation

```python
async def generate_fallback_schedules(base_schedule):
    """Pre-compute fallback schedules for rapid activation."""

    fallbacks = {}

    ***REMOVED*** Level 1: Minor adjustments
    fallbacks["level_1"] = await optimize_schedule(
        base_schedule,
        constraints={"maintain_coverage": True},
        flexibility="high"
    )

    ***REMOVED*** Level 2: Significant restructure
    fallbacks["level_2"] = await optimize_schedule(
        base_schedule,
        constraints={"essential_only": False},
        flexibility="very_high",
        allow_overtime=True
    )

    ***REMOVED*** Level 3: Emergency minimum
    fallbacks["level_3"] = await generate_essential_only_schedule(
        base_schedule
    )

    return fallbacks
```

---

***REMOVED******REMOVED*** Sacrifice Hierarchy

When load shedding is necessary, the system follows a defined sacrifice hierarchy:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Sacrifice Hierarchy                           │
│              (Priority order - shed first to last)               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Administrative meetings         [First to shed]             │
│  2. Elective rotations                                          │
│  3. Educational activities                                      │
│  4. Non-urgent clinic sessions                                  │
│  5. Consultation services                                       │
│  6. Urgent clinic sessions                                      │
│  7. Ward coverage                                               │
│  8. ICU coverage                                                │
│  9. Emergency coverage               [Last resort only]         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

***REMOVED******REMOVED******REMOVED*** Implementation

```python
class SacrificeHierarchy:
    """Manages load shedding priorities."""

    PRIORITY_ORDER = [
        ("administrative", 1),
        ("elective", 2),
        ("educational", 3),
        ("clinic_non_urgent", 4),
        ("consultation", 5),
        ("clinic_urgent", 6),
        ("ward", 7),
        ("icu", 8),
        ("emergency", 9),
    ]

    async def shed_load(self, required_reduction: float):
        """Shed load according to sacrifice hierarchy."""

        shed_assignments = []
        current_reduction = 0

        for activity_type, priority in self.PRIORITY_ORDER:
            if current_reduction >= required_reduction:
                break

            assignments = await self.get_sheddable_assignments(
                activity_type
            )

            for assignment in assignments:
                shed_assignments.append(assignment)
                current_reduction += assignment.load_weight

                if current_reduction >= required_reduction:
                    break

        return shed_assignments
```

---

***REMOVED******REMOVED*** Health Monitoring

***REMOVED******REMOVED******REMOVED*** Metrics Collected

| Metric | Description | Threshold |
|--------|-------------|-----------|
| `utilization` | Current system utilization | < 80% |
| `coverage_ratio` | Positions filled / Required | > 95% |
| `compliance_score` | ACGME compliance percentage | > 98% |
| `stability_index` | Schedule stability metric | > 0.85 |
| `fairness_gini` | Workload distribution fairness | < 0.15 |

***REMOVED******REMOVED******REMOVED*** Prometheus Metrics

```python
from prometheus_client import Gauge, Counter, Histogram

***REMOVED*** Define metrics
utilization_gauge = Gauge(
    'residency_utilization',
    'Current system utilization percentage'
)

coverage_gauge = Gauge(
    'residency_coverage_ratio',
    'Ratio of filled to required positions'
)

violation_counter = Counter(
    'residency_violations_total',
    'Total ACGME violations detected',
    ['severity', 'type']
)

health_check_duration = Histogram(
    'residency_health_check_seconds',
    'Time spent running health checks'
)
```

***REMOVED******REMOVED******REMOVED*** Health Check Endpoint

```http
GET /api/resilience/health-check
```

**Response:**
```json
{
  "status": "healthy",
  "defense_level": "GREEN",
  "utilization": 0.65,
  "metrics": {
    "coverage_ratio": 0.98,
    "compliance_score": 0.99,
    "stability_index": 0.92,
    "fairness_gini": 0.08
  },
  "contingency": {
    "n1_resilient": true,
    "n2_resilient": true,
    "critical_personnel": []
  },
  "last_check": "2025-01-15T10:30:00Z"
}
```

---

***REMOVED******REMOVED*** Automated Tasks

***REMOVED******REMOVED******REMOVED*** Celery Background Tasks

```python
***REMOVED*** app/resilience/tasks.py

@celery_app.task
def run_health_check():
    """Periodic health check task."""

    metrics = calculate_all_metrics()

    ***REMOVED*** Update defense level
    defense_level = determine_defense_level(metrics)

    ***REMOVED*** Take automated actions if configured
    if settings.RESILIENCE_AUTO_ACTIVATE_DEFENSE:
        execute_defense_level_actions(defense_level)

    ***REMOVED*** Send alerts if needed
    if defense_level >= DefenseLevel.YELLOW:
        send_resilience_alerts(defense_level, metrics)

    return {
        "defense_level": defense_level.value,
        "metrics": metrics
    }

@celery_app.task
def run_contingency_analysis():
    """Periodic contingency analysis task."""

    schedule = get_current_schedule()

    n1_result = perform_n1_analysis(schedule)
    n2_result = perform_n2_analysis(schedule)

    ***REMOVED*** Alert on failures
    if not n1_result["n1_resilient"]:
        alert_contingency_failure("N-1", n1_result)

    return {
        "n1": n1_result,
        "n2": n2_result
    }
```

***REMOVED******REMOVED******REMOVED*** Task Schedule (Celery Beat)

```python
CELERY_BEAT_SCHEDULE = {
    'health-check': {
        'task': 'app.resilience.tasks.run_health_check',
        'schedule': timedelta(minutes=15),  ***REMOVED*** Every 15 minutes
    },
    'contingency-analysis': {
        'task': 'app.resilience.tasks.run_contingency_analysis',
        'schedule': timedelta(hours=24),  ***REMOVED*** Daily
    },
    'fallback-regeneration': {
        'task': 'app.resilience.tasks.regenerate_fallbacks',
        'schedule': timedelta(hours=6),  ***REMOVED*** Every 6 hours
    },
}
```

---

***REMOVED******REMOVED*** Configuration

***REMOVED******REMOVED******REMOVED*** Environment Variables

```env
***REMOVED*** Defense level thresholds
RESILIENCE_WARNING_THRESHOLD=0.70
RESILIENCE_MAX_UTILIZATION=0.80
RESILIENCE_CRITICAL_THRESHOLD=0.90
RESILIENCE_EMERGENCY_THRESHOLD=0.95

***REMOVED*** Automated responses
RESILIENCE_AUTO_ACTIVATE_DEFENSE=true
RESILIENCE_AUTO_ACTIVATE_FALLBACK=false
RESILIENCE_AUTO_SHED_LOAD=false

***REMOVED*** Check intervals
RESILIENCE_HEALTH_CHECK_INTERVAL_MINUTES=15
RESILIENCE_CONTINGENCY_ANALYSIS_INTERVAL_HOURS=24

***REMOVED*** Alerting
RESILIENCE_ALERT_RECIPIENTS=admin@example.com
RESILIENCE_SLACK_CHANNEL=***REMOVED***residency-alerts
```

***REMOVED******REMOVED******REMOVED*** Tuning Thresholds

Adjust thresholds based on your program's risk tolerance:

| Setting | Conservative | Moderate | Aggressive |
|---------|--------------|----------|------------|
| Warning | 0.65 | 0.70 | 0.75 |
| Max Utilization | 0.75 | 0.80 | 0.85 |
| Critical | 0.85 | 0.90 | 0.95 |
| Emergency | 0.90 | 0.95 | 0.98 |

---

***REMOVED******REMOVED*** Alerting Integration

***REMOVED******REMOVED******REMOVED*** Email Alerts

```python
async def send_resilience_alert(level, metrics):
    """Send email alert for resilience status."""

    recipients = settings.RESILIENCE_ALERT_RECIPIENTS.split(',')

    subject = f"[{level.name}] Residency Scheduler Alert"

    body = render_template("resilience_alert.html", {
        "level": level,
        "metrics": metrics,
        "timestamp": datetime.utcnow()
    })

    await send_email(recipients, subject, body)
```

***REMOVED******REMOVED******REMOVED*** Slack Integration (via n8n)

The n8n workflow automation handles Slack alerts:

```json
{
  "name": "Resilience Alert to Slack",
  "nodes": [
    {
      "type": "webhook",
      "parameters": {
        "path": "resilience-alert"
      }
    },
    {
      "type": "slack",
      "parameters": {
        "channel": "***REMOVED***residency-alerts",
        "message": "🚨 Defense Level: {{$json.level}}\nUtilization: {{$json.utilization}}%"
      }
    }
  ]
}
```

---

***REMOVED******REMOVED*** Dashboard

***REMOVED******REMOVED******REMOVED*** Resilience Dashboard View

The frontend provides a dedicated resilience dashboard:

- **Defense Level Indicator** - Visual status badge
- **Utilization Gauge** - Real-time utilization meter
- **Metrics Panel** - Key health metrics
- **Alert History** - Recent alerts and responses
- **Contingency Status** - N-1/N-2 analysis results

***REMOVED******REMOVED******REMOVED*** API Endpoint

```http
GET /api/resilience/dashboard
```

Returns all data needed for the resilience dashboard in a single request.

---

***REMOVED******REMOVED*** Best Practices

***REMOVED******REMOVED******REMOVED*** Operational Guidelines

1. **Monitor daily** - Review resilience dashboard at start of each day
2. **Investigate warnings** - Don't ignore YELLOW status
3. **Pre-plan coverage** - Identify backups before absences
4. **Test fallbacks** - Periodically validate fallback schedules
5. **Update thresholds** - Adjust based on historical patterns

***REMOVED******REMOVED******REMOVED*** Response Playbooks

Create documented playbooks for each defense level:

***REMOVED******REMOVED******REMOVED******REMOVED*** YELLOW Response Playbook
1. Review upcoming absences for next 2 weeks
2. Confirm backup personnel availability
3. Prepare overtime authorization if needed
4. Schedule check-in for 24 hours

***REMOVED******REMOVED******REMOVED******REMOVED*** ORANGE Response Playbook
1. Activate contingency roster
2. Contact backup personnel
3. Notify affected residents
4. Escalate to program director
5. Schedule check-in for 12 hours

***REMOVED******REMOVED******REMOVED******REMOVED*** RED Response Playbook
1. Emergency team meeting
2. Implement overtime
3. Cancel non-essential activities
4. External resource assessment
5. Continuous monitoring

---

***REMOVED******REMOVED*** Related Documentation

- [Architecture](Architecture) - System design
- [Configuration](Configuration) - Environment setup
- [API Reference](API-Reference) - API documentation
- [Troubleshooting](Troubleshooting) - Common issues
