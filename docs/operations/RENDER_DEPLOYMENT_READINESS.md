# Render Deployment Readiness Assessment

> **Last Updated:** 2025-12-30
> **Status:** READY WITH CAVEATS
> **Assessed By:** Claude Code Session (claude/assess-docker-render-readiness-ubgDD)

---

## Executive Summary

The repository has a well-structured Render Blueprint (`render.yaml`) and production-ready Dockerfiles. The application can be deployed to Render, but several items need attention for production reliability.

---

## Current Configuration

### Render Blueprint Services (`render.yaml`)

| Service | Type | Runtime | Health Check | Plan |
|---------|------|---------|--------------|------|
| `residency-scheduler-frontend` | web | docker | `/` | starter |
| `residency-scheduler-backend` | web | docker | `/health` | starter |
| `residency-scheduler-worker` | worker | docker | N/A | starter |
| `residency-redis` | redis | managed | N/A | starter |
| `residency-db` | database | managed | N/A | starter |

### Dockerfile Quality

| Component | Base Image | Multi-stage | Non-root User | Size Optimized |
|-----------|------------|-------------|---------------|----------------|
| Backend | python:3.12-slim | Yes | Yes (appuser:1001) | Yes |
| Frontend | node:22-slim | Yes | Yes (nextjs:1001) | Yes (standalone) |

---

## Issues Requiring Attention

### Critical (Must Fix Before Production)

#### 1. Missing Celery Beat Scheduler

**Location:** `render.yaml`

**Problem:** No Celery Beat service defined. Scheduled tasks won't run.

**Affected Features:**
- Resilience health checks (every 15 min)
- N-1/N-2 contingency analysis (every 24 hours)
- Periodic compliance reports
- Cache cleanup tasks

**Fix:** Add to `render.yaml`:
```yaml
- type: worker
  name: residency-scheduler-beat
  runtime: docker
  dockerfilePath: ./backend/Dockerfile
  dockerContext: ./backend
  plan: starter
  envVars:
    - key: DATABASE_URL
      fromDatabase:
        name: residency-db
        property: connectionString
    - key: REDIS_URL
      fromService:
        name: residency-redis
        type: redis
        property: connectionString
    - key: CELERY_BROKER_URL
      fromService:
        name: residency-redis
        type: redis
        property: connectionString
    - key: CELERY_RESULT_BACKEND
      fromService:
        name: residency-redis
        type: redis
        property: connectionString
    - key: SECRET_KEY
      generateValue: true
    - key: DEBUG
      value: "false"
  dockerCommand: celery -A app.core.celery_app beat --loglevel=info
```

#### 2. Static Health Check Response

**Location:** `backend/app/main.py:405-411`

**Problem:** Health endpoint returns static `"database": "connected"` without verifying.

**Current Code:**
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "database": "connected",  # NOT ACTUALLY VERIFIED
    }
```

**Risk:** Render won't detect database connection failures, causing silent failures.

**Fix:** Implement actual database check:
```python
from sqlalchemy import text
from app.api.deps import get_db

@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        logger.error(f"Health check DB failure: {e}")
        raise HTTPException(status_code=503, detail="Database unavailable")

    return {"status": "healthy", "database": db_status}
```

### High Priority

#### 3. pgvector Extension Dependency

**Location:** `docker-compose.yml:7`

**Problem:** Local development uses `pgvector/pgvector:0.8.1-pg15` image. Render's managed PostgreSQL may not have pgvector extension installed.

**Affected Features:**
- RAG document search (`/api/v1/rag/*`)
- Vector similarity for scheduling preferences
- AI-assisted schedule explanations

**Options:**
1. **Verify Render PostgreSQL supports pgvector** (check their docs/support)
2. **Make pgvector optional** with graceful degradation
3. **Use external vector DB** (Pinecone, Weaviate) for production

**Graceful Degradation Pattern:**
```python
# backend/app/db/session.py
try:
    await db.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    PGVECTOR_AVAILABLE = True
except Exception:
    logger.warning("pgvector not available - RAG features disabled")
    PGVECTOR_AVAILABLE = False
```

#### 4. Manual Frontend API URL Configuration

**Location:** `render.yaml:19-22`

**Problem:** `NEXT_PUBLIC_API_URL` has `sync: false`, requiring manual post-deployment configuration.

**Current:**
```yaml
- key: NEXT_PUBLIC_API_URL
  sync: false  # Must set manually
```

**Impact:** Frontend won't connect to backend until admin manually sets this value in Render dashboard.

**Post-Deploy Step Required:**
1. Go to Render Dashboard > residency-scheduler-frontend > Environment
2. Set `NEXT_PUBLIC_API_URL` = `https://residency-scheduler-backend.onrender.com`
3. Trigger manual deploy or wait for next deploy

### Medium Priority

#### 5. Celery Queue Mismatch

**Problem:** Queue lists differ between environments.

| Source | Queues |
|--------|--------|
| `render.yaml` | `default,resilience,notifications,metrics` |
| `docker-compose.yml` | `default,resilience,notifications,metrics,exports,security` |

**Impact:** Tasks routed to `exports` or `security` queues won't be processed on Render.

**Fix:** Align queues in `render.yaml`:
```yaml
dockerCommand: celery -A app.core.celery_app worker --loglevel=info -Q default,resilience,notifications,metrics,exports,security
```

#### 6. Starter Plan Resource Limits

**Concern:** OR-Tools constraint solver is memory-intensive. Starter plan (512MB) may be insufficient for large schedules.

**Monitoring Required:**
- Watch for OOM kills during schedule generation
- Monitor worker memory usage

**Scaling Path:**
- Backend: Upgrade to Standard (2GB) if schedule generation fails
- Worker: Upgrade to Standard (2GB) for complex constraint solving

---

## Deployment Checklist

### Pre-Deployment

- [ ] Add Celery Beat service to `render.yaml`
- [ ] Fix `/health` endpoint to verify database connection
- [ ] Align Celery queue definitions
- [ ] Verify pgvector availability or implement fallback
- [ ] Review and update CORS_ORIGINS for production domain

### Post-Deployment

- [ ] Set `NEXT_PUBLIC_API_URL` in frontend environment
- [ ] Verify health checks are passing (Render Dashboard)
- [ ] Test database connectivity via `/health` endpoint
- [ ] Run smoke tests on critical endpoints
- [ ] Verify Celery worker is processing tasks
- [ ] Check scheduled tasks are running (after Beat is added)

### Monitoring Setup

- [ ] Configure Render notifications for deploy failures
- [ ] Set up external uptime monitoring (e.g., UptimeRobot)
- [ ] Configure log retention/export if needed
- [ ] Set up alerting for 5xx error spikes

---

## Environment Variables Reference

### Auto-Configured by Render

| Variable | Source | Service |
|----------|--------|---------|
| `DATABASE_URL` | `residency-db` connection string | backend, worker |
| `REDIS_URL` | `residency-redis` connection string | backend, worker |
| `CELERY_BROKER_URL` | `residency-redis` connection string | backend, worker |
| `CELERY_RESULT_BACKEND` | `residency-redis` connection string | backend, worker |
| `SECRET_KEY` | Auto-generated (32+ chars) | backend, worker |
| `WEBHOOK_SECRET` | Auto-generated (32+ chars) | backend |

### Manual Configuration Required

| Variable | Value | Service | Notes |
|----------|-------|---------|-------|
| `NEXT_PUBLIC_API_URL` | `https://residency-scheduler-backend.onrender.com` | frontend | Set after first deploy |

### Hardcoded in Blueprint

| Variable | Value | Service |
|----------|-------|---------|
| `DEBUG` | `false` | backend, worker |
| `ENVIRONMENT` | `production` | backend |
| `NODE_ENV` | `production` | frontend |
| `RATE_LIMIT_ENABLED` | `true` | backend |
| `CORS_ORIGINS` | `["https://residency-scheduler-frontend.onrender.com"]` | backend |

---

## Resource Scaling Guide

### When to Scale Up

| Symptom | Likely Cause | Solution |
|---------|--------------|----------|
| Schedule generation timeouts | Worker memory exhaustion | Upgrade worker to Standard |
| 503 errors during peak usage | Backend overloaded | Upgrade backend to Standard |
| Slow API responses | Database connection saturation | Upgrade PostgreSQL plan |
| Redis connection errors | Redis memory limit | Upgrade Redis plan |

### Render Plan Comparison

| Plan | RAM | CPU | Monthly Cost (approx) |
|------|-----|-----|----------------------|
| Starter | 512MB | 0.5 | $7/service |
| Standard | 2GB | 1.0 | $25/service |
| Pro | 4GB | 2.0 | $85/service |

---

## Related Documentation

- [CLAUDE.md](../../CLAUDE.md) - Project guidelines
- [DEPLOYMENT_TROUBLESHOOTING.md](../development/DEPLOYMENT_TROUBLESHOOTING.md) - Docker debugging
- [docker-compose.yml](../../docker-compose.yml) - Local development compose
- [docker-compose.prod.yml](../../docker-compose.prod.yml) - Production compose overrides
- [render.yaml](../../render.yaml) - Render Blueprint

---

## Revision History

| Date | Author | Changes |
|------|--------|---------|
| 2025-12-30 | Claude Code | Initial assessment |

---

*This document should be reviewed before each production deployment and updated as issues are resolved.*
