# Infrastructure Guide

## Overview

This guide provides comprehensive information about the Residency Scheduler infrastructure, including architecture, service dependencies, deployment patterns, scaling strategies, monitoring, and security considerations.

**Target Audience**: DevOps engineers, system administrators, infrastructure teams

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Service Dependencies](#service-dependencies)
3. [Port Mappings](#port-mappings)
4. [Environment Configuration](#environment-configuration)
5. [Scaling Considerations](#scaling-considerations)
6. [Monitoring Setup](#monitoring-setup)
7. [Backup and Recovery](#backup-and-recovery)
8. [Security Considerations](#security-considerations)
9. [Performance Tuning](#performance-tuning)
10. [Disaster Recovery](#disaster-recovery)

---

## Architecture Overview

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                           INTERNET                                   │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │   Nginx Reverse Proxy   │
                    │   (Port 80/443)         │
                    │   - SSL Termination     │
                    │   - Load Balancing      │
                    │   - Static Assets       │
                    └──────────┬──────────────┘
                               │
                ┌──────────────┼──────────────┐
                │              │              │
       ┌────────▼────────┐    │    ┌────────▼────────┐
       │   Frontend       │    │    │   Backend API   │
       │   (Next.js)      │◄───┘    │   (FastAPI)     │
       │   Port 3000      │         │   Port 8000     │
       │                  │         │                 │
       │   - React UI     │         │   - REST API    │
       │   - SSR/SSG      │         │   - Auth        │
       │   - Client State │         │   - Business    │
       └──────────────────┘         │     Logic       │
                                    └────────┬────────┘
                                             │
                        ┌────────────────────┼────────────────────┐
                        │                    │                    │
              ┌─────────▼─────────┐  ┌──────▼──────┐   ┌────────▼────────┐
              │   PostgreSQL      │  │   Redis     │   │  Celery Worker  │
              │   (Port 5432)     │  │  (Port 6379)│   │                 │
              │                   │  │             │   │  - Async Tasks  │
              │   - Primary DB    │  │  - Cache    │   │  - Background   │
              │   - Persistence   │  │  - Sessions │   │  - Scheduling   │
              │   - ACID          │  │  - Celery   │   └────────┬────────┘
              └───────────────────┘  │    Broker   │            │
                                     └──────┬──────┘            │
                                            │                   │
                                     ┌──────▼───────────────────▼──┐
                                     │    Celery Beat Scheduler    │
                                     │                             │
                                     │   - Periodic Tasks          │
                                     │   - Health Checks           │
                                     │   - Resilience Analysis     │
                                     └─────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                        MONITORING LAYER                              │
│                                                                      │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐        │
│   │  Prometheus  │───▶│   Grafana    │    │    Logs      │        │
│   │  (Metrics)   │    │  (Dashboards)│    │  (ELK/Loki)  │        │
│   └──────────────┘    └──────────────┘    └──────────────┘        │
└─────────────────────────────────────────────────────────────────────┘
```

### Component Descriptions

#### Frontend Layer
- **Technology**: Next.js 14 with React 18
- **Responsibilities**:
  - User interface rendering
  - Client-side routing
  - State management
  - API communication
- **Deployment**: Docker container or Node.js process

#### Backend Layer
- **Technology**: FastAPI (Python 3.11+)
- **Responsibilities**:
  - RESTful API endpoints
  - Business logic
  - Authentication/Authorization
  - Database operations
  - Resilience framework
- **Deployment**: Docker container with Uvicorn/Gunicorn

#### Database Layer
- **Technology**: PostgreSQL 15
- **Responsibilities**:
  - Primary data storage
  - Relational data integrity
  - Transaction management
- **Deployment**: Docker container or managed service (RDS, Cloud SQL)

#### Cache/Message Broker Layer
- **Technology**: Redis 7
- **Responsibilities**:
  - Celery message broker
  - Result backend
  - Session storage
  - Application cache
- **Deployment**: Docker container or managed service (ElastiCache, Redis Cloud)

#### Background Task Layer
- **Technology**: Celery with Redis broker
- **Components**:
  - **Worker**: Executes async tasks
  - **Beat**: Schedules periodic tasks
- **Responsibilities**:
  - Health checks
  - Contingency analysis
  - Fallback precomputation
  - Utilization forecasting
  - Alert notifications

---

## Service Dependencies

### Dependency Graph

```
┌──────────┐
│    db    │ (No dependencies)
└────┬─────┘
     │
     │   ┌───────┐
     └──▶│ redis │ (No dependencies)
         └───┬───┘
             │
     ┌───────┴───────┐
     │               │
┌────▼─────┐   ┌────▼──────────┐
│ backend  │   │ celery-worker │
└────┬─────┘   └────┬──────────┘
     │              │
     │         ┌────▼──────────┐
     │         │ celery-beat   │
     │         └───────────────┘
     │
┌────▼─────┐
│ frontend │
└──────────┘
```

### Startup Order

1. **db** - Database must be ready first
2. **redis** - Cache/broker second
3. **backend** + **celery-worker** + **celery-beat** - Can start in parallel after db + redis
4. **frontend** - Starts after backend is healthy

### Health Check Configuration

Each service has health checks to ensure proper dependency resolution:

```yaml
# Database health check
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U scheduler -d residency_scheduler"]
  interval: 10s
  timeout: 5s
  retries: 5
  start_period: 10s

# Redis health check
healthcheck:
  test: ["CMD", "redis-cli", "ping"]
  interval: 10s
  timeout: 5s
  retries: 5
  start_period: 5s

# Backend health check
healthcheck:
  test: ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

---

## Port Mappings

### Default Ports

| Service | Internal Port | External Port | Protocol | Purpose |
|---------|--------------|---------------|----------|---------|
| PostgreSQL | 5432 | 5432* | TCP | Database connections |
| Redis | 6379 | 6379* | TCP | Cache/broker access |
| Backend | 8000 | 8000 | HTTP | API endpoints |
| Frontend | 3000 | 3000 | HTTP | Web application |
| Nginx | 80/443 | 80/443 | HTTP/HTTPS | Reverse proxy |
| Prometheus | 9090 | 9090* | HTTP | Metrics collection |
| Grafana | 3001 | 3001* | HTTP | Monitoring dashboard |

*Not exposed externally in production (internal Docker network only)

### Port Configuration

```bash
# Development (all ports exposed)
BACKEND_PORT=8000
FRONTEND_PORT=3000
DB_PORT=5432
REDIS_PORT=6379

# Production (only HTTP/HTTPS exposed)
HTTP_PORT=80
HTTPS_PORT=443
# Internal services on Docker network only
```

### Firewall Rules (Production)

```bash
# Allow HTTP/HTTPS only
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow SSH (for management)
sudo ufw allow 22/tcp

# Block direct access to internal services
sudo ufw deny 5432/tcp  # PostgreSQL
sudo ufw deny 6379/tcp  # Redis
sudo ufw deny 8000/tcp  # Backend (use Nginx)

# Enable firewall
sudo ufw enable
```

---

## Environment Configuration

### Environment Hierarchy

1. **Development**: `.env.dev` - Local development with debug enabled
2. **Staging**: `.env.staging` - Production-like environment for testing
3. **Production**: `.env.prod` - Live production environment

### Configuration Management

```bash
# Store sensitive configs securely
# Option 1: Environment variables (12-factor app)
export DATABASE_URL="postgresql://..."
export SECRET_KEY="..."

# Option 2: Docker secrets
docker secret create db_password db_password.txt

# Option 3: HashiCorp Vault or AWS Secrets Manager
vault kv get secret/residency-scheduler/db_password
```

### Required Variables by Service

#### Backend
```bash
DATABASE_URL=postgresql://scheduler:${DB_PASSWORD}@db:5432/residency_scheduler
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
SECRET_KEY=<256-bit-secret>
DEBUG=false
LOG_LEVEL=info
CORS_ORIGINS=["https://scheduler.example.com"]
```

#### Frontend
```bash
NEXT_PUBLIC_API_URL=https://api.scheduler.example.com
NODE_ENV=production
NEXT_TELEMETRY_DISABLED=1
```

#### Database
```bash
POSTGRES_USER=scheduler
POSTGRES_PASSWORD=<strong-password>
POSTGRES_DB=residency_scheduler
```

---

## Scaling Considerations

### Vertical Scaling (Scale Up)

Increase resources for existing containers:

```yaml
# docker-compose.prod.yml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '4.0'    # Increase from 2.0
          memory: 4G     # Increase from 2G
```

### Horizontal Scaling (Scale Out)

#### Backend API

```bash
# Scale backend to 3 instances
docker compose up -d --scale backend=3

# Use Nginx for load balancing
upstream backend {
    server backend-1:8000;
    server backend-2:8000;
    server backend-3:8000;
}
```

#### Celery Workers

```yaml
# docker-compose.prod.yml
services:
  celery-worker:
    deploy:
      replicas: 3  # Run 3 worker instances
```

Or manually:

```bash
# Scale workers
docker compose up -d --scale celery-worker=5
```

#### Database Scaling

**Read Replicas** (PostgreSQL):
```sql
-- Create read replica
CREATE SUBSCRIPTION read_replica
CONNECTION 'host=primary dbname=residency_scheduler'
PUBLICATION my_publication;
```

**Connection Pooling** (PgBouncer):
```bash
# Add PgBouncer service
pgbouncer:
  image: pgbouncer/pgbouncer
  environment:
    DATABASES_HOST: db
    DATABASES_PORT: 5432
    DATABASES_DBNAME: residency_scheduler
    PGBOUNCER_POOL_MODE: transaction
    PGBOUNCER_MAX_CLIENT_CONN: 1000
    PGBOUNCER_DEFAULT_POOL_SIZE: 25
```

### Auto-Scaling Triggers

Monitor these metrics for auto-scaling decisions:

| Metric | Scale Up When | Scale Down When |
|--------|---------------|-----------------|
| CPU Usage | > 70% for 5 min | < 30% for 15 min |
| Memory Usage | > 80% for 5 min | < 40% for 15 min |
| Request Queue | > 100 requests | < 10 requests |
| Response Time | > 2 seconds | < 500ms |

---

## Monitoring Setup

### Prometheus Configuration

#### 1. Install Prometheus

```bash
# Create prometheus.yml
cat > prometheus.yml <<EOF
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'residency-scheduler'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
EOF
```

#### 2. Add to Docker Compose

```yaml
# docker-compose.monitoring.yml
services:
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    networks:
      - app-network

  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards
    depends_on:
      - prometheus
    networks:
      - app-network

volumes:
  prometheus_data:
  grafana_data:
```

### Key Metrics to Monitor

#### Application Metrics

```python
# Already instrumented in backend/app/resilience/metrics.py
- resilience_defense_level (Gauge)
- resilience_utilization_rate (Gauge)
- resilience_faculty_availability (Gauge)
- resilience_contingency_violations (Counter)
- resilience_health_checks (Counter)
- resilience_task_duration (Histogram)
```

#### System Metrics

- **CPU Usage**: `rate(process_cpu_seconds_total[5m])`
- **Memory Usage**: `process_resident_memory_bytes`
- **Request Rate**: `rate(http_requests_total[1m])`
- **Error Rate**: `rate(http_requests_total{status=~"5.."}[1m])`
- **Response Time**: `http_request_duration_seconds`

#### Database Metrics

- **Active Connections**: `pg_stat_activity_count`
- **Query Duration**: `pg_stat_statements_mean_time`
- **Database Size**: `pg_database_size_bytes`
- **Transaction Rate**: `pg_stat_database_xact_commit`

#### Celery Metrics

- **Active Tasks**: `celery_active_tasks`
- **Queue Length**: `celery_queue_length`
- **Task Success Rate**: `celery_task_success_total / celery_task_total`
- **Task Duration**: `celery_task_runtime_seconds`

### Grafana Dashboards

#### Import Pre-built Dashboards

```bash
# Resilience Dashboard (Custom)
# Import via Grafana UI: dashboards/resilience_dashboard.json

# PostgreSQL Dashboard (ID: 9628)
# Redis Dashboard (ID: 11835)
# Docker Dashboard (ID: 193)
```

### Alerting Rules

```yaml
# prometheus/alerts.yml
groups:
  - name: resilience
    interval: 30s
    rules:
      - alert: HighDefenseLevel
        expr: resilience_defense_level >= 3
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Defense level elevated to {{ $value }}"

      - alert: HighUtilization
        expr: resilience_utilization_rate > 0.9
        for: 10m
        labels:
          severity: critical
        annotations:
          summary: "Utilization rate at {{ $value }}"

      - alert: ServiceDown
        expr: up{job="residency-scheduler"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Service {{ $labels.instance }} is down"

      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Error rate > 5% on {{ $labels.instance }}"
```

### Log Aggregation

#### Option 1: ELK Stack (Elasticsearch, Logstash, Kibana)

```yaml
# docker-compose.logging.yml
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data

  logstash:
    image: docker.elastic.co/logstash/logstash:8.11.0
    volumes:
      - ./logstash/pipeline:/usr/share/logstash/pipeline
    depends_on:
      - elasticsearch

  kibana:
    image: docker.elastic.co/kibana/kibana:8.11.0
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch
```

#### Option 2: Loki + Promtail (Lightweight)

```yaml
services:
  loki:
    image: grafana/loki:latest
    ports:
      - "3100:3100"
    volumes:
      - loki_data:/loki

  promtail:
    image: grafana/promtail:latest
    volumes:
      - /var/log:/var/log
      - ./promtail-config.yml:/etc/promtail/config.yml
    command: -config.file=/etc/promtail/config.yml
```

---

## Backup and Recovery

### Backup Strategy

#### 1. Database Backups

**Automated Daily Backups**:
```bash
# Cron job (runs at 2 AM daily)
0 2 * * * /opt/residency-scheduler/scripts/backup-db.sh --docker --retention 30
```

**Manual Backup**:
```bash
./scripts/backup-db.sh --docker
```

**Backup to S3**:
```bash
# Set environment variables
export AWS_ACCESS_KEY_ID=<key>
export AWS_SECRET_ACCESS_KEY=<secret>
export S3_BUCKET=residency-scheduler-backups

# Run backup with S3 upload
./scripts/backup-db.sh --docker --s3
```

#### 2. Volume Backups

```bash
# Backup Docker volumes
docker run --rm \
  -v residency-scheduler_postgres_data:/data \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/postgres_volume_$(date +%Y%m%d).tar.gz -C /data .
```

#### 3. Configuration Backups

```bash
# Backup configuration files
tar czf config_backup_$(date +%Y%m%d).tar.gz \
  .env \
  docker-compose.yml \
  docker-compose.prod.yml \
  nginx/
```

### Recovery Procedures

#### Database Recovery

```bash
# 1. Stop services
docker compose down

# 2. Restore from backup
BACKUP_FILE="backups/postgres/residency_scheduler_20241217_020000.sql.gz"
gunzip -c "$BACKUP_FILE" | docker compose exec -T db psql -U scheduler -d residency_scheduler

# 3. Restart services
docker compose up -d

# 4. Verify
./scripts/health-check.sh --docker
```

#### Full System Recovery

```bash
# 1. Restore configuration
tar xzf config_backup_20241217.tar.gz

# 2. Restore volumes
docker run --rm \
  -v residency-scheduler_postgres_data:/data \
  -v $(pwd)/backups:/backup \
  alpine tar xzf /backup/postgres_volume_20241217.tar.gz -C /data

# 3. Start services
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 4. Verify all services
./scripts/health-check.sh --docker --verbose
```

### Backup Testing

```bash
# Test restore monthly
# 1. Create test environment
docker compose -f docker-compose.test.yml up -d

# 2. Restore latest backup
./scripts/backup-db.sh --docker  # Create fresh backup
# ... restore to test environment ...

# 3. Verify data integrity
docker compose -f docker-compose.test.yml exec backend python scripts/verify_data.py

# 4. Cleanup
docker compose -f docker-compose.test.yml down -v
```

---

## Security Considerations

### 1. Network Security

#### Firewall Configuration
```bash
# Production firewall rules
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
```

#### Docker Network Isolation
```yaml
# Separate networks for different layers
networks:
  frontend-network:
    internal: false
  backend-network:
    internal: true
  database-network:
    internal: true
```

### 2. SSL/TLS Configuration

#### Let's Encrypt with Certbot
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d scheduler.example.com

# Auto-renewal is configured automatically
```

#### Nginx SSL Configuration
```nginx
# Strong SSL configuration
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256';
ssl_prefer_server_ciphers on;
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;
ssl_stapling on;
ssl_stapling_verify on;

# Security headers
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
```

### 3. Access Control

#### Database Security
```sql
-- Revoke public access
REVOKE ALL ON SCHEMA public FROM PUBLIC;

-- Grant specific permissions
GRANT USAGE ON SCHEMA public TO scheduler;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO scheduler;

-- Enable SSL connections only
ALTER SYSTEM SET ssl = on;
```

#### Redis Security
```bash
# redis.conf
requirepass <strong-password>
rename-command FLUSHDB ""
rename-command FLUSHALL ""
rename-command CONFIG ""
maxmemory-policy allkeys-lru
```

### 4. Secrets Management

```bash
# Use Docker secrets in production
echo "my_db_password" | docker secret create db_password -

# Reference in compose file
services:
  backend:
    secrets:
      - db_password
    environment:
      DB_PASSWORD_FILE: /run/secrets/db_password

secrets:
  db_password:
    external: true
```

### 5. Security Scanning

```bash
# Scan Docker images for vulnerabilities
docker scan residency-scheduler-backend:latest

# Audit Python dependencies
pip install safety
safety check -r requirements.txt

# Audit npm dependencies
npm audit
```

---

## Performance Tuning

### Database Optimization

```sql
-- Enable query logging
ALTER SYSTEM SET log_min_duration_statement = 1000;  -- Log queries > 1s

-- Increase shared buffers (25% of RAM)
ALTER SYSTEM SET shared_buffers = '2GB';

-- Increase work memory
ALTER SYSTEM SET work_mem = '64MB';

-- Enable auto-vacuum
ALTER SYSTEM SET autovacuum = on;

-- Create indexes on frequently queried columns
CREATE INDEX idx_assignments_faculty_id ON assignments(faculty_id);
CREATE INDEX idx_assignments_date ON assignments(date);
```

### Redis Optimization

```bash
# redis.conf
maxmemory 1gb
maxmemory-policy allkeys-lru
save ""  # Disable RDB snapshots (use AOF only)
appendonly yes
appendfsync everysec
```

### Backend Optimization

```python
# Use connection pooling
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True
)

# Enable caching
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
```

### Celery Optimization

```python
# Increase concurrency
CELERY_WORKER_CONCURRENCY = os.cpu_count() * 2

# Task routing for optimization
task_routes = {
    'app.resilience.tasks.*': {'queue': 'resilience'},
    'app.notifications.tasks.*': {'queue': 'notifications'},
}

# Prefetch multiplier
worker_prefetch_multiplier = 1  # For long-running tasks
```

---

## Disaster Recovery

### RPO and RTO Targets

| Scenario | RPO | RTO | Strategy |
|----------|-----|-----|----------|
| Database corruption | 1 hour | 4 hours | Hourly backups, PITR |
| Service failure | 0 minutes | 15 minutes | Auto-restart, health checks |
| Data center outage | 24 hours | 8 hours | Multi-region deployment |
| Complete system loss | 24 hours | 24 hours | Backup restoration |

### Multi-Region Deployment

```yaml
# Example: AWS multi-region setup
Primary Region (us-east-1):
  - Active application servers
  - Primary database (RDS Multi-AZ)
  - Redis cluster

Secondary Region (us-west-2):
  - Standby application servers
  - Read replica database
  - Redis replica

Failover Process:
  1. Detect primary region failure
  2. Promote read replica to master
  3. Update DNS to point to secondary region
  4. Start application servers in secondary region
```

### Testing Disaster Recovery

```bash
# Quarterly DR drill
# 1. Schedule maintenance window
# 2. Simulate failure (stop primary region)
# 3. Execute failover procedure
# 4. Verify all services operational
# 5. Test critical user workflows
# 6. Document issues and improve
```

---

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [PostgreSQL Performance](https://www.postgresql.org/docs/current/performance-tips.html)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/naming/)
- [Celery Documentation](https://docs.celeryproject.org/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)

---

**Last Updated**: 2024-12-17
**Version**: 1.0
**Maintained By**: Infrastructure Team
**Review Frequency**: Quarterly
