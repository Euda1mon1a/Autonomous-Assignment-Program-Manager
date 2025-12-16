# Service Operations Guide

## Overview

This guide provides comprehensive instructions for operating, monitoring, and troubleshooting the Residency Scheduler services. It covers both Docker-based and manual deployment scenarios.

## Table of Contents

1. [Service Architecture](#service-architecture)
2. [Starting Services](#starting-services)
3. [Stopping Services](#stopping-services)
4. [Checking Service Status](#checking-service-status)
5. [Health Checks](#health-checks)
6. [Monitoring Stack](#monitoring-stack)
7. [Log Management](#log-management)
8. [Background Tasks (Celery)](#background-tasks-celery)
9. [Troubleshooting](#troubleshooting)
10. [Emergency Procedures](#emergency-procedures)

---

## Service Architecture

### Core Services

| Service | Container Name | Port | Purpose |
|---------|----------------|------|---------|
| PostgreSQL | residency-scheduler-db | 5432 | Primary database |
| FastAPI Backend | residency-scheduler-backend | 8000 | REST API, business logic |
| Next.js Frontend | residency-scheduler-frontend | 3000 | Web user interface |

### Production Services

| Service | Container Name | Port | Purpose |
|---------|----------------|------|---------|
| Redis | rs-redis-prod | 6379 | Cache, message broker |
| Celery Worker | rs-celery-prod | - | Background task processing |

### Monitoring Stack

| Service | Port | Purpose |
|---------|------|---------|
| Prometheus | 9090 | Metrics collection |
| Grafana | 3001 | Visualization dashboards |
| Alertmanager | 9093 | Alert routing |
| Loki | 3100 | Log aggregation |
| Promtail | - | Log collection agent |
| Node Exporter | 9100 | Host metrics |
| cAdvisor | 8080 | Container metrics |
| PostgreSQL Exporter | 9187 | Database metrics |

### Infrastructure Services

| Service | Port | Purpose |
|---------|------|---------|
| Nginx | 80, 443 | Reverse proxy, SSL termination |
| Certbot | - | SSL certificate management |

---

## Starting Services

### Docker Deployment

#### Development Mode

```bash
# Navigate to project directory
cd /path/to/Autonomous-Assignment-Program-Manager

# Start core services with development overrides (hot reload enabled)
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# View startup logs
docker-compose logs -f
```

#### Production Mode

```bash
# Start core services with production configuration
docker-compose -f docker-compose.yml -f .docker/docker-compose.prod.yml up -d

# Start with Nginx reverse proxy
docker-compose -f docker-compose.yml -f .docker/docker-compose.prod.yml \
    -f nginx/docker-compose.nginx.yml up -d

# Start monitoring stack
docker-compose -f monitoring/docker-compose.monitoring.yml up -d
```

#### Start Individual Services

```bash
# Start only the database
docker-compose up -d db

# Start backend (waits for healthy db)
docker-compose up -d backend

# Start frontend
docker-compose up -d frontend
```

### Manual Deployment

```bash
# Start PostgreSQL
sudo systemctl start postgresql

# Start backend service
sudo systemctl start residency-backend

# Start frontend (PM2)
pm2 start residency-frontend

# Start Nginx
sudo systemctl start nginx
```

---

## Stopping Services

### Docker Deployment

```bash
# Stop all services (preserves data volumes)
docker-compose down

# Stop all services and remove volumes (DATA LOSS!)
docker-compose down -v

# Stop specific service
docker-compose stop backend

# Stop with all compose files
docker-compose -f docker-compose.yml -f .docker/docker-compose.prod.yml down
```

### Manual Deployment

```bash
# Stop all services
sudo systemctl stop residency-backend
pm2 stop residency-frontend
sudo systemctl stop nginx

# Stop PostgreSQL (careful - affects all databases)
sudo systemctl stop postgresql
```

### Graceful Shutdown

```bash
# Docker: Allow 30 seconds for graceful shutdown
docker-compose stop -t 30

# Send SIGTERM to allow cleanup
docker-compose kill -s SIGTERM backend
```

---

## Checking Service Status

### Docker Status Commands

```bash
# View all container status
docker-compose ps

# Expected healthy output:
# NAME                           STATUS              PORTS
# residency-scheduler-db         Up (healthy)        5432/tcp
# residency-scheduler-backend    Up (healthy)        8000/tcp
# residency-scheduler-frontend   Up (healthy)        3000/tcp

# Detailed container info
docker inspect residency-scheduler-backend

# Resource usage
docker stats --no-stream

# Check specific container health
docker inspect --format='{{.State.Health.Status}}' residency-scheduler-db
```

### Manual Deployment Status

```bash
# Check systemd services
sudo systemctl status residency-backend
sudo systemctl status postgresql
sudo systemctl status nginx

# Check PM2 processes
pm2 status
pm2 show residency-frontend

# Check listening ports
sudo ss -tlnp | grep -E '(3000|8000|5432)'
```

### Quick Status Script

Create a status check script at `/usr/local/bin/rs-status`:

```bash
#!/bin/bash
echo "=== Residency Scheduler Status ==="
echo ""
echo "--- Containers ---"
docker-compose ps 2>/dev/null || echo "Docker Compose not running"
echo ""
echo "--- Health Endpoints ---"
echo -n "Backend:  "
curl -sf http://localhost:8000/health && echo " OK" || echo " FAIL"
echo -n "Frontend: "
curl -sf http://localhost:3000 >/dev/null && echo "OK" || echo "FAIL"
echo ""
echo "--- Resource Usage ---"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" 2>/dev/null
```

---

## Health Checks

### Available Health Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `GET /` | GET | Basic health (returns `{"status": "healthy"}`) |
| `GET /health` | GET | Detailed health with database connectivity |
| `GET /health/resilience` | GET | Resilience system status |
| `GET /metrics` | GET | Prometheus metrics endpoint |

### Health Check Examples

```bash
# Basic health check
curl http://localhost:8000/health
# Response: {"status": "healthy", "database": "connected"}

# Resilience system status
curl http://localhost:8000/health/resilience
# Response includes: utilization_monitor, defense_in_depth,
#                    contingency_analyzer, fallback_scheduler

# Prometheus metrics
curl http://localhost:8000/metrics
```

### Container Health Checks

Docker containers have built-in health checks:

| Service | Health Check Command | Interval |
|---------|---------------------|----------|
| PostgreSQL | `pg_isready -U scheduler` | 10s |
| Backend | `curl -f http://localhost:8000/health` | 30s |
| Frontend | `wget http://localhost:3000` | 30s |
| Redis | `redis-cli ping` | 10s |
| Celery | `celery inspect ping` | 60s |

### Automated Health Monitoring

The Celery worker runs periodic health checks:

| Task | Schedule | Description |
|------|----------|-------------|
| `periodic_health_check` | Every 15 minutes | Full system health assessment |
| `run_contingency_analysis` | Daily 2 AM UTC | N-1/N-2 vulnerability analysis |
| `generate_utilization_forecast` | Daily 6 AM UTC | Utilization forecasting |
| `precompute_fallback_schedules` | Weekly Sunday 3 AM | Crisis fallback preparation |

---

## Monitoring Stack

### Starting the Monitoring Stack

```bash
# Start monitoring services
docker-compose -f monitoring/docker-compose.monitoring.yml up -d

# Verify all monitoring services
docker-compose -f monitoring/docker-compose.monitoring.yml ps
```

### Accessing Monitoring Tools

| Tool | URL | Default Credentials |
|------|-----|---------------------|
| Grafana | http://localhost:3001 | admin / (see .env) |
| Prometheus | http://localhost:9090 | None |
| Alertmanager | http://localhost:9093 | None |

### Key Prometheus Metrics

```promql
# HTTP request rate
rate(http_requests_total[5m])

# Request latency (95th percentile)
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Database connection pool usage
pg_stat_activity_count

# Utilization rate
residency_scheduler_utilization_rate

# Defense level
residency_scheduler_defense_level
```

### Grafana Dashboards

Pre-configured dashboards are available for:

- **Application Overview**: Request rates, latencies, error rates
- **Database Performance**: Query times, connection pools, table sizes
- **System Resources**: CPU, memory, disk, network
- **Resilience Metrics**: Utilization, defense levels, contingency status

### Configuring Alerts

Edit `monitoring/alertmanager/alertmanager.yml`:

```yaml
receivers:
  - name: 'email-alerts'
    email_configs:
      - to: 'ops@your-domain.com'
        from: 'alerts@your-domain.com'
        smarthost: 'smtp.your-domain.com:587'

  - name: 'slack-alerts'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/xxx/xxx/xxx'
        channel: '#alerts'

  - name: 'pagerduty-critical'
    pagerduty_configs:
      - service_key: '<your-pagerduty-key>'
```

---

## Log Management

### Viewing Logs

#### Docker Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail=100 backend

# Since specific time
docker-compose logs --since="2024-01-01T00:00:00" backend

# With timestamps
docker-compose logs -t backend
```

#### Manual Deployment Logs

```bash
# Backend logs
sudo journalctl -u residency-backend -f

# Nginx access logs
sudo tail -f /var/log/nginx/access.log

# Application logs
sudo tail -f /var/log/residency-scheduler/backend.log
```

### Log Aggregation with Loki

```bash
# Query logs via Grafana's Explore tab
# Or use LogCLI:
logcli query '{container="residency-scheduler-backend"}'

# Filter by level
logcli query '{container="residency-scheduler-backend"} |= "ERROR"'
```

### Log Levels

Configure log levels via environment variables:

```bash
# Backend log level
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# Celery log level
CELERY_LOG_LEVEL=INFO
```

---

## Background Tasks (Celery)

### Checking Celery Status

```bash
# Worker status
docker-compose exec celery-worker celery -A app.celery_app inspect active

# Scheduled tasks
docker-compose exec celery-worker celery -A app.celery_app inspect scheduled

# Task statistics
docker-compose exec celery-worker celery -A app.celery_app inspect stats
```

### Celery Queues

| Queue | Purpose | Tasks |
|-------|---------|-------|
| resilience | Health monitoring | Health checks, contingency analysis |
| notifications | Alert delivery | Email, Slack notifications |
| default | General tasks | Miscellaneous background tasks |

### Manually Triggering Tasks

```bash
# Trigger health check
docker-compose exec backend python -c "
from app.resilience.tasks import periodic_health_check
periodic_health_check.delay()
"

# Trigger contingency analysis
docker-compose exec backend python -c "
from app.resilience.tasks import run_contingency_analysis
run_contingency_analysis.delay()
"
```

### Monitoring Celery with Flower (Optional)

```bash
# Start Flower monitoring
docker-compose exec celery-worker celery -A app.celery_app flower --port=5555

# Access at http://localhost:5555
```

---

## Troubleshooting

### Service Won't Start

#### Database Issues

```bash
# Check PostgreSQL logs
docker-compose logs db

# Verify database is accepting connections
docker-compose exec db pg_isready -U scheduler

# Check database exists
docker-compose exec db psql -U scheduler -l

# Repair database (if corrupted)
docker-compose exec db pg_resetwal -D /var/lib/postgresql/data
```

#### Backend Issues

```bash
# Check backend logs
docker-compose logs backend

# Verify environment variables
docker-compose exec backend env | grep -E '(DATABASE|SECRET)'

# Test database connection from backend
docker-compose exec backend python -c "
from app.db.session import SessionLocal
db = SessionLocal()
print('Database connected!' if db else 'Failed')
"

# Run migrations manually
docker-compose exec backend alembic upgrade head
```

#### Frontend Issues

```bash
# Check frontend logs
docker-compose logs frontend

# Verify API URL configuration
docker-compose exec frontend env | grep NEXT_PUBLIC

# Rebuild frontend
docker-compose build --no-cache frontend
```

### Connection Issues

```bash
# Test internal DNS resolution
docker-compose exec backend ping db
docker-compose exec frontend ping backend

# Check network connectivity
docker network ls
docker network inspect residency-scheduler_default

# Verify ports are exposed
docker-compose ps --format "table {{.Name}}\t{{.Ports}}"
```

### Performance Issues

```bash
# Check resource usage
docker stats

# Identify slow queries
docker-compose exec db psql -U scheduler -c "
SELECT pid, now() - pg_stat_activity.query_start AS duration, query
FROM pg_stat_activity
WHERE state != 'idle'
ORDER BY duration DESC;
"

# Check connection pool
docker-compose exec db psql -U scheduler -c "
SELECT count(*) FROM pg_stat_activity;
"
```

### Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| `Connection refused` | Service not running | Start the service |
| `FATAL: password authentication failed` | Wrong credentials | Check .env file |
| `relation does not exist` | Missing migrations | Run `alembic upgrade head` |
| `No space left on device` | Disk full | Clean up logs/volumes |
| `OOM killed` | Out of memory | Increase container memory limits |

---

## Emergency Procedures

### Service Recovery

```bash
# Full restart (preserves data)
docker-compose down
docker-compose up -d

# Force recreate containers
docker-compose up -d --force-recreate

# Reset to clean state (DATA LOSS - backup first!)
docker-compose down -v
docker-compose up -d
docker-compose exec backend alembic upgrade head
```

### Database Recovery

```bash
# Create emergency backup
docker-compose exec db pg_dump -U scheduler residency_scheduler > emergency_backup.sql

# Restore from backup
docker-compose exec -T db psql -U scheduler residency_scheduler < backup.sql
```

### Rollback Deployment

```bash
# Stop services
docker-compose down

# Checkout previous version
git checkout <previous-tag>

# Rebuild and restart
docker-compose build
docker-compose up -d

# Rollback migrations if needed
docker-compose exec backend alembic downgrade -1
```

### Contact Information

For critical issues requiring immediate attention:

- **On-call Team**: oncall@your-domain.com
- **Database Admin**: dba@your-domain.com
- **Infrastructure**: infra@your-domain.com

---

## Quick Reference Card

### Essential Commands

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f

# Check status
docker-compose ps

# Health check
curl http://localhost:8000/health

# Restart single service
docker-compose restart backend

# View resource usage
docker stats
```

### Important Ports

| Port | Service |
|------|---------|
| 3000 | Frontend |
| 8000 | Backend API |
| 5432 | PostgreSQL |
| 6379 | Redis |
| 9090 | Prometheus |
| 3001 | Grafana |

### Log Locations

| Component | Docker | Manual |
|-----------|--------|--------|
| Backend | `docker-compose logs backend` | `/var/log/residency-scheduler/` |
| Frontend | `docker-compose logs frontend` | PM2 logs |
| Database | `docker-compose logs db` | `/var/log/postgresql/` |
| Nginx | `docker-compose logs nginx` | `/var/log/nginx/` |

---

*Last Updated: December 2024*
