# Scheduler Dashboards and Alert Rules

This document describes the Grafana dashboards and Prometheus alert rules created specifically for the Residency Scheduler application, with focus on resilience monitoring, ACGME compliance, and background task execution.

## New Files Created

### Grafana Dashboards

1. **`grafana/dashboards/scheduler_overview.json`**
   - Main system health and performance dashboard
   - Best for: Day-to-day monitoring and ops team

2. **`grafana/dashboards/resilience_metrics.json`**
   - Resilience framework deep-dive
   - Best for: Capacity planning and incident response

3. **`grafana/dashboards/celery_tasks.json`**
   - Background task monitoring
   - Best for: Worker scaling and job debugging

### Configuration Files

4. **`grafana/provisioning/datasources/prometheus.yml`**
   - Auto-configures Prometheus as Grafana datasource

5. **`prometheus/alerts/scheduler_alerts.yml`**
   - Comprehensive alert rules for all critical conditions

## Dashboard Details

### 1. Scheduler Overview Dashboard

**Purpose**: Primary operational dashboard for daily monitoring

**Key Panels**:

| Panel | Metric | Purpose |
|-------|--------|---------|
| System Utilization | `resilience_utilization_rate` | Gauge showing current utilization with 80% threshold marker |
| Defense Level | `resilience_defense_level` | Current Defense-in-Depth level (1-5) |
| Schedule Coverage | `resilience_coverage_rate` | Percentage of blocks with valid assignments |
| ACGME Compliance | `(resilience_n1_compliant + resilience_n2_compliant) / 2` | N-1/N-2 compliance score |
| Faculty Available | `resilience_faculty_available` | On-duty vs total faculty count |
| Active Fallbacks | `resilience_active_fallbacks` | Number of emergency fallback schedules active |
| Utilization Over Time | `resilience_utilization_rate` (time series) | Trend analysis with threshold line |
| Schedule Operations | `rate(schedule_generation_total[5m])` | Success/failure rates by algorithm |
| ACGME Violations | `rate(schedule_violations_total[5m])` | Violation types detected |
| Task Queue Depth | `celery_queue_length` | Background job backlog |
| Auth Success Rate | Token issuance vs failures | Authentication health (24h) |
| Idempotency Hit Rate | Cache hits vs total requests | API efficiency (1h) |
| Schedule Gen Time | `schedule_generation_duration_seconds` | Average generation latency |

**Thresholds**:
- Utilization: Green <70%, Yellow 70-80%, Orange 80-90%, Red >90%
- Defense Level: Green (1), Yellow (2), Orange (3), Red (4), Dark Red (5)
- Coverage: Red <85%, Yellow 85-95%, Green >95%

**Refresh Rate**: 30 seconds

**Time Range**: Default 6 hours, with quick selectors for 1h, 12h, 24h, 7d

### 2. Resilience Metrics Dashboard

**Purpose**: Detailed resilience framework analysis and capacity planning

**Key Panels**:

| Panel | Metric | Purpose |
|-------|--------|---------|
| Utilization Gauge | `resilience_utilization_rate` | Large gauge with 80% threshold from queuing theory |
| Defense Level Status | `resilience_defense_level` | Current level with detailed descriptions |
| Defense Level History | Time series of defense level changes | Trend analysis and pattern detection |
| N-1 Contingency | `resilience_n1_compliant` | Can system survive loss of 1 faculty? |
| N-2 Contingency | `resilience_n2_compliant` | Can system survive loss of 2 faculty? |
| Capacity Buffer | `resilience_buffer_remaining` | Distance from 80% threshold |
| Load Shedding Level | `resilience_load_shedding_level` | Current sacrifice hierarchy level (0-5) |
| Faculty Availability | Time series by type (total/on_duty/on_leave) | Staffing trends |
| Coverage vs Utilization | Dual time series | Correlation analysis |
| Crisis Activations | `resilience_crisis_activations_total` | Cumulative by severity |
| Fallback Activations | `resilience_fallback_activations_total` | Emergency response events |
| Health Check Duration | Histogram quantiles (p50, p95) | Performance monitoring |
| Contingency Analysis Duration | N-1/N-2 computation time | System complexity indicator |
| Active Fallbacks | Current count | Emergency mode status |
| Suspended Activities | Load shedding impact | Number of non-essential activities suspended |
| Health Check Failures | 24h failure count | System reliability |

**Special Features**:
- **80% Threshold**: Prominently displayed based on queuing theory (M/M/c model)
- **Defense Level Mapping**: Text overlays explain each level
  - Level 1: Prevention (Proactive Monitoring)
  - Level 2: Detection (Early Warning Active)
  - Level 3: Response (Load Shedding)
  - Level 4: Recovery (Fallback Active)
  - Level 5: Emergency (Crisis Mode)
- **Step-after interpolation**: Shows exact timing of level changes

**Refresh Rate**: 1 minute

**Time Range**: Default 12 hours (resilience patterns emerge over longer periods)

### 3. Celery Tasks Dashboard

**Purpose**: Background task execution monitoring and worker health

**Key Panels**:

| Panel | Metric | Purpose |
|-------|--------|---------|
| Active Workers | `celery_workers` | Number of healthy workers |
| Total Queue Depth | `sum(celery_queue_length)` | All queues combined |
| Task Success Rate | Success / (Success + Failure) | Overall job health (5m) |
| Tasks Running | `sum(celery_tasks_active)` | Currently executing tasks |
| Success/Failure Rates | `rate(celery_task_*_total[5m])` | By task name |
| Queue Depths by Queue | `celery_queue_length` | Per-queue monitoring |
| Task Duration | Histogram quantiles (p50, p95, p99) | Performance distribution |
| Active Tasks by Worker | `celery_tasks_active` by worker | Load balancing visibility |
| Task Statistics Table | Success rate, failure rate, p95 duration | Sortable table view |
| Resilience Health Check | Specific task monitoring | Critical task performance |
| N-1/N-2 Analysis Task | Contingency analysis job | Long-running task health |
| Total Processed (24h) | Daily task volume | Throughput metrics |
| Total Failures (24h) | Daily failure count | Reliability metrics |
| Avg Task Duration (1h) | Recent average | Performance baseline |

**Thresholds**:
- Workers: Red if 0, Green if >0
- Queue Depth: Green <50, Yellow 50-100, Orange 100-500, Red >500
- Success Rate: Red <90%, Yellow 90-95%, Green >95%
- Task Duration: Green <10s, Yellow 10-60s, Red >60s

**Variable Templates**:
- `$queue`: Multi-select dropdown for filtering by queue name

**Refresh Rate**: 30 seconds

**Time Range**: Default 6 hours

## Alert Rules

### Alert Structure

All alerts include:
- **Labels**: `severity`, `component`, `tier`, `compliance`, `page`
- **Annotations**: `summary`, `description`, `runbook_url`, `action_required`

### Critical Alerts (Page Oncall)

These alerts have `page: "true"` label and should trigger PagerDuty/oncall system:

| Alert | Condition | Duration | Action |
|-------|-----------|----------|--------|
| **CriticalUtilization** | >90% utilization | 2m | Activate load shedding, review staff availability |
| **DefenseLevelCritical** | Level 4-5 (Recovery/Emergency) | 5m | Review fallbacks, assess incident severity |
| **BothContingenciesFailed** | N-1 AND N-2 both failing | 30m | URGENT: Review staffing, activate protocols |
| **CriticalCoverageGap** | <85% coverage | 5m | Immediate schedule review, consider fallbacks |
| **CriticalFacultyShortage** | <3 faculty on duty | 5m | Contact on-call staff, activate emergency staffing |
| **CriticalLoadShedding** | Level 4-5 | 2m | Review suspended activities, assess duration |
| **ACGMEViolationDetected** | Any violation | 2m | Correct assignments, document remediation |
| **CeleryTaskFailureRateCritical** | >20% failure rate | 5m | Check worker logs, verify Redis connectivity |
| **CeleryQueueBacklogCritical** | >500 pending tasks | 5m | Scale workers, investigate slow tasks |
| **CeleryNoWorkers** | 0 active workers | 2m | Start workers immediately, check Redis |
| **SuspiciousAuthActivity** | Token tampering detected | 2m | Review access logs, check for compromised tokens |

### Warning Alerts (Slack Notification)

| Alert | Condition | Duration | Investigation |
|-------|-----------|----------|---------------|
| **HighUtilization** | >80% utilization | 5m | Monitor for cascade failure risk |
| **DefenseLevelDegraded** | Level 2-3 | 10m | System detected potential issues |
| **N1ContingencyFailed** | N-1 fails | 15m | Review staff availability, consider load reduction |
| **ScheduleCoverageGap** | <95% coverage | 10m | Some blocks may lack adequate assignments |
| **LowFacultyAvailability** | <5 faculty on duty | 15m | Monitor utilization closely |
| **LoadSheddingActive** | Level 1-3 | 5m | Non-essential activities suspended |
| **HighViolationRate** | >0.1 violations/sec (1h) | 10m | Review scheduling logic |
| **CeleryTaskFailureRate** | >5% failure rate | 10m | Check task logs |
| **CeleryQueueBacklog** | >100 pending | 15m | Workers may be overloaded |
| **ResilienceHealthCheckStale** | No check in >20min | 5m | Check Celery beat scheduler |
| **SlowScheduleGeneration** | p95 >60s | 10m | May impact user experience |
| **ScheduleGenerationFailures** | >0.01/sec | 5m | Review algorithm errors |
| **HighAuthFailureRate** | >1/sec | 5m | Possible brute force attack |

### Info Alerts (Email)

| Alert | Condition | Duration | Note |
|-------|-----------|----------|------|
| **N2ContingencyFailed** | N-2 fails | 5m | Expected during high utilization |
| **HighTokenBlacklistRate** | >0.5/sec (10m) | 5m | Monitor for anomalies |
| **HighContingencyAnalysisDuration** | p95 >120s | 15m | Performance or complexity indicator |

### Alert Groups

#### 1. `scheduler_resilience`
- Utilization monitoring
- Defense-in-Depth levels
- N-1/N-2 contingency
- Coverage and staffing
- Load shedding

**Interval**: 30s

#### 2. `scheduler_compliance`
- ACGME violation detection
- Violation rate tracking

**Interval**: 1m

#### 3. `scheduler_tasks`
- Celery worker health
- Task failure rates
- Queue backlogs
- Health check staleness

**Interval**: 1m

#### 4. `scheduler_performance`
- Schedule generation speed
- Contingency analysis duration
- General performance degradation

**Interval**: 1m

#### 5. `scheduler_security`
- Authentication failures
- Token tampering
- Suspicious activity

**Interval**: 1m

## Deployment

### Quick Deploy with Existing Monitoring Stack

If using the existing `docker-compose.monitoring.yml`:

```bash
# Dashboards are already in place
cd /home/user/Autonomous-Assignment-Program-Manager/monitoring

# Copy alert rules to Prometheus rules directory
cp prometheus/alerts/scheduler_alerts.yml prometheus/rules/

# Reload Prometheus
docker-compose -f docker-compose.monitoring.yml exec prometheus kill -HUP 1

# Restart Grafana to pick up new dashboards
docker-compose -f docker-compose.monitoring.yml restart grafana
```

### Verify Deployment

1. **Check Prometheus Alerts**:
   ```bash
   curl http://localhost:9090/api/v1/rules | jq '.data.groups[] | select(.name | contains("scheduler"))'
   ```

2. **Check Grafana Dashboards**:
   - Open http://localhost:3001
   - Navigate to Dashboards → Browse
   - Look for "Residency Scheduler" folder
   - Verify 3 dashboards present

3. **Test Metrics**:
   ```bash
   # Check resilience metrics
   curl http://localhost:8000/metrics | grep resilience_

   # Check if Prometheus is scraping
   curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.labels.job == "scheduler-backend")'
   ```

## Metric Sources

All metrics referenced in dashboards and alerts come from:

1. **Resilience Metrics**: `/home/user/Autonomous-Assignment-Program-Manager/backend/app/resilience/metrics.py`
   - `ResilienceMetrics` class
   - Exposed via `/metrics` endpoint

2. **Observability Metrics**: `/home/user/Autonomous-Assignment-Program-Manager/backend/app/core/observability.py`
   - `ObservabilityMetrics` class
   - Authentication, idempotency, scheduling metrics

3. **Celery Metrics**: Provided by `celery-exporter` or similar tool
   - Worker counts, queue depths, task statistics

## Customization

### Adjusting Alert Thresholds

Edit `monitoring/prometheus/alerts/scheduler_alerts.yml`:

```yaml
# Example: Lower utilization warning threshold
- alert: HighUtilization
  expr: resilience_utilization_rate{component="overall"} > 0.70  # Changed from 0.80
  for: 5m
```

### Adding Dashboard Panels

Dashboards use standard Grafana JSON format. To add a panel:

1. Edit the dashboard JSON file
2. Add to `panels` array
3. Specify `gridPos` for layout
4. Add `targets` with PromQL queries
5. Configure `fieldConfig` for thresholds and units

### Modifying Time Ranges

In dashboard JSON, update:

```json
"time": {
  "from": "now-24h",  // Change from default
  "to": "now"
}
```

## Runbook Integration

All critical alerts include `runbook_url` annotations. Update these to point to your documentation:

```yaml
annotations:
  runbook_url: "https://docs.your-org.com/runbooks/high-utilization"
```

Runbooks should document:
1. **What this alert means**
2. **Why it's important**
3. **How to investigate**
4. **What actions to take**
5. **Who to escalate to**

## Dashboard Variables

Dashboards support templating for dynamic filtering:

### Example: Queue Filter (Celery Dashboard)

```json
"templating": {
  "list": [
    {
      "name": "queue",
      "type": "query",
      "datasource": "${datasource}",
      "query": "label_values(celery_queue_length, queue)",
      "multi": true,
      "includeAll": true
    }
  ]
}
```

Use in queries as `{queue=~"$queue"}`

## Best Practices

### 1. Alert Tuning

- **Start conservative**: Better to have false positives initially
- **Tune based on patterns**: Adjust thresholds after observing normal behavior
- **Document changes**: Track why thresholds were adjusted

### 2. Dashboard Organization

- **Overview first**: Start with high-level view
- **Drill-down pattern**: Link to detailed dashboards
- **Consistent colors**: Use same color scheme across dashboards

### 3. Alert Fatigue Prevention

- **Use appropriate durations**: Allow time for transient issues to resolve
- **Group related alerts**: Avoid multiple alerts for same root cause
- **Regular review**: Disable or tune noisy alerts

### 4. Incident Response

- **Playbooks**: Create runbooks for each critical alert
- **Practice**: Run game days to test response procedures
- **Post-mortems**: Document incidents and improve alerts

## Monitoring the Monitors

Set up meta-monitoring to ensure the monitoring stack itself is healthy:

```yaml
# Example: Alert if Prometheus can't scrape backend
- alert: PrometheusTargetDown
  expr: up{job="scheduler-backend"} == 0
  for: 2m
  labels:
    severity: critical
  annotations:
    summary: "Prometheus cannot scrape scheduler backend"
```

## Support

### Common Issues

**Q: Dashboards show "No Data"**
- Check Prometheus targets: http://localhost:9090/targets
- Verify backend metrics endpoint: http://localhost:8000/metrics
- Check Grafana datasource: Configuration → Data Sources

**Q: Alerts not firing**
- Verify rules loaded: http://localhost:9090/rules
- Check alert evaluation: http://localhost:9090/alerts
- Review Alertmanager config: http://localhost:9093

**Q: Wrong time range in panels**
- Check browser timezone settings
- Verify Grafana timezone: User → Preferences
- Update dashboard time settings

### Getting Help

1. Check Prometheus logs: `docker-compose -f docker-compose.monitoring.yml logs prometheus`
2. Check Grafana logs: `docker-compose -f docker-compose.monitoring.yml logs grafana`
3. Review metric definitions in:
   - `/backend/app/resilience/metrics.py`
   - `/backend/app/core/observability.py`

## References

- **Main Monitoring README**: `/monitoring/README.md`
- **Prometheus Query Language**: https://prometheus.io/docs/prometheus/latest/querying/basics/
- **Grafana Dashboard Guide**: https://grafana.com/docs/grafana/latest/dashboards/
- **Alertmanager Configuration**: https://prometheus.io/docs/alerting/latest/configuration/
- **Queuing Theory (M/M/c)**: Justification for 80% threshold
