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
***REMOVED*** DEVELOPMENT: Run with all ports exposed
docker-compose -f docker-compose.monitoring.yml up -d

***REMOVED*** PRODUCTION: Run with internal network only (recommended)
docker-compose -f docker-compose.monitoring.yml -f docker-compose.monitoring.prod.yml up -d

***REMOVED*** Or use the setup script (development mode)
./scripts/setup-monitoring.sh
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

***REMOVED******REMOVED******REMOVED*** ⚠️ CRITICAL: Production Deployment Security

**DO NOT deploy the base `docker-compose.monitoring.yml` file to production as-is.**

The base configuration exposes all monitoring ports for development convenience. In production, this creates serious security vulnerabilities:

- **Information Disclosure**: Prometheus, Grafana, and other services reveal system architecture, performance metrics, and potential vulnerabilities
- **No Built-in Authentication**: Services like Prometheus have no authentication mechanism
- **Attack Surface**: Exposed ports increase the attack surface for potential exploitation
- **Sensitive Data**: Monitoring data may contain database query patterns, API usage, and system internals

***REMOVED******REMOVED******REMOVED*** Production Deployment

**Always use the production override file:**

```bash
docker-compose \
  -f docker-compose.monitoring.yml \
  -f docker-compose.monitoring.prod.yml \
  up -d
```

The production override (`docker-compose.monitoring.prod.yml`) removes all external port mappings. Services remain accessible within the internal Docker network.

***REMOVED******REMOVED******REMOVED*** Accessing Monitoring in Production

***REMOVED******REMOVED******REMOVED******REMOVED*** Option 1: Authenticated Reverse Proxy (Recommended)

Set up nginx or Traefik with authentication in front of Grafana:

```nginx
***REMOVED*** Example nginx configuration
upstream grafana {
    server grafana:3000;
}

server {
    listen 443 ssl http2;
    server_name monitoring.example.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;

    location / {
        proxy_pass http://grafana;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Option 2: SSH Tunneling

For admin access to any monitoring service:

```bash
***REMOVED*** Tunnel to Grafana
ssh -L 3001:localhost:3001 user@production-server

***REMOVED*** Access at http://localhost:3001

***REMOVED*** Tunnel to Prometheus
ssh -L 9090:localhost:9090 user@production-server
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Option 3: VPN Access

Configure VPN access to the internal Docker network for authorized administrators.

***REMOVED******REMOVED******REMOVED*** Additional Security Best Practices

1. **Change default passwords** in production (especially Grafana)
   ```bash
   ***REMOVED*** Set strong Grafana admin password in .env
   GRAFANA_ADMIN_PASSWORD=$(python -c 'import secrets; print(secrets.token_urlsafe(32))')
   ```

2. **Restrict network access** to monitoring ports (handled by production override)

3. **Enable TLS** for external access (use reverse proxy with Let's Encrypt)

4. **Use secrets management** for sensitive configuration
   - Store alert webhook URLs in environment variables
   - Never commit `.env` files with production secrets
   - Use Docker secrets or HashiCorp Vault for credentials

5. **Regular security updates** for container images
   ```bash
   ***REMOVED*** Update images regularly
   docker-compose pull
   docker-compose up -d
   ```

6. **Enable audit logging** in Grafana
   ```env
   ***REMOVED*** In .env file
   GF_LOG_MODE=console file
   GF_LOG_LEVEL=info
   ```

7. **Implement rate limiting** on reverse proxy to prevent abuse

8. **Monitor monitoring access** - Set up alerts for unauthorized access attempts

***REMOVED******REMOVED******REMOVED*** Port Exposure Summary

**Development (docker-compose.monitoring.yml):**
- Grafana: 3001 → Exposed for UI access
- Prometheus: 9090 → Exposed for UI access
- Alertmanager: 9093 → Exposed for UI access
- Loki: 3100 → Exposed for API access
- All exporters: Various ports → Exposed for debugging

**Production (+ docker-compose.monitoring.prod.yml):**
- All services: Internal network only
- Access via reverse proxy or SSH tunnel only
- Zero external port exposure

***REMOVED******REMOVED*** Integration with CI/CD

The monitoring stack can be integrated with your CI/CD pipeline:

```yaml
***REMOVED*** Example GitHub Actions step
- name: Check Monitoring Health
  run: |
    ./monitoring/scripts/health-check.sh
```
