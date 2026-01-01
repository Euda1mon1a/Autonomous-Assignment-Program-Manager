# Metrics API

The Metrics API provides endpoints for Prometheus-compatible metrics collection, health monitoring, and system observability. Metrics are used for performance monitoring, alerting, capacity planning, and debugging.

## Base URL

```
/metrics
```

## Endpoints Overview

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/metrics/health` | GET | Metrics system health check |
| `/metrics/info` | GET | Documentation of available metrics |
| `/metrics/export` | GET | Export metrics (Prometheus format) |
| `/metrics/summary` | GET | High-level metrics summary |
| `/metrics/reset` | POST | Reset metrics (debug mode only) |

**Note:** The main `/metrics` endpoint (not under `/api/v1`) is served directly by Prometheus middleware for scraping. Use `/metrics/export` for the same data via the API router.

---

## Metrics Health Check

**Purpose:** Check if metrics collection is enabled and functioning.

```http
GET /metrics/health
```

### Response

**Status:** 200 OK

```json
{
  "status": "healthy",
  "metrics_enabled": true,
  "collectors": [
    "http",
    "database",
    "cache",
    "background_tasks",
    "schedule",
    "acgme_compliance",
    "errors",
    "system_resources"
  ],
  "prometheus_available": true,
  "message": "Metrics collection operational"
}
```

### Response (Degraded)

```json
{
  "status": "degraded",
  "metrics_enabled": false,
  "collectors": [],
  "prometheus_available": false,
  "message": "Metrics disabled - prometheus_client not available"
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | "healthy" or "degraded" |
| `metrics_enabled` | boolean | Whether metrics collection is active |
| `collectors` | string[] | List of active metric collectors |
| `prometheus_available` | boolean | Whether prometheus_client library is available |
| `message` | string | Status message |

### Notes
- Returns "degraded" if prometheus_client is not installed
- Use this endpoint to verify metrics are being collected
- Does not check individual metric values

---

## Metrics Information

**Purpose:** Get documentation of all available metrics and their descriptions.

```http
GET /metrics/info
```

### Response

**Status:** 200 OK

```json
{
  "metrics": {
    "http": {
      "http_requests_total": {
        "type": "counter",
        "description": "Total HTTP requests by method, endpoint, and status code",
        "labels": ["method", "endpoint", "status_code"]
      },
      "http_request_duration_seconds": {
        "type": "histogram",
        "description": "HTTP request latency by method and endpoint",
        "labels": ["method", "endpoint"]
      },
      "http_requests_in_progress": {
        "type": "gauge",
        "description": "Number of HTTP requests currently being processed",
        "labels": ["method", "endpoint"]
      },
      "http_active_connections": {
        "type": "gauge",
        "description": "Number of active HTTP connections",
        "labels": []
      },
      "http_request_size_bytes": {
        "type": "summary",
        "description": "HTTP request size in bytes",
        "labels": ["method", "endpoint"]
      },
      "http_response_size_bytes": {
        "type": "summary",
        "description": "HTTP response size in bytes",
        "labels": ["method", "endpoint"]
      }
    },
    "database": {
      "db_queries_total": {
        "type": "counter",
        "description": "Total database queries by operation type",
        "labels": ["operation"]
      },
      "db_query_duration_seconds": {
        "type": "histogram",
        "description": "Database query execution time by operation",
        "labels": ["operation"]
      },
      "db_connections_active": {
        "type": "gauge",
        "description": "Number of active database connections",
        "labels": []
      },
      "db_connection_pool_size": {
        "type": "gauge",
        "description": "Database connection pool size",
        "labels": []
      }
    },
    "cache": {
      "cache_operations_total": {
        "type": "counter",
        "description": "Total cache operations by type and result",
        "labels": ["operation", "result"]
      },
      "cache_hit_ratio": {
        "type": "gauge",
        "description": "Cache hit ratio (hits / total_requests)",
        "labels": ["cache_name"]
      },
      "cache_operation_duration_seconds": {
        "type": "histogram",
        "description": "Cache operation duration by operation type",
        "labels": ["operation"]
      }
    },
    "background_tasks": {
      "background_tasks_total": {
        "type": "counter",
        "description": "Total background tasks by name and status",
        "labels": ["task_name", "status"]
      },
      "background_task_duration_seconds": {
        "type": "histogram",
        "description": "Background task execution time by task name",
        "labels": ["task_name"]
      },
      "background_tasks_in_progress": {
        "type": "gauge",
        "description": "Number of background tasks currently executing",
        "labels": ["task_name"]
      },
      "background_task_queue_depth": {
        "type": "gauge",
        "description": "Number of tasks waiting in queue",
        "labels": ["queue_name"]
      }
    },
    "schedule": {
      "schedule_generation_total": {
        "type": "counter",
        "description": "Total schedule generation attempts by algorithm and outcome",
        "labels": ["algorithm", "outcome"]
      },
      "schedule_generation_duration_seconds": {
        "type": "histogram",
        "description": "Schedule generation time by algorithm",
        "labels": ["algorithm"]
      },
      "schedule_optimization_score": {
        "type": "gauge",
        "description": "Current schedule optimization score",
        "labels": ["algorithm"]
      }
    },
    "acgme_compliance": {
      "acgme_violations_total": {
        "type": "counter",
        "description": "Total ACGME violations detected by type",
        "labels": ["violation_type"]
      },
      "acgme_compliance_score": {
        "type": "gauge",
        "description": "ACGME compliance score (0.0-1.0)",
        "labels": ["rule"]
      },
      "acgme_validation_duration_seconds": {
        "type": "histogram",
        "description": "Time to validate ACGME compliance",
        "labels": []
      }
    },
    "errors": {
      "errors_total": {
        "type": "counter",
        "description": "Total errors by type, severity, and endpoint",
        "labels": ["error_type", "severity", "endpoint"]
      },
      "exceptions_unhandled_total": {
        "type": "counter",
        "description": "Total unhandled exceptions by type",
        "labels": ["exception_type"]
      }
    },
    "system": {
      "system_cpu_usage_percent": {
        "type": "gauge",
        "description": "Current CPU usage percentage",
        "labels": []
      },
      "system_memory_usage_bytes": {
        "type": "gauge",
        "description": "Current memory usage in bytes",
        "labels": ["type"]
      },
      "system_disk_usage_percent": {
        "type": "gauge",
        "description": "Disk usage percentage",
        "labels": ["mount_point"]
      }
    }
  },
  "total_metrics": 28,
  "categories": [
    "http",
    "database",
    "cache",
    "background_tasks",
    "schedule",
    "acgme_compliance",
    "errors",
    "system"
  ]
}
```

### Metric Types

| Type | Description | Example Use Case |
|------|-------------|------------------|
| **counter** | Monotonically increasing value | Total requests, total errors |
| **gauge** | Value that can go up or down | Active connections, CPU usage |
| **histogram** | Samples observations in buckets | Request duration, response time |
| **summary** | Similar to histogram with quantiles | Request/response size |

### Metric Categories

| Category | Purpose | Key Metrics |
|----------|---------|-------------|
| **http** | HTTP request/response tracking | Request count, latency, active connections |
| **database** | Database query performance | Query count, duration, connection pool |
| **cache** | Cache performance | Hit ratio, cache operations |
| **background_tasks** | Celery task monitoring | Task count, duration, queue depth |
| **schedule** | Schedule generation metrics | Generation time, optimization score |
| **acgme_compliance** | ACGME validation metrics | Violations, compliance score |
| **errors** | Error tracking | Error count by type and severity |
| **system** | System resource usage | CPU, memory, disk usage |

### Notes
- Use this endpoint to discover available metrics for Grafana dashboards
- Label combinations create unique time series
- Histogram buckets are predefined (not shown in this endpoint)

---

## Export Metrics

**Purpose:** Export all metrics in Prometheus text format for scraping.

```http
GET /metrics/export
```

### Response

**Content-Type:** `text/plain; version=0.0.4; charset=utf-8`

```
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",endpoint="/api/v1/schedule",status_code="200"} 42.0
http_requests_total{method="POST",endpoint="/api/v1/assignments",status_code="201"} 15.0
http_requests_total{method="GET",endpoint="/api/v1/health/ready",status_code="200"} 1250.0

# HELP http_request_duration_seconds HTTP request latency
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{method="GET",endpoint="/api/v1/schedule",le="0.005"} 5.0
http_request_duration_seconds_bucket{method="GET",endpoint="/api/v1/schedule",le="0.01"} 10.0
http_request_duration_seconds_bucket{method="GET",endpoint="/api/v1/schedule",le="0.025"} 15.0
http_request_duration_seconds_bucket{method="GET",endpoint="/api/v1/schedule",le="+Inf"} 42.0
http_request_duration_seconds_sum{method="GET",endpoint="/api/v1/schedule"} 1.25
http_request_duration_seconds_count{method="GET",endpoint="/api/v1/schedule"} 42.0

# HELP db_connections_active Number of active database connections
# TYPE db_connections_active gauge
db_connections_active 3.0

# HELP background_tasks_in_progress Background tasks executing
# TYPE background_tasks_in_progress gauge
background_tasks_in_progress{task_name="resilience_health_check"} 0.0
background_tasks_in_progress{task_name="n_minus_1_analysis"} 1.0

# ... (all other metrics)
```

### Prometheus Format Details

Each metric includes:
- **HELP:** Human-readable description
- **TYPE:** Metric type (counter, gauge, histogram, summary)
- **Values:** Metric name, labels (in curly braces), and value

### Error Response (503)

```json
{
  "detail": "Metrics export unavailable - prometheus_client not installed"
}
```

### Notes
- This endpoint duplicates the main `/metrics` endpoint functionality
- Use `/metrics` directly for Prometheus scraping (more efficient)
- Use `/metrics/export` for API consistency or testing
- Response format follows Prometheus text exposition format

---

## Metrics Summary

**Purpose:** Get high-level summary of current metric values.

```http
GET /metrics/summary
```

### Response (Enabled)

**Status:** 200 OK

```json
{
  "status": "enabled",
  "timestamp": null,
  "http": {
    "active_connections": "See /metrics endpoint",
    "requests_in_progress": "See /metrics endpoint"
  },
  "database": {
    "active_connections": "See /metrics endpoint",
    "pool_size": "See /metrics endpoint"
  },
  "cache": {
    "hit_ratio": "See /metrics endpoint"
  },
  "background_tasks": {
    "tasks_in_progress": "See /metrics endpoint",
    "queue_depth": "See /metrics endpoint"
  },
  "message": "For detailed metrics, query the /metrics endpoint directly"
}
```

### Response (Disabled)

```json
{
  "status": "disabled",
  "message": "Metrics collection is disabled"
}
```

### Notes
- This is a placeholder endpoint - extracting current values from Prometheus metrics is complex
- For detailed metric values, use `/metrics/export` or Prometheus queries
- Consider this a "metrics availability" check rather than a data endpoint

---

## Reset Metrics

**Purpose:** Reset all metric counters (development/testing only).

```http
POST /metrics/reset
```

**Authentication:** Debug mode required

### Response (Debug Mode)

**Status:** 200 OK

```json
{
  "status": "warning",
  "message": "Prometheus metrics cannot be reset without restarting the application",
  "recommendation": "Restart the application to reset metrics"
}
```

### Response (Production)

**Status:** 403 Forbidden

```json
{
  "detail": "Metrics reset is only available in debug mode"
}
```

### Notes
- Prometheus metrics cannot be reset without recreating the registry
- Only available when `DEBUG=true` in settings
- **Not recommended for production use**
- Restart the application to truly reset metrics

---

## Prometheus Integration

### Configuration

Add Prometheus scrape config:

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'residency-scheduler'
    scrape_interval: 15s
    scrape_timeout: 10s
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'
```

### Scraping Behavior

- **Interval:** Every 15 seconds (recommended)
- **Timeout:** 10 seconds
- **Endpoint:** `/metrics` (not `/api/v1/metrics/export`)
- **Format:** Prometheus text format

### Common Prometheus Queries

#### Request Rate
```promql
rate(http_requests_total[5m])
```

#### Request Latency (p95)
```promql
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

#### Error Rate
```promql
rate(errors_total[5m])
```

#### Database Connection Pool Usage
```promql
db_connections_active / db_connection_pool_size * 100
```

#### Cache Hit Ratio
```promql
cache_hit_ratio
```

#### ACGME Compliance Score
```promql
acgme_compliance_score
```

---

## Grafana Dashboard Examples

### HTTP Performance Panel

**Query:**
```promql
rate(http_requests_total{status_code=~"2.."}[5m])
```

**Visualization:** Graph
**Title:** Successful Requests per Second

---

### Database Query Duration

**Query:**
```promql
histogram_quantile(0.95, rate(db_query_duration_seconds_bucket[5m]))
```

**Visualization:** Graph
**Title:** Database Query Duration (p95)

---

### Background Task Queue Depth

**Query:**
```promql
background_task_queue_depth
```

**Visualization:** Stat
**Title:** Celery Queue Depth

---

### ACGME Violations

**Query:**
```promql
increase(acgme_violations_total[24h])
```

**Visualization:** Bar gauge
**Title:** ACGME Violations (Last 24 Hours)

---

### System Resource Usage

**Queries:**
```promql
system_cpu_usage_percent
system_memory_usage_bytes{type="used"} / 1024 / 1024 / 1024
system_disk_usage_percent{mount_point="/"}
```

**Visualization:** Gauge
**Title:** System Resources

---

## Alerting Rules

### High Error Rate

```yaml
groups:
  - name: errors
    rules:
      - alert: HighErrorRate
        expr: rate(errors_total[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors/sec"
```

### Database Connection Pool Exhausted

```yaml
- alert: DatabaseConnectionPoolExhausted
  expr: db_connections_active / db_connection_pool_size > 0.9
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "Database connection pool near capacity"
    description: "{{ $value | humanizePercentage }} of connections in use"
```

### Long-Running Schedule Generation

```yaml
- alert: ScheduleGenerationSlow
  expr: histogram_quantile(0.95, rate(schedule_generation_duration_seconds_bucket[5m])) > 300
  for: 10m
  labels:
    severity: warning
  annotations:
    summary: "Schedule generation taking too long"
    description: "p95 generation time is {{ $value }} seconds"
```

### ACGME Compliance Degradation

```yaml
- alert: ACGMEComplianceLow
  expr: acgme_compliance_score < 0.95
  for: 15m
  labels:
    severity: critical
  annotations:
    summary: "ACGME compliance score below threshold"
    description: "Compliance score is {{ $value | humanizePercentage }}"
```

---

## Metric Collection Best Practices

### Instrumentation

Use the metrics instance in your code:

```python
from app.core.metrics import get_metrics

metrics = get_metrics()

# Increment a counter
metrics.increment_counter("http_requests_total", {
    "method": "GET",
    "endpoint": "/api/v1/schedule",
    "status_code": "200"
})

# Record a histogram value
metrics.observe_histogram("http_request_duration_seconds", 0.045, {
    "method": "GET",
    "endpoint": "/api/v1/schedule"
})

# Set a gauge value
metrics.set_gauge("db_connections_active", 5)
```

### Label Cardinality

**Good (low cardinality):**
```python
labels = {"method": "GET", "status_code": "200"}  # ~10 unique combinations
```

**Bad (high cardinality):**
```python
labels = {"user_id": "uuid", "timestamp": "2024-01-15T10:30:00"}  # Millions of combinations
```

**Rule:** Keep label combinations under 1000 per metric

### Naming Conventions

Follow Prometheus naming conventions:
- Use snake_case: `http_requests_total`
- Append unit suffix: `_seconds`, `_bytes`, `_total`
- Use descriptive names: `acgme_compliance_score`, not `score`

---

## Performance Considerations

### Scraping Overhead

- **Scrape interval:** 15s is standard (don't go below 5s)
- **Metrics count:** ~28 base metrics × label combinations
- **Overhead:** < 1ms per scrape for typical cardinality

### Storage

Prometheus storage requirements:
```
~1-2 bytes per sample
15-day retention: ~86,400 samples per metric
High-cardinality metrics can use significant disk space
```

### Query Performance

- Use `rate()` for counters, not raw values
- Limit time ranges for heavy queries (< 24 hours for dashboards)
- Use recording rules for expensive queries

---

## Troubleshooting

### Metrics Not Appearing

1. Check metrics are enabled:
   ```bash
   GET /metrics/health
   ```

2. Verify prometheus_client is installed:
   ```bash
   pip list | grep prometheus
   ```

3. Check Prometheus scrape status:
   ```
   http://prometheus:9090/targets
   ```

### High Cardinality Warning

If metrics storage grows too large:
1. Identify high-cardinality metrics in Prometheus UI
2. Review label usage - remove unnecessary labels
3. Consider dropping metrics with `drop` relabeling

### Stale Metrics

Prometheus marks metrics stale after 5 minutes of no updates. To keep metrics active:
- Use gauges for infrequently-updated values
- Periodically update critical gauges (e.g., in background tasks)

---

## Related Documentation

- `backend/app/api/routes/metrics.py` - Implementation
- `backend/app/core/metrics.py` - Metrics collection system
- `backend/app/middleware/metrics_middleware.py` - HTTP metrics middleware
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
