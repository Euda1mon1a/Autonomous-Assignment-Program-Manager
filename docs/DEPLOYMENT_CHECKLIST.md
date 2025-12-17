# Deployment Checklist

## Overview

This checklist ensures a safe and successful deployment of the Residency Scheduler application to production. Follow these steps in order and verify each before proceeding.

**Critical**: Always deploy during maintenance windows and have a rollback plan ready.

---

## Pre-Deployment Checklist

### 1. Code Preparation

- [ ] All code merged to main branch and reviewed
- [ ] All tests passing (`pytest` in backend, `npm test` in frontend)
- [ ] Linting passes (`ruff check` and `mypy` in backend)
- [ ] No known critical bugs
- [ ] Version number updated in appropriate files
- [ ] CHANGELOG.md updated with release notes

### 2. Environment Configuration

- [ ] `.env` file created with production values
- [ ] All required environment variables set (see [Environment Variables](#environment-variables) below)
- [ ] Secret key generated (256-bit, cryptographically secure)
- [ ] Database password set (strong, unique)
- [ ] CORS origins configured for production domain(s)
- [ ] Debug mode disabled (`DEBUG=false`)
- [ ] Sensitive data removed from version control

### 3. Infrastructure Verification

- [ ] Server/VM provisioned with adequate resources
  - Minimum: 2 CPU cores, 4 GB RAM, 20 GB storage
  - Recommended: 4 CPU cores, 8 GB RAM, 50 GB storage
- [ ] Docker and Docker Compose installed (20.10+, 2.0+)
- [ ] SSL certificates obtained (Let's Encrypt or commercial)
- [ ] Domain DNS configured and propagated
- [ ] Firewall rules configured (ports 80, 443 open)
- [ ] Backup storage configured

### 4. Database Preparation

- [ ] Database backup of current production (if upgrading)
- [ ] Database migration files reviewed
- [ ] Migration tested in staging environment
- [ ] Database rollback plan documented

### 5. Security Review

- [ ] Security headers configured in Nginx
- [ ] Rate limiting enabled
- [ ] SQL injection protections verified
- [ ] XSS protections verified
- [ ] CSRF protections enabled
- [ ] Authentication mechanisms tested
- [ ] Authorization rules verified
- [ ] Secrets management reviewed (no hardcoded credentials)

---

## Environment Variables Reference

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DB_PASSWORD` | PostgreSQL password | `secure_random_password_123` |
| `SECRET_KEY` | JWT signing key (256-bit) | `generate_with_openssl_or_python` |
| `CORS_ORIGINS` | Allowed CORS origins | `["https://scheduler.example.com"]` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Full database connection string | Built from components |
| `REDIS_URL` | Redis connection URL | `redis://redis:6379/0` |
| `DEBUG` | Debug mode (MUST be false) | `false` |
| `LOG_LEVEL` | Logging level | `info` |
| `NEXT_PUBLIC_API_URL` | Frontend API URL | `http://localhost:8000` |
| `TRUSTED_HOSTS` | Allowed host headers | `["*"]` |
| `RATE_LIMIT_ENABLED` | Enable rate limiting | `true` |
| `CELERY_WORKER_CONCURRENCY` | Celery worker threads | `4` |
| `BACKUP_RETENTION_DAYS` | Backup retention period | `30` |

### Generate Secret Key

```bash
# Using Python
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Using OpenSSL
openssl rand -base64 32
```

---

## Deployment Steps

### Step 1: Prepare Server

```bash
# SSH into server
ssh user@production-server

# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Docker (if not already installed)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt install docker-compose-plugin

# Verify installations
docker --version
docker compose version
```

### Step 2: Deploy Application Code

```bash
# Clone repository
git clone <repository-url> /opt/residency-scheduler
cd /opt/residency-scheduler

# Checkout specific version/tag
git checkout v1.0.0  # or specific commit hash

# Verify correct branch/tag
git log -1
```

### Step 3: Configure Environment

```bash
# Create .env file
cp .env.example .env

# Edit with production values
nano .env

# Set proper permissions
chmod 600 .env

# Verify no sensitive data in git
git status
```

### Step 4: Database Migration

```bash
# Build backend image first
docker compose -f docker-compose.yml -f docker-compose.prod.yml build backend

# Start database only
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d db

# Wait for database to be healthy
docker compose ps

# Run migrations
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec backend alembic upgrade head

# Verify migration success
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec backend alembic current
```

### Step 5: Start All Services

```bash
# Build all images
docker compose -f docker-compose.yml -f docker-compose.prod.yml build

# Start all services
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Monitor startup
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f
```

### Step 6: Service Startup Order

**Critical**: Services must start in this order to satisfy dependencies:

1. **Database (db)** - Wait for healthy status
2. **Redis** - Wait for healthy status
3. **Backend** - Wait for healthy status
4. **Celery Worker** - Depends on db + redis
5. **Celery Beat** - Depends on db + redis
6. **Frontend** - Depends on backend
7. **Nginx** (if using) - Last to start

Docker Compose handles this automatically with `depends_on` and health checks.

---

## Post-Deployment Verification

### 1. Health Checks

```bash
# Run comprehensive health check
./scripts/health-check.sh --docker --verbose

# Expected output: All services HEALTHY
```

### 2. Service Status

```bash
# Check all containers are running
docker compose ps

# Expected: All services "Up" with "(healthy)" status
```

### 3. API Verification

```bash
# Test backend health endpoint
curl https://scheduler.example.com/health

# Expected: {"status": "ok", "database": "connected", ...}

# Test resilience endpoint
curl https://scheduler.example.com/health/resilience

# Expected: {..., "defense_level": "GREEN", ...}

# Test API documentation
curl https://scheduler.example.com/docs

# Expected: HTML page with API documentation
```

### 4. Frontend Verification

```bash
# Test frontend
curl -I https://scheduler.example.com

# Expected: HTTP 200 OK

# Check in browser
# - Visit https://scheduler.example.com
# - Verify login page loads
# - Test login functionality
# - Check console for errors
```

### 5. Celery Verification

```bash
# Check Celery workers
docker compose exec celery-worker celery -A app.core.celery_app inspect active

# Expected: List of active workers

# Check Celery beat schedule
docker compose exec celery-beat celery -A app.core.celery_app inspect scheduled

# Expected: List of scheduled tasks
```

### 6. Database Verification

```bash
# Connect to database
docker compose exec db psql -U scheduler -d residency_scheduler

# Run verification queries
SELECT COUNT(*) FROM alembic_version;  -- Should show current version
SELECT COUNT(*) FROM users;            -- Should show expected user count
\q

# Test database backup
./scripts/backup-db.sh --docker

# Expected: Backup file created in ./backups/postgres/
```

### 7. Log Review

```bash
# Review logs for errors
docker compose logs --tail=100 backend
docker compose logs --tail=100 celery-worker
docker compose logs --tail=100 celery-beat

# Look for:
# - No ERROR or CRITICAL messages
# - Successful startup messages
# - No connection errors
```

### 8. Performance Testing

```bash
# Test response time
time curl https://scheduler.example.com/health

# Expected: < 500ms

# Load test (optional, use Apache Bench)
ab -n 100 -c 10 https://scheduler.example.com/health

# Review metrics
curl https://scheduler.example.com/metrics
```

---

## Monitoring Setup

### 1. Configure Health Check Monitoring

```bash
# Add to crontab for automated checks
crontab -e

# Add line:
*/5 * * * * /opt/residency-scheduler/scripts/health-check.sh --docker || echo "Health check failed" | mail -s "Alert: Service Unhealthy" admin@example.com
```

### 2. Set Up Automated Backups

```bash
# Add to crontab
crontab -e

# Add line (daily at 2 AM):
0 2 * * * /opt/residency-scheduler/scripts/backup-db.sh --docker --retention 30
```

### 3. Log Rotation

```bash
# Create logrotate config
sudo nano /etc/logrotate.d/residency-scheduler

# Add configuration:
/var/lib/docker/containers/*/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    sharedscripts
    postrotate
        docker kill --signal=USR1 $(docker ps -q) 2>/dev/null || true
    endscript
}
```

### 4. Prometheus/Grafana (Optional but Recommended)

See `INFRASTRUCTURE_GUIDE.md` for detailed setup instructions.

---

## Rollback Procedures

### When to Rollback

Rollback immediately if:
- Critical bugs discovered in production
- Database migration fails
- Services won't start
- Security vulnerability detected
- Data corruption detected

### Rollback Steps

#### 1. Quick Rollback (No Database Changes)

```bash
# Stop current services
docker compose down

# Checkout previous version
git checkout v0.9.0  # previous stable version

# Restart services
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Verify
./scripts/health-check.sh --docker
```

#### 2. Full Rollback (With Database Restore)

```bash
# Stop all services
docker compose down

# Restore database from backup
BACKUP_FILE="backups/postgres/residency_scheduler_20241217_020000.sql.gz"
gunzip -c "$BACKUP_FILE" | docker compose exec -T db psql -U scheduler -d residency_scheduler

# Rollback code
git checkout v0.9.0

# Downgrade database (if needed)
docker compose exec backend alembic downgrade <revision>

# Restart services
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Verify
./scripts/health-check.sh --docker
```

#### 3. Emergency Shutdown

```bash
# Stop all services immediately
docker compose down

# Or kill individual service
docker compose stop backend

# Check status
docker compose ps
```

### Rollback Verification

After rollback:

- [ ] All services started successfully
- [ ] Health checks passing
- [ ] Database integrity verified
- [ ] User logins working
- [ ] Critical features functional
- [ ] Logs reviewed for errors
- [ ] Stakeholders notified

---

## Troubleshooting Common Issues

### Issue: Database Migration Fails

```bash
# Check current migration state
docker compose exec backend alembic current

# Check migration history
docker compose exec backend alembic history

# Manually fix and retry
docker compose exec backend alembic upgrade head

# If stuck, mark as resolved
docker compose exec backend alembic stamp head
```

### Issue: Container Won't Start

```bash
# Check detailed logs
docker compose logs --tail=200 <service-name>

# Rebuild without cache
docker compose build --no-cache <service-name>

# Check resource usage
docker stats

# Check disk space
df -h
```

### Issue: Connection Refused

```bash
# Check if service is listening
docker compose exec backend netstat -tlnp

# Check network connectivity
docker compose exec frontend ping backend

# Verify environment variables
docker compose exec backend env | grep DATABASE_URL
```

### Issue: Celery Tasks Not Running

```bash
# Check worker is connected
docker compose exec celery-worker celery -A app.core.celery_app inspect active

# Check Redis connection
docker compose exec celery-worker python -c "import redis; r = redis.from_url('redis://redis:6379/0'); print(r.ping())"

# Restart workers
docker compose restart celery-worker celery-beat
```

---

## Post-Deployment Tasks

### Immediate (Within 24 Hours)

- [ ] Monitor error logs continuously
- [ ] Verify automated backups running
- [ ] Test critical user workflows
- [ ] Monitor performance metrics
- [ ] Document any issues encountered

### Within 1 Week

- [ ] Review user feedback
- [ ] Analyze performance metrics
- [ ] Optimize slow queries (if any)
- [ ] Update documentation with lessons learned
- [ ] Plan next iteration

### Within 1 Month

- [ ] Security audit
- [ ] Performance tuning
- [ ] Test backup restoration procedure
- [ ] Review and update monitoring alerts
- [ ] Capacity planning review

---

## Emergency Contacts

| Role | Name | Contact | Availability |
|------|------|---------|--------------|
| System Admin | [Name] | [Email/Phone] | 24/7 |
| Database Admin | [Name] | [Email/Phone] | Business Hours |
| Developer Lead | [Name] | [Email/Phone] | On-call |
| Security Team | [Name] | [Email/Phone] | 24/7 |

---

## Additional Resources

- [INFRASTRUCTURE_GUIDE.md](./INFRASTRUCTURE_GUIDE.md) - Architecture and scaling
- [DEPLOYMENT.md](./DEPLOYMENT.md) - Detailed deployment procedures
- [TODO_RESILIENCE.md](./TODO_RESILIENCE.md) - Resilience framework tasks
- [ARCHITECTURE.md](./ARCHITECTURE.md) - System architecture overview

---

**Last Updated**: 2024-12-17
**Version**: 1.0
**Maintained By**: Infrastructure Team
