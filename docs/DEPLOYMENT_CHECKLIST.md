***REMOVED*** Deployment Checklist

***REMOVED******REMOVED*** Overview

This checklist ensures a safe and successful deployment of the Residency Scheduler application to production. Follow these steps in order and verify each before proceeding.

**Critical**: Always deploy during maintenance windows and have a rollback plan ready.

---

***REMOVED******REMOVED*** Pre-Deployment Checklist

***REMOVED******REMOVED******REMOVED*** 1. Code Preparation

- [ ] All code merged to main branch and reviewed
- [ ] All tests passing (`pytest` in backend, `npm test` in frontend)
- [ ] Linting passes (`ruff check` and `mypy` in backend)
- [ ] No known critical bugs
- [ ] Version number updated in appropriate files
- [ ] CHANGELOG.md updated with release notes

***REMOVED******REMOVED******REMOVED*** 2. Environment Configuration

- [ ] `.env` file created with production values
- [ ] All required environment variables set (see [Environment Variables](***REMOVED***environment-variables) below)
- [ ] Secret key generated (256-bit, cryptographically secure)
- [ ] Database password set (strong, unique)
- [ ] CORS origins configured for production domain(s)
- [ ] Debug mode disabled (`DEBUG=false`)
- [ ] Sensitive data removed from version control

***REMOVED******REMOVED******REMOVED*** 3. Infrastructure Verification

- [ ] Server/VM provisioned with adequate resources
  - Minimum: 2 CPU cores, 4 GB RAM, 20 GB storage
  - Recommended: 4 CPU cores, 8 GB RAM, 50 GB storage
- [ ] Docker and Docker Compose installed (20.10+, 2.0+)
- [ ] SSL certificates obtained (Let's Encrypt or commercial)
- [ ] Domain DNS configured and propagated
- [ ] Firewall rules configured (ports 80, 443 open)
- [ ] Backup storage configured

***REMOVED******REMOVED******REMOVED*** 4. Database Preparation

- [ ] Database backup of current production (if upgrading)
- [ ] Database migration files reviewed
- [ ] Migration tested in staging environment
- [ ] Database rollback plan documented

***REMOVED******REMOVED******REMOVED*** 5. Security Review

- [ ] Security headers configured in Nginx
- [ ] Rate limiting enabled
- [ ] SQL injection protections verified
- [ ] XSS protections verified
- [ ] CSRF protections enabled
- [ ] Authentication mechanisms tested
- [ ] Authorization rules verified
- [ ] Secrets management reviewed (no hardcoded credentials)

---

***REMOVED******REMOVED*** Environment Variables Reference

***REMOVED******REMOVED******REMOVED*** Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DB_PASSWORD` | PostgreSQL password | `secure_random_password_123` |
| `SECRET_KEY` | JWT signing key (256-bit) | `generate_with_openssl_or_python` |
| `CORS_ORIGINS` | Allowed CORS origins | `["https://scheduler.example.com"]` |

***REMOVED******REMOVED******REMOVED*** Optional Variables

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

***REMOVED******REMOVED******REMOVED*** Generate Secret Key

```bash
***REMOVED*** Using Python
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

***REMOVED*** Using OpenSSL
openssl rand -base64 32
```

---

***REMOVED******REMOVED*** Deployment Steps

***REMOVED******REMOVED******REMOVED*** Step 1: Prepare Server

```bash
***REMOVED*** SSH into server
ssh user@production-server

***REMOVED*** Update system packages
sudo apt update && sudo apt upgrade -y

***REMOVED*** Install Docker (if not already installed)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

***REMOVED*** Install Docker Compose
sudo apt install docker-compose-plugin

***REMOVED*** Verify installations
docker --version
docker compose version
```

***REMOVED******REMOVED******REMOVED*** Step 2: Deploy Application Code

```bash
***REMOVED*** Clone repository
git clone <repository-url> /opt/residency-scheduler
cd /opt/residency-scheduler

***REMOVED*** Checkout specific version/tag
git checkout v1.0.0  ***REMOVED*** or specific commit hash

***REMOVED*** Verify correct branch/tag
git log -1
```

***REMOVED******REMOVED******REMOVED*** Step 3: Configure Environment

```bash
***REMOVED*** Create .env file
cp .env.example .env

***REMOVED*** Edit with production values
nano .env

***REMOVED*** Set proper permissions
chmod 600 .env

***REMOVED*** Verify no sensitive data in git
git status
```

***REMOVED******REMOVED******REMOVED*** Step 4: Database Migration

```bash
***REMOVED*** Build backend image first
docker compose -f docker-compose.yml -f docker-compose.prod.yml build backend

***REMOVED*** Start database only
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d db

***REMOVED*** Wait for database to be healthy
docker compose ps

***REMOVED*** Run migrations
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec backend alembic upgrade head

***REMOVED*** Verify migration success
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec backend alembic current
```

***REMOVED******REMOVED******REMOVED*** Step 5: Start All Services

```bash
***REMOVED*** Build all images
docker compose -f docker-compose.yml -f docker-compose.prod.yml build

***REMOVED*** Start all services
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

***REMOVED*** Monitor startup
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f
```

***REMOVED******REMOVED******REMOVED*** Step 6: Service Startup Order

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

***REMOVED******REMOVED*** Post-Deployment Verification

***REMOVED******REMOVED******REMOVED*** 1. Health Checks

```bash
***REMOVED*** Run comprehensive health check
./scripts/health-check.sh --docker --verbose

***REMOVED*** Expected output: All services HEALTHY
```

***REMOVED******REMOVED******REMOVED*** 2. Service Status

```bash
***REMOVED*** Check all containers are running
docker compose ps

***REMOVED*** Expected: All services "Up" with "(healthy)" status
```

***REMOVED******REMOVED******REMOVED*** 3. API Verification

```bash
***REMOVED*** Test backend health endpoint
curl https://scheduler.example.com/health

***REMOVED*** Expected: {"status": "ok", "database": "connected", ...}

***REMOVED*** Test resilience endpoint
curl https://scheduler.example.com/health/resilience

***REMOVED*** Expected: {..., "defense_level": "GREEN", ...}

***REMOVED*** Test API documentation
curl https://scheduler.example.com/docs

***REMOVED*** Expected: HTML page with API documentation
```

***REMOVED******REMOVED******REMOVED*** 4. Frontend Verification

```bash
***REMOVED*** Test frontend
curl -I https://scheduler.example.com

***REMOVED*** Expected: HTTP 200 OK

***REMOVED*** Check in browser
***REMOVED*** - Visit https://scheduler.example.com
***REMOVED*** - Verify login page loads
***REMOVED*** - Test login functionality
***REMOVED*** - Check console for errors
```

***REMOVED******REMOVED******REMOVED*** 5. Celery Verification

```bash
***REMOVED*** Check Celery workers
docker compose exec celery-worker celery -A app.core.celery_app inspect active

***REMOVED*** Expected: List of active workers

***REMOVED*** Check Celery beat schedule
docker compose exec celery-beat celery -A app.core.celery_app inspect scheduled

***REMOVED*** Expected: List of scheduled tasks
```

***REMOVED******REMOVED******REMOVED*** 6. Database Verification

```bash
***REMOVED*** Connect to database
docker compose exec db psql -U scheduler -d residency_scheduler

***REMOVED*** Run verification queries
SELECT COUNT(*) FROM alembic_version;  -- Should show current version
SELECT COUNT(*) FROM users;            -- Should show expected user count
\q

***REMOVED*** Test database backup
./scripts/backup-db.sh --docker

***REMOVED*** Expected: Backup file created in ./backups/postgres/
```

***REMOVED******REMOVED******REMOVED*** 7. Log Review

```bash
***REMOVED*** Review logs for errors
docker compose logs --tail=100 backend
docker compose logs --tail=100 celery-worker
docker compose logs --tail=100 celery-beat

***REMOVED*** Look for:
***REMOVED*** - No ERROR or CRITICAL messages
***REMOVED*** - Successful startup messages
***REMOVED*** - No connection errors
```

***REMOVED******REMOVED******REMOVED*** 8. Performance Testing

```bash
***REMOVED*** Test response time
time curl https://scheduler.example.com/health

***REMOVED*** Expected: < 500ms

***REMOVED*** Load test (optional, use Apache Bench)
ab -n 100 -c 10 https://scheduler.example.com/health

***REMOVED*** Review metrics
curl https://scheduler.example.com/metrics
```

---

***REMOVED******REMOVED*** Monitoring Setup

***REMOVED******REMOVED******REMOVED*** 1. Configure Health Check Monitoring

```bash
***REMOVED*** Add to crontab for automated checks
crontab -e

***REMOVED*** Add line:
*/5 * * * * /opt/residency-scheduler/scripts/health-check.sh --docker || echo "Health check failed" | mail -s "Alert: Service Unhealthy" admin@example.com
```

***REMOVED******REMOVED******REMOVED*** 2. Set Up Automated Backups

```bash
***REMOVED*** Add to crontab
crontab -e

***REMOVED*** Add line (daily at 2 AM):
0 2 * * * /opt/residency-scheduler/scripts/backup-db.sh --docker --retention 30
```

***REMOVED******REMOVED******REMOVED*** 3. Log Rotation

```bash
***REMOVED*** Create logrotate config
sudo nano /etc/logrotate.d/residency-scheduler

***REMOVED*** Add configuration:
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

***REMOVED******REMOVED******REMOVED*** 4. Prometheus/Grafana (Optional but Recommended)

See `INFRASTRUCTURE_GUIDE.md` for detailed setup instructions.

---

***REMOVED******REMOVED*** Rollback Procedures

***REMOVED******REMOVED******REMOVED*** When to Rollback

Rollback immediately if:
- Critical bugs discovered in production
- Database migration fails
- Services won't start
- Security vulnerability detected
- Data corruption detected

***REMOVED******REMOVED******REMOVED*** Rollback Steps

***REMOVED******REMOVED******REMOVED******REMOVED*** 1. Quick Rollback (No Database Changes)

```bash
***REMOVED*** Stop current services
docker compose down

***REMOVED*** Checkout previous version
git checkout v0.9.0  ***REMOVED*** previous stable version

***REMOVED*** Restart services
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

***REMOVED*** Verify
./scripts/health-check.sh --docker
```

***REMOVED******REMOVED******REMOVED******REMOVED*** 2. Full Rollback (With Database Restore)

```bash
***REMOVED*** Stop all services
docker compose down

***REMOVED*** Restore database from backup
BACKUP_FILE="backups/postgres/residency_scheduler_20241217_020000.sql.gz"
gunzip -c "$BACKUP_FILE" | docker compose exec -T db psql -U scheduler -d residency_scheduler

***REMOVED*** Rollback code
git checkout v0.9.0

***REMOVED*** Downgrade database (if needed)
docker compose exec backend alembic downgrade <revision>

***REMOVED*** Restart services
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

***REMOVED*** Verify
./scripts/health-check.sh --docker
```

***REMOVED******REMOVED******REMOVED******REMOVED*** 3. Emergency Shutdown

```bash
***REMOVED*** Stop all services immediately
docker compose down

***REMOVED*** Or kill individual service
docker compose stop backend

***REMOVED*** Check status
docker compose ps
```

***REMOVED******REMOVED******REMOVED*** Rollback Verification

After rollback:

- [ ] All services started successfully
- [ ] Health checks passing
- [ ] Database integrity verified
- [ ] User logins working
- [ ] Critical features functional
- [ ] Logs reviewed for errors
- [ ] Stakeholders notified

---

***REMOVED******REMOVED*** Troubleshooting Common Issues

***REMOVED******REMOVED******REMOVED*** Issue: Database Migration Fails

```bash
***REMOVED*** Check current migration state
docker compose exec backend alembic current

***REMOVED*** Check migration history
docker compose exec backend alembic history

***REMOVED*** Manually fix and retry
docker compose exec backend alembic upgrade head

***REMOVED*** If stuck, mark as resolved
docker compose exec backend alembic stamp head
```

***REMOVED******REMOVED******REMOVED*** Issue: Container Won't Start

```bash
***REMOVED*** Check detailed logs
docker compose logs --tail=200 <service-name>

***REMOVED*** Rebuild without cache
docker compose build --no-cache <service-name>

***REMOVED*** Check resource usage
docker stats

***REMOVED*** Check disk space
df -h
```

***REMOVED******REMOVED******REMOVED*** Issue: Connection Refused

```bash
***REMOVED*** Check if service is listening
docker compose exec backend netstat -tlnp

***REMOVED*** Check network connectivity
docker compose exec frontend ping backend

***REMOVED*** Verify environment variables
docker compose exec backend env | grep DATABASE_URL
```

***REMOVED******REMOVED******REMOVED*** Issue: Celery Tasks Not Running

```bash
***REMOVED*** Check worker is connected
docker compose exec celery-worker celery -A app.core.celery_app inspect active

***REMOVED*** Check Redis connection
docker compose exec celery-worker python -c "import redis; r = redis.from_url('redis://redis:6379/0'); print(r.ping())"

***REMOVED*** Restart workers
docker compose restart celery-worker celery-beat
```

---

***REMOVED******REMOVED*** Post-Deployment Tasks

***REMOVED******REMOVED******REMOVED*** Immediate (Within 24 Hours)

- [ ] Monitor error logs continuously
- [ ] Verify automated backups running
- [ ] Test critical user workflows
- [ ] Monitor performance metrics
- [ ] Document any issues encountered

***REMOVED******REMOVED******REMOVED*** Within 1 Week

- [ ] Review user feedback
- [ ] Analyze performance metrics
- [ ] Optimize slow queries (if any)
- [ ] Update documentation with lessons learned
- [ ] Plan next iteration

***REMOVED******REMOVED******REMOVED*** Within 1 Month

- [ ] Security audit
- [ ] Performance tuning
- [ ] Test backup restoration procedure
- [ ] Review and update monitoring alerts
- [ ] Capacity planning review

---

***REMOVED******REMOVED*** Emergency Contacts

| Role | Name | Contact | Availability |
|------|------|---------|--------------|
| System Admin | [Name] | [Email/Phone] | 24/7 |
| Database Admin | [Name] | [Email/Phone] | Business Hours |
| Developer Lead | [Name] | [Email/Phone] | On-call |
| Security Team | [Name] | [Email/Phone] | 24/7 |

---

***REMOVED******REMOVED*** Additional Resources

- [INFRASTRUCTURE_GUIDE.md](./INFRASTRUCTURE_GUIDE.md) - Architecture and scaling
- [DEPLOYMENT.md](./DEPLOYMENT.md) - Detailed deployment procedures
- [TODO_RESILIENCE.md](./TODO_RESILIENCE.md) - Resilience framework tasks
- [ARCHITECTURE.md](./ARCHITECTURE.md) - System architecture overview

---

**Last Updated**: 2024-12-17
**Version**: 1.0
**Maintained By**: Infrastructure Team
