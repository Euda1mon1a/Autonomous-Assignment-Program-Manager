# Monitoring Dashboard Specifications

> **Last Updated:** 2025-12-31
> **Purpose:** Grafana dashboard specifications for comprehensive system monitoring

---

## Table of Contents

1. [System Health Dashboard](#system-health-dashboard)
2. [Scheduler Performance Dashboard](#scheduler-performance-dashboard)
3. [ACGME Compliance Dashboard](#acgme-compliance-dashboard)
4. [Resilience Metrics Dashboard](#resilience-metrics-dashboard)
5. [Swap Activity Dashboard](#swap-activity-dashboard)
6. [User Activity Dashboard](#user-activity-dashboard)
7. [Error Tracking Dashboard](#error-tracking-dashboard)
8. [SLA Monitoring Dashboard](#sla-monitoring-dashboard)
9. [Grafana JSON Exports](#grafana-json-exports)

---

## System Health Dashboard

### Purpose
Monitor overall system health, dependencies, and availability.

### Key Metrics

| Metric | Source | Alert Threshold | Description |
|--------|--------|-----------------|-------------|
| **System Status** | `/health` endpoint | Any UNHEALTHY | Overall system health status |
| **Database Availability** | health_checks.py | > 5s latency | Database connectivity and latency |
| **Redis Availability** | health_checks.py | > 100ms latency | Cache system health |
| **API Uptime** | request_total metric | < 99.9% | HTTP API availability |
| **Active Connections** | db_connections_in_use | > 80 | Database connection pool usage |
| **Memory Usage** | system metric | > 85% | System memory utilization |
| **CPU Usage** | system metric | > 80% | System CPU utilization |
| **Disk Usage** | system metric | > 85% | Disk space availability |

### Dashboard Panels

**Row 1: Overall Status**
- Status card showing current system health
- Uptime gauge (percentage)
- Incident count (active alerts)

**Row 2: Dependency Health**
- Database health (status + latency)
- Redis health (status + memory)
- External services (if any)

**Row 3: System Resources**
- CPU usage gauge and trend
- Memory usage gauge and trend
- Disk usage gauge
- Active connections graph

**Row 4: Error Rate**
- Error rate over time
- 5xx errors count
- 4xx errors count
- Exception count

### Example Queries

```sql
-- Database Availability
avg(rate(db_connections_in_use[5m]))

-- Error Rate
rate(error_total[5m])

-- Request Latency
histogram_quantile(0.95, rate(request_latency_seconds_bucket[5m]))
```

---

## Scheduler Performance Dashboard

### Purpose
Monitor schedule generation performance and quality.

### Key Metrics

| Metric | Source | Alert Threshold | Description |
|--------|--------|-----------------|-------------|
| **Generation Time** | schedule_generation_seconds | > 300s | Time to generate schedule |
| **Success Rate** | schedule_generation_success_total | < 95% | Percentage of successful generations |
| **Quality Score** | schedule_quality_score | < 80 | Generated schedule quality (0-100) |
| **Solver Iterations** | solver_iterations | > 1000 | Number of solver iterations needed |
| **Remaining Conflicts** | solver_conflicts | > 10 | Unresolved scheduling conflicts |
| **Rotation Balance** | schedule_rotation_balance | < 85 | Fairness of rotation distribution |
| **Assignment Latency** | assignment_latency_seconds | > 1s | Time to create assignment |

### Dashboard Panels

**Row 1: Generation Performance**
- Generation time histogram (by block count)
- Success rate gauge
- Failure reasons pie chart

**Row 2: Schedule Quality**
- Quality score gauge
- Quality trend over time
- Rotation balance visualization

**Row 3: Solver Performance**
- Iterations graph
- Conflict count trend
- Solver convergence rate

**Row 4: Assignment Performance**
- Assignment creation latency histogram
- Assignments per minute
- Assignment error rate

### Example Queries

```sql
-- Average Generation Time
avg(schedule_generation_seconds)

-- Success Rate
sum(schedule_generation_success_total) /
  (sum(schedule_generation_success_total) + sum(schedule_generation_failure_total))

-- Quality Score
schedule_quality_score
```

---

## ACGME Compliance Dashboard

### Purpose
Monitor ACGME regulatory compliance status in real-time.

### Key Metrics

| Metric | Source | Alert Threshold | Description |
|--------|--------|-----------------|-------------|
| **Compliance Rate** | compliance_rate | < 100% | Overall ACGME compliance percentage |
| **80-Hour Violations** | work_hour_violation_total | > 0 | Work hour rule violations |
| **1-in-7 Violations** | rest_day_violation_total | > 0 | Rest day rule violations |
| **Supervision Violations** | supervision_ratio_violation_total | > 0 | Supervision ratio violations |
| **Average Work Hours** | average_work_hours | > 80 | Weekly average work hours |
| **Max Work Hours** | max_work_hours | > 80 | Weekly maximum work hours |
| **Compliance Checks** | compliance_check_total | N/A | Total checks performed |

### Dashboard Panels

**Row 1: Overall Compliance**
- Compliance rate gauge
- Compliance trend line
- Violation count by type

**Row 2: Rule-Specific Compliance**
- 80-hour rule status (by training level)
- 1-in-7 rule status
- Supervision ratio status

**Row 3: Work Hours Analysis**
- Average work hours by training level
- Maximum work hours trend
- Work hour distribution histogram

**Row 4: Violation Details**
- Recent violations table
- Violation trend graph
- At-risk residents (approaching limits)

### Example Queries

```sql
-- Compliance Rate
(1 - (sum(compliance_violation_total) / sum(compliance_check_total))) * 100

-- 80-Hour Violations
rate(work_hour_violation_total[1w])

-- Average Work Hours by Level
avg(average_work_hours) by (training_level)
```

---

## Resilience Metrics Dashboard

### Purpose
Monitor system resilience and failure recovery capability.

### Key Metrics

| Metric | Source | Alert Threshold | Description |
|--------|--------|-----------------|-------------|
| **Resilience Score** | resilience_health_score | < 70 | Overall resilience (0-100) |
| **Defense Level** | defense_layer_status | > 3 (ORANGE) | Current defense layer (1-5) |
| **Utilization Rate** | utilization_rate | > 80% | System utilization (%) |
| **N-1 Contingency** | n_minus_one_contingency_count | < 3 | Available N-1 plans |
| **N-2 Contingency** | n_minus_two_contingency_count | < 2 | Available N-2 plans |
| **Recovery Distance** | recovery_distance | > 50 | Edits needed for N-1 recovery |
| **Cascade Risk** | cascade_failure_risk | > 50% | Risk of cascade failure |
| **Burnout Rt** | burnout_reproduction_number | > 1.0 | Burnout spread rate |

### Dashboard Panels

**Row 1: Resilience Status**
- Resilience score gauge
- Defense level indicator
- Cascade failure risk gauge

**Row 2: Utilization & Contingency**
- Utilization rate gauge
- N-1/N-2 contingency counts
- Recovery distance metric

**Row 3: Defense Layers**
- Defense layer status (1-5)
- Layer transition history
- Breach risk by layer

**Row 4: Burnout Analysis**
- Burnout Rt trend
- Reproduction number by person
- SIR model predictions

---

## Swap Activity Dashboard

### Purpose
Monitor schedule swap requests and execution.

### Key Metrics

| Metric | Source | Alert Threshold | Description |
|--------|--------|-----------------|-------------|
| **Swap Requests** | swap_request_total | N/A | Total swap requests received |
| **Execution Count** | swap_execution_total | N/A | Completed swaps (by status) |
| **Execution Time** | swap_execution_seconds | > 10s | Time to execute swap |
| **Validation Failures** | swap_validation_failure_total | > 10% | Failed validation checks |
| **Queue Depth** | swap_queue_depth | > 50 | Pending swaps in queue |
| **Compatibility Checks** | swap_compatibility_check_seconds | > 1s | Time for compatibility check |

### Dashboard Panels

**Row 1: Swap Activity**
- Requests per day (time series)
- Successful swaps percentage
- Failed swaps percentage

**Row 2: Performance**
- Execution time histogram
- Compatibility check time histogram
- Queue depth trend

**Row 3: Validation**
- Validation failure reasons (pie chart)
- Failure rate trend
- Affected residents count

**Row 4: SLA Metrics**
- Swap processing time SLA (target 5 minutes)
- SLA compliance percentage
- P95 processing time

---

## User Activity Dashboard

### Purpose
Monitor user engagement and system usage patterns.

### Key Metrics

| Metric | Source | Alert Threshold | Description |
|--------|--------|-----------------|-------------|
| **Active Users** | active_users | N/A | Current active users by role |
| **User Actions** | user_action_total | N/A | Actions by type and role |
| **Login Count** | login_total | > 5 failures in 1h | Login attempts (success/failure) |
| **Session Duration** | session_duration_seconds | N/A | Average session length |
| **API Key Usage** | api_key_usage_total | N/A | API key activity |
| **Role Distribution** | user_role_distribution | N/A | Users by role |

### Dashboard Panels

**Row 1: User Activity**
- Active users gauge (by role)
- User actions graph (by type)
- Login success rate

**Row 2: Session Metrics**
- Average session duration
- Session count trend
- Session duration distribution

**Row 3: API Usage**
- API key usage by endpoint
- Top API consumers
- API key activity heatmap

**Row 4: User Demographics**
- Role distribution pie chart
- Users per role trend
- Activity by time of day

---

## Error Tracking Dashboard

### Purpose
Monitor application errors and exceptions.

### Key Metrics

| Metric | Source | Alert Threshold | Description |
|--------|--------|-----------------|-------------|
| **Error Rate** | error_total | > 5% | Errors per minute |
| **Exception Count** | exception_total | > 10 | Total exceptions by type |
| **Error By Type** | error_total[error_type] | N/A | Errors grouped by type |
| **Error By Endpoint** | error_total[endpoint] | N/A | Errors grouped by endpoint |
| **5xx Status Codes** | request_total[status=5xx] | > 1% | Server error rate |

### Dashboard Panels

**Row 1: Error Overview**
- Error rate gauge
- Error trend graph
- Critical errors count

**Row 2: Error Distribution**
- Top 10 error types (table)
- Error distribution pie chart
- Error timeline

**Row 3: Exception Details**
- Exception count by type
- Stack trace preview
- First occurrence date

**Row 4: Endpoint Health**
- Error rate by endpoint (table)
- Problem endpoints ranking
- Error correlation analysis

---

## SLA Monitoring Dashboard

### Purpose
Monitor Service Level Agreement compliance.

### Key Metrics

| Metric | Source | Target | Description |
|--------|--------|--------|-------------|
| **Availability** | uptime_percent | 99.9% | System availability percentage |
| **Response Time P95** | request_latency_seconds | < 500ms | 95th percentile latency |
| **Response Time P99** | request_latency_seconds | < 1000ms | 99th percentile latency |
| **Error Rate** | error_total | < 0.1% | Percentage of requests that error |
| **Database Latency** | db_query_latency_seconds | < 100ms | Average database query time |

### Dashboard Panels

**Row 1: SLA Compliance**
- Availability percentage gauge
- SLA status (compliant/at-risk/violated)
- Monthly SLA summary

**Row 2: Response Time SLA**
- P95 response time gauge
- P99 response time gauge
- Response time trend

**Row 3: Reliability SLA**
- Error rate gauge
- Error budget remaining (%)
- Error budget consumption

**Row 4: Monthly Summary**
- SLA compliance table
- Uptime percentage
- Availability by day

---

## Grafana JSON Exports

All dashboards are exported as Grafana JSON for version control and reproducibility.

### Import Instructions

1. Access Grafana: `http://grafana-host:3000`
2. Go to **Dashboards** → **Import**
3. Paste JSON content or upload file
4. Select Prometheus data source
5. Click **Import**

### Dashboard JSON Structure

Each dashboard includes:

```json
{
  "dashboard": {
    "title": "Dashboard Name",
    "description": "Dashboard purpose",
    "tags": ["monitoring", "category"],
    "timezone": "browser",
    "panels": [
      {
        "title": "Panel Title",
        "type": "graph|stat|gauge|table",
        "targets": [
          {
            "expr": "PromQL query",
            "legendFormat": "Legend format"
          }
        ]
      }
    ]
  }
}
```

### Key Grafana Features Used

- **Auto-refresh**: 30 seconds default
- **Time range**: Last 6 hours default (user adjustable)
- **Templating**: Variables for environment and service selection
- **Alerts**: Threshold-based visualization
- **Annotations**: Event markers and deployment tracking

### Prometheus Data Source

All dashboards connect to Prometheus at: `http://prometheus:9090`

Configuration:
- Scrape interval: 15 seconds
- Evaluation interval: 15 seconds
- Retention period: 15 days

---

## Dashboard Refresh Rates

| Dashboard | Refresh | Purpose |
|-----------|---------|---------|
| System Health | 30s | Real-time dependency monitoring |
| Scheduler | 1m | Generation performance tracking |
| Compliance | 5m | Regulatory compliance review |
| Resilience | 5m | System failure prediction |
| Swap Activity | 30s | Real-time queue monitoring |
| User Activity | 5m | Usage pattern analysis |
| Error Tracking | 30s | Real-time error detection |
| SLA Monitoring | 1m | Compliance tracking |

---

## Alert Integration

Dashboards integrate with alert manager:

1. **Critical Alerts**: Red background, pulsing border
2. **Warning Alerts**: Orange background
3. **Info Alerts**: Blue background
4. **Alert History**: Annotations on time-series graphs

### Alert Routing

- **Critical**: Email, SMS, PagerDuty
- **Warning**: Email, Slack
- **Info**: Slack only

---

## Best Practices

### Viewing Dashboards

1. **Real-time monitoring**: Use system health dashboard
2. **Performance analysis**: Review scheduler performance trends
3. **Compliance audits**: Use compliance dashboard for reporting
4. **Incident response**: Quickly navigate to error tracking dashboard
5. **Capacity planning**: Track utilization trends on resilience dashboard

### Customization

Dashboards can be customized by:
- Adding custom variables (environment, service)
- Creating dashboard-specific alerts
- Combining panels into views
- Setting up scheduled reports

### Troubleshooting

| Issue | Solution |
|-------|----------|
| No data in dashboard | Check Prometheus connectivity and scrape targets |
| Metrics missing | Verify application is emitting metrics |
| Slow dashboard load | Reduce time range or add more specific filters |
| Alert not firing | Check alert rule threshold and data availability |

---

## Related Documentation

- **Metrics Collection**: See `backend/app/monitoring/metrics.py`
- **Logging Configuration**: See `backend/app/monitoring/logging_config.py`
- **Alert System**: See `backend/app/monitoring/alerts.py`
- **Health Checks**: See `backend/app/monitoring/health_checks.py`
- **Observability Guide**: See `docs/monitoring/OBSERVABILITY_GUIDE.md`

---

*Dashboard specifications are maintained as living documentation. Update when new metrics or dashboards are added.*
