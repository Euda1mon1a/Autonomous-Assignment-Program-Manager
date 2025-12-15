# Monitoring and Observability Stack

Comprehensive monitoring, logging, and alerting infrastructure for the Residency Scheduler application.

## Overview

This monitoring stack provides:
- **Metrics Collection**: Prometheus for time-series metrics
- **Visualization**: Grafana dashboards for system and application metrics
- **Log Aggregation**: Loki + Promtail for centralized logging
- **Alerting**: Alertmanager for alert routing and notifications
- **Infrastructure Metrics**: Node Exporter, cAdvisor, PostgreSQL Exporter

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Monitoring Stack                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐              │
│   │   Backend   │────▶│  Prometheus │────▶│  Grafana    │              │
│   │   FastAPI   │     │   :9090     │     │   :3001     │              │
│   └─────────────┘     └──────┬──────┘     └─────────────┘              │
│                              │                                          │
│   ┌─────────────┐            ▼                                          │
│   │  PostgreSQL │     ┌─────────────┐                                   │
│   │   :5432     │────▶│Alertmanager │────▶ Email/Slack/PagerDuty       │
│   └─────────────┘     │   :9093     │                                   │
│                       └─────────────┘                                   │
│                                                                          │
│   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐              │
│   │  Containers │────▶│  Promtail   │────▶│    Loki     │              │
│   │   (logs)    │     │   :9080     │     │   :3100     │              │
│   └─────────────┘     └─────────────┘     └─────────────┘              │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Setup Environment

```bash
# Copy environment template
cp .env.example .env

# Edit with your configuration
nano .env
```

### 2. Start Monitoring Stack

```bash
# Run the setup script
./scripts/setup-monitoring.sh

# Or manually with docker-compose
docker-compose -f docker-compose.monitoring.yml up -d
```

### 3. Access Services

| Service | URL | Default Credentials |
|---------|-----|---------------------|
| Grafana | http://localhost:3001 | admin / admin |
| Prometheus | http://localhost:9090 | - |
| Alertmanager | http://localhost:9093 | - |
| Loki | http://localhost:3100 | - |

## Directory Structure

```
monitoring/
├── prometheus/
│   ├── prometheus.yml          # Main Prometheus configuration
│   └── rules/
│       ├── application.yml     # Application-specific alerts
│       └── infrastructure.yml  # Infrastructure alerts
├── alertmanager/
│   ├── alertmanager.yml        # Alert routing configuration
│   └── templates/
│       └── slack.tmpl          # Slack notification template
├── grafana/
│   ├── provisioning/
│   │   ├── datasources/        # Auto-provisioned data sources
│   │   └── dashboards/         # Dashboard provisioning config
│   └── dashboards/
│       ├── overview.json           # Overview dashboard
│       ├── application-metrics.json # API metrics dashboard
│       ├── system-metrics.json     # System metrics dashboard
│       └── database-metrics.json   # PostgreSQL dashboard
├── loki/
│   └── loki-config.yml         # Loki configuration
├── promtail/
│   └── promtail-config.yml     # Log collection configuration
├── scripts/
│   ├── setup-monitoring.sh     # Setup script
│   ├── health-check.sh         # Health verification
│   └── backup-monitoring.sh    # Data backup script
├── docker-compose.monitoring.yml
├── .env.example
└── README.md
```

## Dashboards

### Overview Dashboard
High-level view of system health including:
- Service status (Backend, PostgreSQL)
- Active alerts count
- Request rate and latency
- System resource usage

### Application Metrics
Detailed API performance metrics:
- Request rate by method and endpoint
- Response times (P50, P95, P99)
- Error rates
- Schedule generation statistics
- ACGME compliance violations

### System Metrics
Infrastructure monitoring:
- CPU usage breakdown
- Memory utilization
- Disk I/O and space
- Network traffic
- Container resource usage

### Database Metrics
PostgreSQL performance:
- Connection statistics
- Transaction rates
- Cache hit ratios
- Query performance
- Lock monitoring

## Alerting

### Alert Severities

| Severity | Response Time | Notification Channels |
|----------|--------------|----------------------|
| Critical | Immediate | PagerDuty, Slack, Email |
| Warning | 30 minutes | Slack, Email |
| Info | Best effort | Slack |

### Key Alerts

**Application Alerts:**
- `APIServiceDown` - Backend API unreachable
- `HighErrorRate` - Error rate > 5%
- `HighLatencyP95` - P95 latency > 2s
- `ACGMEComplianceViolations` - Compliance issues detected

**Infrastructure Alerts:**
- `HighCPUUsage` - CPU > 80%
- `HighMemoryUsage` - Memory > 80%
- `DiskSpaceWarning` - Disk < 20% free
- `ContainerRestarting` - Frequent container restarts

**Database Alerts:**
- `PostgreSQLDown` - Database unreachable
- `PostgreSQLHighConnections` - > 80 connections
- `PostgreSQLSlowQueries` - Long-running queries
- `PostgreSQLDeadlocks` - Deadlocks detected

## Log Aggregation

Logs are collected via Promtail and stored in Loki. Query logs in Grafana using LogQL:

```logql
# Application errors
{service="residency-scheduler-backend"} |= "ERROR"

# Slow API requests
{service="residency-scheduler-backend"} | json | request_time > 1s

# Schedule generation logs
{service="residency-scheduler-backend"} |= "schedule" |= "generation"

# PostgreSQL errors
{service="postgresql"} |= "ERROR"
```

## Maintenance

### Health Check

```bash
./scripts/health-check.sh
```

### Backup

```bash
# Manual backup
./scripts/backup-monitoring.sh

# Set up cron for daily backups
0 2 * * * /path/to/monitoring/scripts/backup-monitoring.sh
```

### Viewing Logs

```bash
# All services
docker-compose -f docker-compose.monitoring.yml logs -f

# Specific service
docker-compose -f docker-compose.monitoring.yml logs -f prometheus
```

### Reloading Configuration

```bash
# Reload Prometheus config without restart
curl -X POST http://localhost:9090/-/reload

# Reload Alertmanager config
curl -X POST http://localhost:9093/-/reload
```

## Customization

### Adding New Dashboards

1. Create dashboard JSON in `grafana/dashboards/`
2. Dashboard will be auto-provisioned on Grafana restart

### Adding New Alerts

1. Edit `prometheus/rules/*.yml`
2. Reload Prometheus: `curl -X POST http://localhost:9090/-/reload`

### Adding New Log Sources

1. Edit `promtail/promtail-config.yml`
2. Restart Promtail container

## Troubleshooting

### Prometheus Not Scraping

```bash
# Check target status
curl http://localhost:9090/api/v1/targets

# Check configuration
docker-compose -f docker-compose.monitoring.yml exec prometheus promtool check config /etc/prometheus/prometheus.yml
```

### Loki Not Receiving Logs

```bash
# Check Promtail status
docker-compose -f docker-compose.monitoring.yml logs promtail

# Verify Loki is ready
curl http://localhost:3100/ready
```

### Grafana Dashboard Issues

```bash
# Check provisioning logs
docker-compose -f docker-compose.monitoring.yml logs grafana | grep provisioning

# Verify data source connectivity
curl -u admin:admin http://localhost:3001/api/datasources
```

## Security Considerations

1. **Change default passwords** in production
2. **Restrict network access** to monitoring ports
3. **Enable TLS** for external access
4. **Use secrets management** for sensitive configuration
5. **Regular security updates** for container images

## Integration with CI/CD

The monitoring stack can be integrated with your CI/CD pipeline:

```yaml
# Example GitHub Actions step
- name: Check Monitoring Health
  run: |
    ./monitoring/scripts/health-check.sh
```
