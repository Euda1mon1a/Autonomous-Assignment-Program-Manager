***REMOVED*** Service Operations Guide

***REMOVED******REMOVED*** Overview

This guide provides comprehensive instructions for operating, monitoring, and troubleshooting the Residency Scheduler services. It covers both Docker-based and manual deployment scenarios.

***REMOVED******REMOVED*** Table of Contents

1. [Service Architecture](***REMOVED***service-architecture)
2. [Starting Services](***REMOVED***starting-services)
3. [Stopping Services](***REMOVED***stopping-services)
4. [Checking Service Status](***REMOVED***checking-service-status)
5. [Health Checks](***REMOVED***health-checks)
6. [Monitoring Stack](***REMOVED***monitoring-stack)
7. [Log Management](***REMOVED***log-management)
8. [Background Tasks (Celery)](***REMOVED***background-tasks-celery)
9. [Troubleshooting](***REMOVED***troubleshooting)
10. [Emergency Procedures](***REMOVED***emergency-procedures)

---

***REMOVED******REMOVED*** Service Architecture

***REMOVED******REMOVED******REMOVED*** Core Services

| Service | Container Name | Port | Purpose |
|---------|----------------|------|---------|
| PostgreSQL | residency-scheduler-db | 5432 | Primary database |
| FastAPI Backend | residency-scheduler-backend | 8000 | REST API, business logic |
| Next.js Frontend | residency-scheduler-frontend | 3000 | Web user interface |

***REMOVED******REMOVED******REMOVED*** Production Services

| Service | Container Name | Port | Purpose |
|---------|----------------|------|---------|
| Redis | rs-redis-prod | 6379 | Cache, message broker |
| Celery Worker | rs-celery-prod | - | Background task processing |

***REMOVED******REMOVED******REMOVED*** Monitoring Stack

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

***REMOVED******REMOVED******REMOVED*** Infrastructure Services

| Service | Port | Purpose |
|---------|------|---------|
| Nginx | 80, 443 | Reverse proxy, SSL termination |
| Certbot | - | SSL certificate management |

---

***REMOVED******REMOVED*** Starting Services

***REMOVED******REMOVED******REMOVED*** Docker Deployment

***REMOVED******REMOVED******REMOVED******REMOVED*** Development Mode

```bash
***REMOVED*** Navigate to project directory
cd /path/to/Autonomous-Assignment-Program-Manager

***REMOVED*** Start core services with development overrides (hot reload enabled)
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

***REMOVED*** View startup logs
docker-compose logs -f
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Production Mode

```bash
***REMOVED*** Start core services with production configuration
docker-compose -f docker-compose.yml -f .docker/docker-compose.prod.yml up -d

***REMOVED*** Start with Nginx reverse proxy
docker-compose -f docker-compose.yml -f .docker/docker-compose.prod.yml \
    -f nginx/docker-compose.nginx.yml up -d

***REMOVED*** Start monitoring stack
docker-compose -f monitoring/docker-compose.monitoring.yml up -d
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Start Individual Services

```bash
***REMOVED*** Start only the database
docker-compose up -d db

***REMOVED*** Start backend (waits for healthy db)
docker-compose up -d backend

***REMOVED*** Start frontend
docker-compose up -d frontend
```

***REMOVED******REMOVED******REMOVED*** Manual Deployment

```bash
***REMOVED*** Start PostgreSQL
sudo systemctl start postgresql

***REMOVED*** Start backend service
sudo systemctl start residency-backend

***REMOVED*** Start frontend (PM2)
pm2 start residency-frontend

***REMOVED*** Start Nginx
sudo systemctl start nginx
```

---

***REMOVED******REMOVED*** Stopping Services

***REMOVED******REMOVED******REMOVED*** Docker Deployment

```bash
***REMOVED*** Stop all services (preserves data volumes)
docker-compose down

***REMOVED*** Stop all services and remove volumes (DATA LOSS!)
docker-compose down -v

***REMOVED*** Stop specific service
docker-compose stop backend

***REMOVED*** Stop with all compose files
docker-compose -f docker-compose.yml -f .docker/docker-compose.prod.yml down
```

***REMOVED******REMOVED******REMOVED*** Manual Deployment

```bash
***REMOVED*** Stop all services
sudo systemctl stop residency-backend
pm2 stop residency-frontend
sudo systemctl stop nginx

***REMOVED*** Stop PostgreSQL (careful - affects all databases)
sudo systemctl stop postgresql
```

***REMOVED******REMOVED******REMOVED*** Graceful Shutdown

```bash
***REMOVED*** Docker: Allow 30 seconds for graceful shutdown
docker-compose stop -t 30

***REMOVED*** Send SIGTERM to allow cleanup
docker-compose kill -s SIGTERM backend
```

---

***REMOVED******REMOVED*** Checking Service Status

***REMOVED******REMOVED******REMOVED*** Docker Status Commands

```bash
***REMOVED*** View all container status
docker-compose ps

***REMOVED*** Expected healthy output:
***REMOVED*** NAME                           STATUS              PORTS
***REMOVED*** residency-scheduler-db         Up (healthy)        5432/tcp
***REMOVED*** residency-scheduler-backend    Up (healthy)        8000/tcp
***REMOVED*** residency-scheduler-frontend   Up (healthy)        3000/tcp

***REMOVED*** Detailed container info
docker inspect residency-scheduler-backend

***REMOVED*** Resource usage
docker stats --no-stream

***REMOVED*** Check specific container health
docker inspect --format='{{.State.Health.Status}}' residency-scheduler-db
```

***REMOVED******REMOVED******REMOVED*** Manual Deployment Status

```bash
***REMOVED*** Check systemd services
sudo systemctl status residency-backend
sudo systemctl status postgresql
sudo systemctl status nginx

***REMOVED*** Check PM2 processes
pm2 status
pm2 show residency-frontend

***REMOVED*** Check listening ports
sudo ss -tlnp | grep -E '(3000|8000|5432)'
```

***REMOVED******REMOVED******REMOVED*** Quick Status Script

Create a status check script at `/usr/local/bin/rs-status`:

```bash
***REMOVED***!/bin/bash
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

***REMOVED******REMOVED*** Health Checks

***REMOVED******REMOVED******REMOVED*** Available Health Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `GET /` | GET | Basic health (returns `{"status": "healthy"}`) |
| `GET /health` | GET | Detailed health with database connectivity |
| `GET /health/resilience` | GET | Resilience system status |
| `GET /metrics` | GET | Prometheus metrics endpoint |

***REMOVED******REMOVED******REMOVED*** Health Check Examples

```bash
***REMOVED*** Basic health check
curl http://localhost:8000/health
***REMOVED*** Response: {"status": "healthy", "database": "connected"}

***REMOVED*** Resilience system status
curl http://localhost:8000/health/resilience
***REMOVED*** Response includes: utilization_monitor, defense_in_depth,
***REMOVED***                    contingency_analyzer, fallback_scheduler

***REMOVED*** Prometheus metrics
curl http://localhost:8000/metrics
```

***REMOVED******REMOVED******REMOVED*** Container Health Checks

Docker containers have built-in health checks:

| Service | Health Check Command | Interval |
|---------|---------------------|----------|
| PostgreSQL | `pg_isready -U scheduler` | 10s |
| Backend | `curl -f http://localhost:8000/health` | 30s |
| Frontend | `wget http://localhost:3000` | 30s |
| Redis | `redis-cli ping` | 10s |
| Celery | `celery inspect ping` | 60s |

***REMOVED******REMOVED******REMOVED*** Automated Health Monitoring

The Celery worker runs periodic health checks:

| Task | Schedule | Description |
|------|----------|-------------|
| `periodic_health_check` | Every 15 minutes | Full system health assessment |
| `run_contingency_analysis` | Daily 2 AM UTC | N-1/N-2 vulnerability analysis |
| `generate_utilization_forecast` | Daily 6 AM UTC | Utilization forecasting |
| `precompute_fallback_schedules` | Weekly Sunday 3 AM | Crisis fallback preparation |

---

***REMOVED******REMOVED*** Monitoring Stack

***REMOVED******REMOVED******REMOVED*** Starting the Monitoring Stack

```bash
***REMOVED*** Start monitoring services
docker-compose -f monitoring/docker-compose.monitoring.yml up -d

***REMOVED*** Verify all monitoring services
docker-compose -f monitoring/docker-compose.monitoring.yml ps
```

***REMOVED******REMOVED******REMOVED*** Accessing Monitoring Tools

| Tool | URL | Default Credentials |
|------|-----|---------------------|
| Grafana | http://localhost:3001 | admin / (see .env) |
| Prometheus | http://localhost:9090 | None |
| Alertmanager | http://localhost:9093 | None |

***REMOVED******REMOVED******REMOVED*** Key Prometheus Metrics

```promql
***REMOVED*** HTTP request rate
rate(http_requests_total[5m])

***REMOVED*** Request latency (95th percentile)
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

***REMOVED*** Database connection pool usage
pg_stat_activity_count

***REMOVED*** Utilization rate
residency_scheduler_utilization_rate

***REMOVED*** Defense level
residency_scheduler_defense_level
```

***REMOVED******REMOVED******REMOVED*** Grafana Dashboards

Pre-configured dashboards are available for:

- **Application Overview**: Request rates, latencies, error rates
- **Database Performance**: Query times, connection pools, table sizes
- **System Resources**: CPU, memory, disk, network
- **Resilience Metrics**: Utilization, defense levels, contingency status

***REMOVED******REMOVED******REMOVED*** Configuring Alerts

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
        channel: '***REMOVED***alerts'

  - name: 'pagerduty-critical'
    pagerduty_configs:
      - service_key: '<your-pagerduty-key>'
```

---

***REMOVED******REMOVED*** Log Management

***REMOVED******REMOVED******REMOVED*** Viewing Logs

***REMOVED******REMOVED******REMOVED******REMOVED*** Docker Logs

```bash
***REMOVED*** All services
docker-compose logs -f

***REMOVED*** Specific service
docker-compose logs -f backend

***REMOVED*** Last 100 lines
docker-compose logs --tail=100 backend

***REMOVED*** Since specific time
docker-compose logs --since="2024-01-01T00:00:00" backend

***REMOVED*** With timestamps
docker-compose logs -t backend
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Manual Deployment Logs

```bash
***REMOVED*** Backend logs
sudo journalctl -u residency-backend -f

***REMOVED*** Nginx access logs
sudo tail -f /var/log/nginx/access.log

***REMOVED*** Application logs
sudo tail -f /var/log/residency-scheduler/backend.log
```

***REMOVED******REMOVED******REMOVED*** Log Aggregation with Loki

```bash
***REMOVED*** Query logs via Grafana's Explore tab
***REMOVED*** Or use LogCLI:
logcli query '{container="residency-scheduler-backend"}'

***REMOVED*** Filter by level
logcli query '{container="residency-scheduler-backend"} |= "ERROR"'
```

***REMOVED******REMOVED******REMOVED*** Log Levels

Configure log levels via environment variables:

```bash
***REMOVED*** Backend log level
LOG_LEVEL=INFO  ***REMOVED*** DEBUG, INFO, WARNING, ERROR, CRITICAL

***REMOVED*** Celery log level
CELERY_LOG_LEVEL=INFO
```

---

***REMOVED******REMOVED*** Background Tasks (Celery)

***REMOVED******REMOVED******REMOVED*** Checking Celery Status

```bash
***REMOVED*** Worker status
docker-compose exec celery-worker celery -A app.celery_app inspect active

***REMOVED*** Scheduled tasks
docker-compose exec celery-worker celery -A app.celery_app inspect scheduled

***REMOVED*** Task statistics
docker-compose exec celery-worker celery -A app.celery_app inspect stats
```

***REMOVED******REMOVED******REMOVED*** Celery Queues

| Queue | Purpose | Tasks |
|-------|---------|-------|
| resilience | Health monitoring | Health checks, contingency analysis |
| notifications | Alert delivery | Email, Slack notifications |
| default | General tasks | Miscellaneous background tasks |

***REMOVED******REMOVED******REMOVED*** Manually Triggering Tasks

```bash
***REMOVED*** Trigger health check
docker-compose exec backend python -c "
from app.resilience.tasks import periodic_health_check
periodic_health_check.delay()
"

***REMOVED*** Trigger contingency analysis
docker-compose exec backend python -c "
from app.resilience.tasks import run_contingency_analysis
run_contingency_analysis.delay()
"
```

***REMOVED******REMOVED******REMOVED*** Monitoring Celery with Flower (Optional)

```bash
***REMOVED*** Start Flower monitoring
docker-compose exec celery-worker celery -A app.celery_app flower --port=5555

***REMOVED*** Access at http://localhost:5555
```

---

***REMOVED******REMOVED*** Troubleshooting

***REMOVED******REMOVED******REMOVED*** Service Won't Start

***REMOVED******REMOVED******REMOVED******REMOVED*** Database Issues

```bash
***REMOVED*** Check PostgreSQL logs
docker-compose logs db

***REMOVED*** Verify database is accepting connections
docker-compose exec db pg_isready -U scheduler

***REMOVED*** Check database exists
docker-compose exec db psql -U scheduler -l

***REMOVED*** Repair database (if corrupted)
docker-compose exec db pg_resetwal -D /var/lib/postgresql/data
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Backend Issues

```bash
***REMOVED*** Check backend logs
docker-compose logs backend

***REMOVED*** Verify environment variables
docker-compose exec backend env | grep -E '(DATABASE|SECRET)'

***REMOVED*** Test database connection from backend
docker-compose exec backend python -c "
from app.db.session import SessionLocal
db = SessionLocal()
print('Database connected!' if db else 'Failed')
"

***REMOVED*** Run migrations manually
docker-compose exec backend alembic upgrade head
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Frontend Issues

```bash
***REMOVED*** Check frontend logs
docker-compose logs frontend

***REMOVED*** Verify API URL configuration
docker-compose exec frontend env | grep NEXT_PUBLIC

***REMOVED*** Rebuild frontend
docker-compose build --no-cache frontend
```

***REMOVED******REMOVED******REMOVED*** Connection Issues

```bash
***REMOVED*** Test internal DNS resolution
docker-compose exec backend ping db
docker-compose exec frontend ping backend

***REMOVED*** Check network connectivity
docker network ls
docker network inspect residency-scheduler_default

***REMOVED*** Verify ports are exposed
docker-compose ps --format "table {{.Name}}\t{{.Ports}}"
```

***REMOVED******REMOVED******REMOVED*** Performance Issues

```bash
***REMOVED*** Check resource usage
docker stats

***REMOVED*** Identify slow queries
docker-compose exec db psql -U scheduler -c "
SELECT pid, now() - pg_stat_activity.query_start AS duration, query
FROM pg_stat_activity
WHERE state != 'idle'
ORDER BY duration DESC;
"

***REMOVED*** Check connection pool
docker-compose exec db psql -U scheduler -c "
SELECT count(*) FROM pg_stat_activity;
"
```

***REMOVED******REMOVED******REMOVED*** Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| `Connection refused` | Service not running | Start the service |
| `FATAL: password authentication failed` | Wrong credentials | Check .env file |
| `relation does not exist` | Missing migrations | Run `alembic upgrade head` |
| `No space left on device` | Disk full | Clean up logs/volumes |
| `OOM killed` | Out of memory | Increase container memory limits |

---

***REMOVED******REMOVED*** Emergency Procedures

***REMOVED******REMOVED******REMOVED*** Service Recovery

```bash
***REMOVED*** Full restart (preserves data)
docker-compose down
docker-compose up -d

***REMOVED*** Force recreate containers
docker-compose up -d --force-recreate

***REMOVED*** Reset to clean state (DATA LOSS - backup first!)
docker-compose down -v
docker-compose up -d
docker-compose exec backend alembic upgrade head
```

***REMOVED******REMOVED******REMOVED*** Database Recovery

```bash
***REMOVED*** Create emergency backup
docker-compose exec db pg_dump -U scheduler residency_scheduler > emergency_backup.sql

***REMOVED*** Restore from backup
docker-compose exec -T db psql -U scheduler residency_scheduler < backup.sql
```

***REMOVED******REMOVED******REMOVED*** Rollback Deployment

```bash
***REMOVED*** Stop services
docker-compose down

***REMOVED*** Checkout previous version
git checkout <previous-tag>

***REMOVED*** Rebuild and restart
docker-compose build
docker-compose up -d

***REMOVED*** Rollback migrations if needed
docker-compose exec backend alembic downgrade -1
```

***REMOVED******REMOVED******REMOVED*** Contact Information

For critical issues requiring immediate attention:

- **On-call Team**: oncall@your-domain.com
- **Database Admin**: dba@your-domain.com
- **Infrastructure**: infra@your-domain.com

---

***REMOVED******REMOVED*** Quick Reference Card

***REMOVED******REMOVED******REMOVED*** Essential Commands

```bash
***REMOVED*** Start all services
docker-compose up -d

***REMOVED*** Stop all services
docker-compose down

***REMOVED*** View logs
docker-compose logs -f

***REMOVED*** Check status
docker-compose ps

***REMOVED*** Health check
curl http://localhost:8000/health

***REMOVED*** Restart single service
docker-compose restart backend

***REMOVED*** View resource usage
docker stats
```

***REMOVED******REMOVED******REMOVED*** Important Ports

| Port | Service |
|------|---------|
| 3000 | Frontend |
| 8000 | Backend API |
| 5432 | PostgreSQL |
| 6379 | Redis |
| 9090 | Prometheus |
| 3001 | Grafana |

***REMOVED******REMOVED******REMOVED*** Log Locations

| Component | Docker | Manual |
|-----------|--------|--------|
| Backend | `docker-compose logs backend` | `/var/log/residency-scheduler/` |
| Frontend | `docker-compose logs frontend` | PM2 logs |
| Database | `docker-compose logs db` | `/var/log/postgresql/` |
| Nginx | `docker-compose logs nginx` | `/var/log/nginx/` |

---

*Last Updated: December 2024*
