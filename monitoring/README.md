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
# DEVELOPMENT: Run with all ports exposed
docker-compose -f docker-compose.monitoring.yml up -d

# PRODUCTION: Run with internal network only (recommended)
docker-compose -f docker-compose.monitoring.yml -f docker-compose.monitoring.prod.yml up -d

# Or use the setup script (development mode)
./scripts/setup-monitoring.sh
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

### ⚠️ CRITICAL: Production Deployment Security

**DO NOT deploy the base `docker-compose.monitoring.yml` file to production as-is.**

The base configuration exposes all monitoring ports for development convenience. In production, this creates serious security vulnerabilities:

- **Information Disclosure**: Prometheus, Grafana, and other services reveal system architecture, performance metrics, and potential vulnerabilities
- **No Built-in Authentication**: Services like Prometheus have no authentication mechanism
- **Attack Surface**: Exposed ports increase the attack surface for potential exploitation
- **Sensitive Data**: Monitoring data may contain database query patterns, API usage, and system internals

### Production Deployment

**Always use the production override file:**

```bash
docker-compose \
  -f docker-compose.monitoring.yml \
  -f docker-compose.monitoring.prod.yml \
  up -d
```

The production override (`docker-compose.monitoring.prod.yml`) removes all external port mappings. Services remain accessible within the internal Docker network.

### Accessing Monitoring in Production

#### Option 1: Authenticated Reverse Proxy (Recommended)

Set up nginx or Traefik with authentication in front of Grafana:

```nginx
# Example nginx configuration
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

#### Option 2: SSH Tunneling

For admin access to any monitoring service:

```bash
# Tunnel to Grafana
ssh -L 3001:localhost:3001 user@production-server

# Access at http://localhost:3001

# Tunnel to Prometheus
ssh -L 9090:localhost:9090 user@production-server
```

#### Option 3: VPN Access

Configure VPN access to the internal Docker network for authorized administrators.

### Additional Security Best Practices

1. **Change default passwords** in production (especially Grafana)
   ```bash
   # Set strong Grafana admin password in .env
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
   # Update images regularly
   docker-compose pull
   docker-compose up -d
   ```

6. **Enable audit logging** in Grafana
   ```env
   # In .env file
   GF_LOG_MODE=console file
   GF_LOG_LEVEL=info
   ```

7. **Implement rate limiting** on reverse proxy to prevent abuse

8. **Monitor monitoring access** - Set up alerts for unauthorized access attempts

### Port Exposure Summary

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

## Integration with CI/CD

The monitoring stack can be integrated with your CI/CD pipeline:

```yaml
# Example GitHub Actions step
- name: Check Monitoring Health
  run: |
    ./monitoring/scripts/health-check.sh
```
