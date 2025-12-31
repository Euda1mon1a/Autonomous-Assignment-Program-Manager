# Observability Guide

> **Last Updated:** 2025-12-31
> **Purpose:** Complete guide to system observability, monitoring, and troubleshooting

---

## Table of Contents

1. [Overview](#overview)
2. [Observability Pillars](#observability-pillars)
3. [Metrics System](#metrics-system)
4. [Logging System](#logging-system)
5. [Tracing System](#tracing-system)
6. [Alerting System](#alerting-system)
7. [Health Checks](#health-checks)
8. [Troubleshooting](#troubleshooting)
9. [Best Practices](#best-practices)

---

## Overview

### What is Observability?

Observability is the ability to understand the internal state of a system from its external outputs (metrics, logs, traces). Unlike monitoring which tests for predefined behaviors, observability allows asking arbitrary questions about system behavior.

### Observability vs. Monitoring

| Aspect | Monitoring | Observability |
|--------|-----------|---------------|
| **Approach** | Predefined alerts | Exploratory analysis |
| **Data** | High-level metrics | Detailed logs, traces, metrics |
| **Use case** | Alerting on known issues | Investigating unknown issues |
| **Setup** | Simpler, less data | Complex, more comprehensive |

### System Components

The residency scheduler observability stack consists of:

1. **Metrics Collection** - Prometheus metrics
2. **Logging** - Structured JSON logs with correlation IDs
3. **Tracing** - OpenTelemetry distributed traces
4. **Alerting** - Alert definitions and escalation
5. **Health Checks** - Dependency health validation
6. **Visualization** - Grafana dashboards

---

## Observability Pillars

### 1. Metrics

Metrics are numeric measurements of system behavior over time.

**Types:**
- **Counter**: Monotonically increasing value (requests, errors)
- **Gauge**: Point-in-time value (memory usage, queue depth)
- **Histogram**: Distribution of values (latency, request size)
- **Summary**: Quantiles of values (percentiles of latency)

**Examples:**
```python
from app.monitoring.metrics import (
    request_count,
    request_latency,
    cache_hit_rate,
    schedule_generation_time,
)

# Record a request
request_count.labels(method='GET', endpoint='/schedules', status=200).inc()
request_latency.labels(method='GET', endpoint='/schedules').observe(0.123)

# Record a cache hit
cache_hit_rate.labels(cache_name='redis_schedule').set(92.5)
```

**Access:**
- Prometheus: `http://prometheus:9090`
- Metrics endpoint: `http://api:8000/metrics`

---

### 2. Logging

Structured logging provides detailed context for debugging and auditing.

**Log Levels:**
- **DEBUG**: Development and detailed troubleshooting
- **INFO**: Important application events
- **WARNING**: Warning conditions that should be investigated
- **ERROR**: Error conditions
- **CRITICAL**: Critical failures requiring immediate action

**Structured Log Format:**
```json
{
  "timestamp": "2025-12-31T12:34:56.789Z",
  "level": "INFO",
  "logger": "app.services.scheduler",
  "message": "Schedule generation started",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "context": {
    "block_count": 730,
    "person_count": 25,
    "generation_id": "gen-12345"
  }
}
```

**Log Categories:**
- `app.audit` - User actions and access logs
- `app.security` - Authentication and authorization events
- `app.performance` - Performance metrics and slow operations
- `app.compliance` - ACGME compliance events

**Usage:**
```python
from app.monitoring.logging_config import (
    audit_logger,
    security_logger,
    performance_logger,
)

# Audit log
audit_logger.log_user_action(
    action='create_schedule',
    user_id='user123',
    resource='schedules',
    details={'block_count': 730}
)

# Security log
security_logger.log_authentication_attempt(
    username='user@example.com',
    success=True,
    ip_address='192.168.1.1'
)

# Performance log
performance_logger.log_query_performance(
    query='SELECT * FROM assignments',
    duration_ms=45.2,
    rows_affected=150
)
```

**Accessing Logs:**
- Log files: `/var/log/residency-scheduler/`
- Structured log viewer: Use JSON parsing tools
- Centralized logging: ELK/Loki integration (optional)

---

### 3. Tracing

Distributed tracing tracks requests across service boundaries.

**Key Concepts:**
- **Trace**: Complete request journey through system
- **Span**: Single operation within a trace
- **Context**: Correlation information propagated across services

**Example:**
```
GET /schedules (Trace ID: abc123)
  ├─ HTTP Request Processing (Span: span1)
  ├─ Database Query (Span: span2, Parent: span1)
  │  └─ Connection Pool (Span: span3, Parent: span2)
  └─ Response Serialization (Span: span4, Parent: span1)
```

**Usage:**
```python
from app.monitoring.tracing import (
    get_tracer,
    TraceContext,
    performance_tracer,
)

# Get current trace context
trace_id = TraceContext.get_trace_id()
span_id = TraceContext.get_span_id()

# Add attributes to current span
TraceContext.set_span_attribute('user_id', 'user123')
TraceContext.set_span_attribute('block_count', 730)

# Trace a specific operation
with get_tracer().start_as_current_span('schedule.generation'):
    # Perform schedule generation
    pass

# Trace database query
performance_tracer.trace_database_query(
    operation='SELECT',
    table='assignments',
    query_time_ms=45.2,
    rows_affected=150
)
```

**Accessing Traces:**
- Jaeger UI: `http://jaeger:16686`
- Search by Trace ID or tags
- View span hierarchy and timings

---

### 4. Alerting

Alerts notify operators of important events.

**Alert Severity Levels:**
- **CRITICAL**: Immediate action required (database down, 95% utilization)
- **WARNING**: Action required soon (high error rate, slow queries)
- **INFO**: Informational (schedule generated, backup completed)

**Built-in Alerts:**

```python
from app.monitoring.alerts import (
    alert_manager,
    AlertSeverity,
    AlertCategory,
)

# Evaluate alerts against current metrics
triggered_alerts = alert_manager.evaluate_all({
    'db_available': True,
    'error_rate': 0.02,
    'utilization_rate': 92.5,
    'cascade_risk': 45.2,
})

# Acknowledge alert
alert_manager.acknowledge_alert(alert_id='alert123', user_id='user456')

# Resolve alert
alert_manager.resolve_alert(alert_id='alert123', user_id='user456')
```

**Alert Routing:**
- **Critical**: Email, SMS, PagerDuty
- **Warning**: Email, Slack
- **Info**: Slack only

**Custom Alerts:**
```python
from app.monitoring.alerts import (
    AlertDefinition,
    AlertCategory,
    AlertSeverity,
    alert_manager,
)

# Define custom alert
custom_alert = AlertDefinition(
    name='High Swap Queue Depth',
    description='Too many swaps pending',
    category=AlertCategory.SWAP,
    severity=AlertSeverity.WARNING,
    condition=lambda m: m.get('swap_queue_depth', 0) > 100,
    threshold=100.0,
    window_minutes=5,
)

# Register alert
alert_manager.register_definition(custom_alert)
```

---

### 5. Health Checks

Health checks validate system dependencies and readiness.

**Types of Checks:**

1. **Database Health**
   ```python
   from app.monitoring.health_checks import check_database_health
   result = await check_database_health(db)
   # result.status: HEALTHY, DEGRADED, or UNHEALTHY
   ```

2. **Redis Health**
   ```python
   from app.monitoring.health_checks import check_redis_health
   result = await check_redis_health(redis_client)
   ```

3. **External Services**
   ```python
   from app.monitoring.health_checks import check_external_service
   result = await check_external_service(
       service_name='notification_api',
       url='https://api.example.com/health'
   )
   ```

4. **System Resources**
   ```python
   from app.monitoring.health_checks import (
       check_disk_space,
       check_memory_usage,
       check_cpu_usage,
   )
   ```

**Health Check Endpoint:**
```python
@app.get('/health')
async def health_check(db: AsyncSession):
    """Get overall system health."""
    result = await health_check_coordinator.run_all_checks()
    return result.to_dict()
```

**Health Check Response:**
```json
{
  "overall_status": "healthy",
  "timestamp": "2025-12-31T12:34:56.789Z",
  "checks": [
    {
      "name": "database",
      "status": "healthy",
      "response_time_ms": 12.5,
      "details": {"connection_ok": true}
    },
    {
      "name": "redis",
      "status": "healthy",
      "response_time_ms": 3.2,
      "details": {"ping": "ok", "memory_used_mb": 123.4}
    }
  ],
  "summary": {
    "total": 8,
    "healthy": 8,
    "degraded": 0,
    "unhealthy": 0
  }
}
```

---

## Metrics System

### Metric Categories

#### 1. Request Metrics
```
request_total[method, endpoint, status]        # Total requests
request_latency_seconds[method, endpoint]      # Request latency histogram
request_size_bytes[method, endpoint]           # Request size
response_size_bytes[method, endpoint, status]  # Response size
concurrent_requests[method, endpoint]          # Active requests
```

#### 2. Error Metrics
```
error_total[error_type, endpoint, method]      # Total errors
error_rate[endpoint, method]                   # Error rate %
exception_total[exception_type, endpoint]      # Total exceptions
```

#### 3. Database Metrics
```
db_query_total[operation, table, status]       # Total queries
db_query_latency_seconds[operation, table]     # Query latency
db_connection_pool_size                        # Pool size
db_connections_in_use                          # In-use connections
db_transaction_duration_seconds                # Transaction time
```

#### 4. Cache Metrics
```
cache_hit_total[cache_name]                    # Cache hits
cache_miss_total[cache_name]                   # Cache misses
cache_hit_rate[cache_name]                     # Hit rate %
cache_size_bytes[cache_name]                   # Cache size
redis_memory_usage_bytes                       # Redis memory
```

#### 5. Scheduler Metrics
```
schedule_generation_seconds[block_count_range] # Gen time
schedule_generation_success_total              # Success count
schedule_quality_score                         # Quality 0-100
solver_iterations                              # Iterations needed
solver_conflicts                               # Remaining conflicts
```

#### 6. Compliance Metrics
```
compliance_rate                                # Compliance %
compliance_violation_total[violation_type]     # Violations
work_hour_violation_total                      # 80-hour violations
rest_day_violation_total                       # 1-in-7 violations
average_work_hours[training_level]             # Avg hours/week
```

#### 7. Resilience Metrics
```
resilience_health_score                        # Health 0-100
defense_layer_status[layer]                    # Layer 1-5
utilization_rate[resource]                     # Utilization %
cascade_failure_risk                           # Risk 0-100%
n_minus_one_contingency_count                  # N-1 plans
recovery_distance                              # Edits for N-1
```

#### 8. Swap Metrics
```
swap_request_total                             # Total requests
swap_execution_total[swap_type, status]        # Executions
swap_execution_seconds[swap_type]              # Exec time
swap_queue_depth                               # Pending swaps
```

#### 9. User Metrics
```
active_users[role]                             # Active count
user_action_total[action_type, role]           # Actions
login_total[status]                            # Login attempts
session_duration_seconds                       # Session length
```

---

## Logging System

### Log Configuration

**Configuration File:** `backend/app/monitoring/logging_config.py`

```python
from app.monitoring.logging_config import configure_logging, LogLevelManager

# Setup logging
configure_logging(
    log_dir='/var/log/residency-scheduler',
    level='INFO',
    console=True,
    file=True,
    json_format=True
)

# Change log levels at runtime
LogLevelManager.set_level('app.services.scheduler', 'DEBUG')
LogLevelManager.set_global_level('WARNING')
```

### Log Files

| File | Content |
|------|---------|
| `app.log` | General application logs |
| `error.log` | ERROR and CRITICAL level only |
| `audit.log` | User actions and access |
| `security.log` | Authentication and authorization |
| `performance.log` | Performance metrics and slow operations |
| `compliance.log` | ACGME compliance events |

### Sensitive Data Redaction

The logging system automatically redacts sensitive data:

```python
from app.monitoring.logging_config import SensitiveDataRedactor

# Data to redact
data = {
    'email': 'user@example.com',
    'password': 'secret123',
    'api_key': 'sk-abc123',
    'ssn': '123-45-6789'
}

# Redacted output
redacted = SensitiveDataRedactor.redact_dict(data)
# {
#   'email': '[REDACTED_email]',
#   'password': '[REDACTED]',
#   'api_key': '[REDACTED_api_key]',
#   'ssn': '[REDACTED_ssn]'
# }
```

### Correlation IDs

Every request gets a unique correlation ID to trace it through logs:

```python
from app.monitoring.logging_config import CorrelationIdFilter

# Correlation ID is automatically added to all log records
# Example log entry:
# {
#   "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
#   "message": "Schedule generation completed"
# }

# Search logs by correlation ID
# logs.filter(correlation_id="550e8400-e29b-41d4-a716-446655440000")
```

---

## Tracing System

### OpenTelemetry Configuration

**Configuration:**
```python
from app.monitoring.tracing import TracingSetup, TracingConfig

config = TracingConfig(
    service_name='residency-scheduler',
    environment='production',
    jaeger_host='jaeger',
    jaeger_port=6831,
    otlp_endpoint='http://localhost:4317',
    sample_rate=1.0,
    enable_jaeger=True,
)

setup = TracingSetup(config)
setup.setup_all(app)  # Setup with FastAPI app
```

### Span Attributes

Best practices for span attributes:

```python
from app.monitoring.tracing import TraceContext

# Add user context
TraceContext.set_span_attribute('user_id', 'user123')
TraceContext.set_span_attribute('user_role', 'faculty')

# Add operation context
TraceContext.set_span_attribute('operation', 'schedule_generation')
TraceContext.set_span_attribute('block_count', 730)

# Add result context
TraceContext.set_span_attribute('success', True)
TraceContext.set_span_attribute('generation_time_ms', 234.5)
```

### Trace Sampling

Control which traces are recorded:

```python
# Sample 10% of traces
config = TracingConfig(sample_rate=0.1)

# Sample based on tags
# High-priority operations: 100%
# Low-priority operations: 1%
```

---

## Alerting System

### Alert Definition Framework

```python
from app.monitoring.alerts import (
    AlertDefinition,
    AlertCategory,
    AlertSeverity,
)

definition = AlertDefinition(
    name='High Error Rate',
    description='Error rate exceeds 5%',
    category=AlertCategory.SYSTEM,
    severity=AlertSeverity.WARNING,
    condition=lambda m: m.get('error_rate', 0) > 5,
    threshold=5.0,
    window_minutes=5,
)
```

### Alert Lifecycle

1. **Trigger**: Condition evaluated and met
2. **Notify**: Alert routed to configured channels
3. **Escalate**: After N minutes, escalate if unacknowledged
4. **Acknowledge**: Operator acknowledges alert
5. **Resolve**: Issue fixed and alert resolved

### Custom Routing

```python
from app.monitoring.alerts import alert_manager, AlertSeverity

# Configure custom routing
alert_manager.router.set_routes(
    AlertSeverity.CRITICAL,
    channels=['email', 'sms', 'pagerduty', 'slack']
)

alert_manager.router.set_routes(
    AlertSeverity.WARNING,
    channels=['email', 'slack']
)
```

### Escalation Policy

```python
escalation_policy = alert_manager.escalation_policy

escalation_policy.define_policy(
    alert_name='Database Connection Failed',
    escalation_steps=[
        {
            'level': 0,
            'after_minutes': 0,
            'action': 'notify_ops'
        },
        {
            'level': 1,
            'after_minutes': 5,
            'action': 'notify_manager'
        },
        {
            'level': 2,
            'after_minutes': 15,
            'action': 'notify_director'
        }
    ]
)
```

---

## Health Checks

### Running Health Checks

```python
from app.monitoring.health_checks import health_check_coordinator

# Run all health checks
result = await health_check_coordinator.run_all_checks()

# Check overall status
if result.is_healthy:
    print("System is healthy")
else:
    print(f"System status: {result.overall_status}")

# Check individual components
for check in result.results:
    print(f"{check.name}: {check.status} ({check.response_time_ms}ms)")
```

### Registering Custom Checks

```python
# Register custom health check
async def check_scheduler_health():
    # Your custom health check logic
    return HealthCheckResult(
        name='scheduler',
        status=HealthStatus.HEALTHY,
        response_time_ms=10.5,
        details={'last_generation': '2025-12-31T12:30:00Z'}
    )

health_check_coordinator.register_check('scheduler', check_scheduler_health)
```

---

## Troubleshooting

### Common Issues

#### High Memory Usage

**Symptoms:** Memory usage gauge shows > 85%

**Investigation:**
```sql
-- Check top processes
SELECT name, memory_usage_bytes
FROM cache_size_bytes
ORDER BY memory_usage_bytes DESC LIMIT 10

-- Check Redis memory
SELECT redis_memory_usage_bytes
```

**Resolution:**
1. Identify cache with high memory usage
2. Adjust cache eviction policy
3. Increase cache ttl or size limit
4. Scale horizontally if needed

#### Slow Database Queries

**Symptoms:** `db_query_latency_seconds` > 100ms

**Investigation:**
```python
performance_logger.log_query_performance(
    query='EXPLAIN SELECT ...',
    duration_ms=elapsed,
    rows_affected=count
)
```

**Resolution:**
1. Check query execution plan
2. Add missing indexes
3. Optimize query logic
4. Increase database resources

#### High Error Rate

**Symptoms:** `error_rate` > 5%

**Investigation:**
```sql
-- Top error types
SELECT error_type, COUNT(*) as count
FROM error_total
GROUP BY error_type
ORDER BY count DESC

-- Errors by endpoint
SELECT endpoint, COUNT(*) as count
FROM error_total
GROUP BY endpoint
```

**Resolution:**
1. Identify error type and endpoint
2. Check recent deployments
3. Review error logs for stack traces
4. Rollback if necessary

#### Compliance Violations

**Symptoms:** `compliance_violation_total` increases

**Investigation:**
```sql
-- Which residents violating rules?
SELECT person_id, violation_type, count
FROM compliance_violation_total
ORDER BY violation_type, count DESC

-- Average work hours vs limit
SELECT person_id, average_work_hours, MAX_HOURS_LIMIT
FROM average_work_hours
WHERE average_work_hours > MAX_HOURS_LIMIT
```

**Resolution:**
1. Identify affected residents
2. Adjust schedule to resolve violations
3. Regenerate schedule if needed
4. Document any exceptions

#### Cascade Failure Risk

**Symptoms:** `cascade_failure_risk` > 50%, `defense_layer_status` increases

**Investigation:**
```python
from app.monitoring.metrics import (
    cascade_failure_risk,
    n_minus_one_contingency_count,
    utilization_rate,
)

# Check contributing factors
print(f"Cascade risk: {cascade_failure_risk._value}")
print(f"N-1 plans: {n_minus_one_contingency_count._value}")
print(f"Utilization: {utilization_rate._value}")
```

**Resolution:**
1. Reduce system utilization (< 80%)
2. Add N-1/N-2 contingency plans
3. Scale system resources
4. Implement circuit breakers

---

## Best Practices

### Metrics

1. **Use appropriate metric types** - Counter for cumulative, gauge for point-in-time
2. **Add meaningful labels** - Include method, endpoint, status for better filtering
3. **Set reasonable retention** - Balance detail and storage
4. **Test in staging** - Verify metric collection before production
5. **Monitor the monitors** - Watch metrics scrape success rate

### Logging

1. **Use structured logging** - JSON format for machine parsing
2. **Add correlation IDs** - Trace requests across systems
3. **Redact sensitive data** - Never log passwords, tokens, PII
4. **Use appropriate log levels** - DEBUG for details, ERROR for issues
5. **Set retention policies** - Don't keep logs forever

### Tracing

1. **Sample appropriately** - 100% in staging, configurable in production
2. **Add context early** - Include user, request ID, operation
3. **Monitor trace quality** - Check for orphaned spans
4. **Set reasonable limits** - Batch size, export intervals
5. **Test with realistic load** - Ensure sampling handles peak traffic

### Alerting

1. **Alert on symptoms, not causes** - Alert on error rate, not individual errors
2. **Set realistic thresholds** - Avoid alert fatigue
3. **Include runbooks** - Provide remediation steps
4. **Test alerts regularly** - Verify routing and escalation
5. **Review and tune** - Adjust thresholds based on false positive rate

### Health Checks

1. **Check dependencies first** - Database, cache before application logic
2. **Set reasonable timeouts** - Don't hang on failed checks
3. **Report partial failures** - DEGRADED status for non-critical issues
4. **Monitor check performance** - Health checks shouldn't cause slowdowns
5. **Implement circuit breakers** - Stop repeated checks of known failures

---

## Related Documentation

- **Metrics Implementation**: `backend/app/monitoring/metrics.py`
- **Logging Implementation**: `backend/app/monitoring/logging_config.py`
- **Alerting Implementation**: `backend/app/monitoring/alerts.py`
- **Health Checks**: `backend/app/monitoring/health_checks.py`
- **Tracing Implementation**: `backend/app/monitoring/tracing.py`
- **Dashboard Specifications**: `docs/monitoring/DASHBOARD_SPECS.md`

---

*This observability guide is a living document. Update when adding new metrics, logging categories, or observability features.*
