***REMOVED*** Monitoring and Observability Stack

Comprehensive monitoring, logging, and alerting infrastructure for the Residency Scheduler application.

***REMOVED******REMOVED*** Overview

This monitoring stack provides:
- **Metrics Collection**: Prometheus for time-series metrics
- **Visualization**: Grafana dashboards for system and application metrics
- **Log Aggregation**: Loki + Promtail for centralized logging
- **Alerting**: Alertmanager for alert routing and notifications
- **Infrastructure Metrics**: Node Exporter, cAdvisor, PostgreSQL Exporter

***REMOVED******REMOVED*** Architecture

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

***REMOVED******REMOVED*** Quick Start

***REMOVED******REMOVED******REMOVED*** 1. Setup Environment

```bash
***REMOVED*** Copy environment template
cp .env.example .env

***REMOVED*** Edit with your configuration
nano .env
```

***REMOVED******REMOVED******REMOVED*** 2. Start Monitoring Stack

```bash
***REMOVED*** Run the setup script
./scripts/setup-monitoring.sh

***REMOVED*** Or manually with docker-compose
docker-compose -f docker-compose.monitoring.yml up -d
```

***REMOVED******REMOVED******REMOVED*** 3. Access Services

| Service | URL | Default Credentials |
|---------|-----|---------------------|
| Grafana | http://localhost:3001 | admin / admin |
| Prometheus | http://localhost:9090 | - |
| Alertmanager | http://localhost:9093 | - |
| Loki | http://localhost:3100 | - |

***REMOVED******REMOVED*** Directory Structure

```
monitoring/
├── prometheus/
│   ├── prometheus.yml          ***REMOVED*** Main Prometheus configuration
│   └── rules/
│       ├── application.yml     ***REMOVED*** Application-specific alerts
│       └── infrastructure.yml  ***REMOVED*** Infrastructure alerts
├── alertmanager/
│   ├── alertmanager.yml        ***REMOVED*** Alert routing configuration
│   └── templates/
│       └── slack.tmpl          ***REMOVED*** Slack notification template
├── grafana/
│   ├── provisioning/
│   │   ├── datasources/        ***REMOVED*** Auto-provisioned data sources
│   │   └── dashboards/         ***REMOVED*** Dashboard provisioning config
│   └── dashboards/
│       ├── overview.json           ***REMOVED*** Overview dashboard
│       ├── application-metrics.json ***REMOVED*** API metrics dashboard
│       ├── system-metrics.json     ***REMOVED*** System metrics dashboard
│       └── database-metrics.json   ***REMOVED*** PostgreSQL dashboard
├── loki/
│   └── loki-config.yml         ***REMOVED*** Loki configuration
├── promtail/
│   └── promtail-config.yml     ***REMOVED*** Log collection configuration
├── scripts/
│   ├── setup-monitoring.sh     ***REMOVED*** Setup script
│   ├── health-check.sh         ***REMOVED*** Health verification
│   └── backup-monitoring.sh    ***REMOVED*** Data backup script
├── docker-compose.monitoring.yml
├── .env.example
└── README.md
```

***REMOVED******REMOVED*** Dashboards

***REMOVED******REMOVED******REMOVED*** Overview Dashboard
High-level view of system health including:
- Service status (Backend, PostgreSQL)
- Active alerts count
- Request rate and latency
- System resource usage

***REMOVED******REMOVED******REMOVED*** Application Metrics
Detailed API performance metrics:
- Request rate by method and endpoint
- Response times (P50, P95, P99)
- Error rates
- Schedule generation statistics
- ACGME compliance violations

***REMOVED******REMOVED******REMOVED*** System Metrics
Infrastructure monitoring:
- CPU usage breakdown
- Memory utilization
- Disk I/O and space
- Network traffic
- Container resource usage

***REMOVED******REMOVED******REMOVED*** Database Metrics
PostgreSQL performance:
- Connection statistics
- Transaction rates
- Cache hit ratios
- Query performance
- Lock monitoring

***REMOVED******REMOVED*** Alerting

***REMOVED******REMOVED******REMOVED*** Alert Severities

| Severity | Response Time | Notification Channels |
|----------|--------------|----------------------|
| Critical | Immediate | PagerDuty, Slack, Email |
| Warning | 30 minutes | Slack, Email |
| Info | Best effort | Slack |

***REMOVED******REMOVED******REMOVED*** Key Alerts

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

***REMOVED******REMOVED*** Log Aggregation

Logs are collected via Promtail and stored in Loki. Query logs in Grafana using LogQL:

```logql
***REMOVED*** Application errors
{service="residency-scheduler-backend"} |= "ERROR"

***REMOVED*** Slow API requests
{service="residency-scheduler-backend"} | json | request_time > 1s

***REMOVED*** Schedule generation logs
{service="residency-scheduler-backend"} |= "schedule" |= "generation"

***REMOVED*** PostgreSQL errors
{service="postgresql"} |= "ERROR"
```

***REMOVED******REMOVED*** Maintenance

***REMOVED******REMOVED******REMOVED*** Health Check

```bash
./scripts/health-check.sh
```

***REMOVED******REMOVED******REMOVED*** Backup

```bash
***REMOVED*** Manual backup
./scripts/backup-monitoring.sh

***REMOVED*** Set up cron for daily backups
0 2 * * * /path/to/monitoring/scripts/backup-monitoring.sh
```

***REMOVED******REMOVED******REMOVED*** Viewing Logs

```bash
***REMOVED*** All services
docker-compose -f docker-compose.monitoring.yml logs -f

***REMOVED*** Specific service
docker-compose -f docker-compose.monitoring.yml logs -f prometheus
```

***REMOVED******REMOVED******REMOVED*** Reloading Configuration

```bash
***REMOVED*** Reload Prometheus config without restart
curl -X POST http://localhost:9090/-/reload

***REMOVED*** Reload Alertmanager config
curl -X POST http://localhost:9093/-/reload
```

***REMOVED******REMOVED*** Customization

***REMOVED******REMOVED******REMOVED*** Adding New Dashboards

1. Create dashboard JSON in `grafana/dashboards/`
2. Dashboard will be auto-provisioned on Grafana restart

***REMOVED******REMOVED******REMOVED*** Adding New Alerts

1. Edit `prometheus/rules/*.yml`
2. Reload Prometheus: `curl -X POST http://localhost:9090/-/reload`

***REMOVED******REMOVED******REMOVED*** Adding New Log Sources

1. Edit `promtail/promtail-config.yml`
2. Restart Promtail container

***REMOVED******REMOVED*** Troubleshooting

***REMOVED******REMOVED******REMOVED*** Prometheus Not Scraping

```bash
***REMOVED*** Check target status
curl http://localhost:9090/api/v1/targets

***REMOVED*** Check configuration
docker-compose -f docker-compose.monitoring.yml exec prometheus promtool check config /etc/prometheus/prometheus.yml
```

***REMOVED******REMOVED******REMOVED*** Loki Not Receiving Logs

```bash
***REMOVED*** Check Promtail status
docker-compose -f docker-compose.monitoring.yml logs promtail

***REMOVED*** Verify Loki is ready
curl http://localhost:3100/ready
```

***REMOVED******REMOVED******REMOVED*** Grafana Dashboard Issues

```bash
***REMOVED*** Check provisioning logs
docker-compose -f docker-compose.monitoring.yml logs grafana | grep provisioning

***REMOVED*** Verify data source connectivity
curl -u admin:admin http://localhost:3001/api/datasources
```

***REMOVED******REMOVED*** Security Considerations

1. **Change default passwords** in production
2. **Restrict network access** to monitoring ports
3. **Enable TLS** for external access
4. **Use secrets management** for sensitive configuration
5. **Regular security updates** for container images

***REMOVED******REMOVED*** Integration with CI/CD

The monitoring stack can be integrated with your CI/CD pipeline:

```yaml
***REMOVED*** Example GitHub Actions step
- name: Check Monitoring Health
  run: |
    ./monitoring/scripts/health-check.sh
```
