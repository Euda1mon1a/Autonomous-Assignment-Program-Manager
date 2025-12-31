# Observability Setup Guide

Complete guide to setting up monitoring, metrics, tracing, and alerting for the Residency Scheduler application.

## Overview

The observability stack consists of:
- **Metrics**: Prometheus + Grafana
- **Logging**: Structured JSON logs + aggregation
- **Tracing**: OpenTelemetry + Jaeger/OTLP
- **Alerting**: Prometheus Alertmanager + PagerDuty/Slack

## Architecture

```
Application
    ├── Metrics → Prometheus → Grafana
    ├── Logs → JSON files → Log aggregation
    ├── Traces → OpenTelemetry → Jaeger/OTLP
    └── Alerts → Alertmanager → PagerDuty/Slack/Email
```

## Setup: Metrics (Prometheus + Grafana)

### 1. Prometheus Configuration

Create `prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'residency-scheduler'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'
```

### 2. Start Prometheus

```bash
docker run -d \
  --name prometheus \
  -p 9090:9090 \
  -v $(pwd)/prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus
```

### 3. Grafana Setup

```bash
# Start Grafana
docker run -d \
  --name grafana \
  -p 3000:3000 \
  grafana/grafana

# Access Grafana at http://localhost:3000 (admin/admin)
```

### 4. Import Dashboards

```python
from app.core.metrics.dashboards import create_dashboards_in_grafana

await create_dashboards_in_grafana(
    grafana_url="http://localhost:3000",
    api_key="your-api-key"
)
```

Pre-built dashboards:
- Overview: System health and performance
- Compliance: ACGME violations and overrides
- Security: Authentication and security events

### 5. Configure Metrics Export

```python
from app.core.metrics.exporters import create_prometheus_exporter

exporter = create_prometheus_exporter(
    push_gateway_url="localhost:9091",
    job_name="residency-scheduler",
    export_interval=60
)

await exporter.start()
```

## Setup: Distributed Tracing

### 1. OpenTelemetry Configuration

```python
from app.tracing import TracingConfig, setup_tracing

config = TracingConfig(
    service_name="residency-scheduler",
    service_version="1.0.0",
    environment="production",
    jaeger_endpoint="localhost:6831",  # or
    otlp_endpoint="http://localhost:4317",
    sample_rate=1.0  # 100% sampling (adjust in production)
)

setup_tracing(config, app)
```

### 2. Jaeger Setup

```bash
# Start Jaeger all-in-one
docker run -d \
  --name jaeger \
  -p 6831:6831/udp \
  -p 16686:16686 \
  jaegertracing/all-in-one:latest

# Access Jaeger UI at http://localhost:16686
```

### 3. OTLP Collector (Alternative)

```bash
# Start OTLP collector
docker run -d \
  --name otel-collector \
  -p 4317:4317 \
  -p 4318:4318 \
  otel/opentelemetry-collector:latest
```

### 4. Custom Spans

```python
from app.tracing import trace_function, add_span_attributes

@trace_function("schedule_generation")
async def generate_schedule():
    add_span_attributes(
        user_id=user.id,
        resident_count=len(residents)
    )
    # ... implementation
```

## Setup: Alerting

### 1. Configure Alert Rules

```python
from app.core.metrics.alerts import get_all_alert_rules, export_prometheus_rules

# Export alert rules
export_prometheus_rules("alerts.yml")
```

### 2. Alertmanager Configuration

Create `alertmanager.yml`:

```yaml
global:
  resolve_timeout: 5m

route:
  group_by: ['alertname', 'severity']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'default'
  routes:
    - match:
        severity: critical
      receiver: 'pagerduty'
    - match:
        severity: warning
      receiver: 'slack'

receivers:
  - name: 'default'
    email_configs:
      - to: 'alerts@example.com'

  - name: 'pagerduty'
    pagerduty_configs:
      - service_key: 'your-pagerduty-key'

  - name: 'slack'
    slack_configs:
      - api_url: 'your-slack-webhook'
        channel: '#alerts'
```

### 3. Start Alertmanager

```bash
docker run -d \
  --name alertmanager \
  -p 9093:9093 \
  -v $(pwd)/alertmanager.yml:/etc/alertmanager/alertmanager.yml \
  prom/alertmanager
```

## Setup: Log Aggregation

### Option 1: ELK Stack

```bash
# Elasticsearch
docker run -d \
  --name elasticsearch \
  -p 9200:9200 \
  -e "discovery.type=single-node" \
  elasticsearch:7.17.0

# Logstash
docker run -d \
  --name logstash \
  -p 5000:5000 \
  -v $(pwd)/logstash.conf:/usr/share/logstash/pipeline/logstash.conf \
  logstash:7.17.0

# Kibana
docker run -d \
  --name kibana \
  -p 5601:5601 \
  kibana:7.17.0
```

### Option 2: Loki + Grafana

```bash
# Loki
docker run -d \
  --name loki \
  -p 3100:3100 \
  grafana/loki:latest

# Promtail (log shipper)
docker run -d \
  --name promtail \
  -v /var/log:/var/log \
  -v $(pwd)/promtail-config.yml:/etc/promtail/config.yml \
  grafana/promtail:latest
```

## Monitoring Checklist

### System Metrics

- [x] CPU usage
- [x] Memory usage
- [x] Disk I/O
- [x] Network I/O
- [x] Process metrics

### Application Metrics

- [x] Request rate
- [x] Response time (p50, p95, p99)
- [x] Error rate
- [x] Active users
- [x] Database connections
- [x] Cache hit rate

### Business Metrics

- [x] ACGME violations
- [x] Schedule generation time
- [x] Swap requests
- [x] User activity
- [x] Compliance score

### Security Metrics

- [x] Failed authentication attempts
- [x] Rate limit violations
- [x] Suspicious activity
- [x] Data access events

## Performance Tuning

### Metric Collection

```python
# Adjust collection frequency
from app.core.metrics.exporters import MetricExportConfig

config = MetricExportConfig(
    export_interval_seconds=60,  # Every minute
    batch_size=100,
    retry_attempts=3
)
```

### Log Volume Management

```bash
# Rotate logs
LOG_MAX_FILE_SIZE=100  # MB
LOG_BACKUP_COUNT=7

# Adjust log levels
LOG_LEVEL=INFO  # DEBUG in dev, INFO in prod
```

### Trace Sampling

```python
# Reduce sampling in high-traffic environments
config = TracingConfig(
    sample_rate=0.1  # 10% sampling
)
```

## Dashboards

### Overview Dashboard

Metrics displayed:
- Request rate (requests/sec)
- Response time p95
- Error rate
- Active users
- Database connections
- Cache hit rate

### Compliance Dashboard

Metrics displayed:
- ACGME violations (24h)
- Violations by type
- Schedule overrides
- Compliance score

### Security Dashboard

Metrics displayed:
- Failed auth attempts
- Rate limit violations
- Suspicious activity events

## Troubleshooting

### Metrics Not Showing

1. Check Prometheus scrape targets: http://localhost:9090/targets
2. Verify metrics endpoint: http://localhost:8000/metrics
3. Check firewall rules
4. Review Prometheus logs

### Traces Not Appearing

1. Verify OpenTelemetry configuration
2. Check Jaeger/OTLP endpoint connectivity
3. Review trace sampling rate
4. Check service name configuration

### Alerts Not Firing

1. Verify Alertmanager is running
2. Check alert rule syntax in Prometheus
3. Review alert evaluation interval
4. Test notification channels

## See Also

- [Logging Guide](logging-guide.md)
- [Alert Runbook](alert-runbook.md)
- [CLAUDE.md - Monitoring Section](../../CLAUDE.md)
