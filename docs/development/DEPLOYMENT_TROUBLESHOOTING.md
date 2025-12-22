# Deployment Troubleshooting Guide

> **Last Updated:** 2025-12-22
> **Purpose:** Document recurring deployment issues and their solutions

This document captures lessons learned from debugging deployment issues. When the stack fails to start or behave correctly, check these common issues first.

---

## Table of Contents

1. [Quick Diagnostic Commands](#quick-diagnostic-commands)
2. [Database Issues](#database-issues)
3. [Docker Build Issues](#docker-build-issues)
4. [CORS and Frontend Issues](#cors-and-frontend-issues)
5. [Authentication Issues](#authentication-issues)
6. [SQLAlchemy Model Issues](#sqlalchemy-model-issues)
7. [Clean Rebuild Procedure](#clean-rebuild-procedure)

---

## Quick Diagnostic Commands

```bash
# Check container status
docker ps -a | grep scheduler

# View backend logs
docker logs scheduler-local-backend --tail 50

# Check if backend is healthy
curl -s http://localhost:8000/health | jq .

# Check database connection
docker exec scheduler-local-db psql -U scheduler -d residency_scheduler -c "SELECT 1"

# Check Redis connection
docker exec scheduler-local-redis redis-cli -a local_dev_redis_pass ping

# View all container logs
docker-compose -f docker-compose.local.yml logs -f
```

---

## Database Issues

### Missing Database Columns

**Symptoms:**
- Backend returns 500 errors
- Browser shows "CORS blocked" (because error occurs before CORS middleware)
- Backend logs show: `psycopg2.errors.UndefinedColumn: column X does not exist`

**Example:**
```
psycopg2.errors.UndefinedColumn: column assignments.explain_json does not exist
LINE 1: ...nments.notes, assignments.override_reason, assignments.explain_json...
```

**Root Cause:** Model defines columns that don't exist in the database table. This happens when:
1. Model was updated but migration was never created
2. Migration exists but was never applied
3. Database was seeded from old schema

**Solution:**
```bash
# Check current migration state
docker exec scheduler-local-backend alembic current

# Apply pending migrations
docker exec scheduler-local-backend alembic upgrade head

# If column still missing, check if migration exists
ls backend/alembic/versions/ | grep -i <column_name>

# If no migration exists, create one (see "Creating Migrations" below)
```

### Missing Tables

**Symptoms:**
- `relation "table_name" does not exist`

**Solution:**
```bash
# Apply all migrations
docker exec scheduler-local-backend alembic upgrade head

# If table still missing, check model is imported in alembic/env.py
```

### Creating Migrations for Missing Columns

When the model has columns that don't exist in the database:

```bash
# Option 1: Auto-generate migration (may need manual review)
cd backend
alembic revision --autogenerate -m "Add missing columns to table"

# Option 2: Manual migration
alembic revision -m "Add missing columns to table"
# Then edit the generated file in alembic/versions/
```

Example migration for missing columns:
```python
def upgrade() -> None:
    op.add_column('assignments', sa.Column('explain_json', postgresql.JSONB(), nullable=True))
    op.add_column('assignments', sa.Column('confidence', sa.Float(), nullable=True))

def downgrade() -> None:
    op.drop_column('assignments', 'confidence')
    op.drop_column('assignments', 'explain_json')
```

---

## Docker Build Issues

### Cached Layer Prevents Dependency Installation

**Symptoms:**
- Python import errors like `ImportError: failed to find libmagic`
- System library missing despite being in Dockerfile

**Root Cause:** Docker build cache retains old layers. Even with `--build`, the base image layer with `apt-get install` may be cached.

**Solution:**
```bash
# Nuclear option: remove all project images and cache
docker-compose -f docker-compose.local.yml down
docker rmi autonomous-assignment-program-manager-backend 2>/dev/null || true
docker rmi autonomous-assignment-program-manager-frontend 2>/dev/null || true
docker builder prune -af

# Rebuild from scratch
docker-compose -f docker-compose.local.yml up -d --build
```

### Volume Data Persistence Issues

**Symptoms:**
- Old data persists despite code changes
- Database schema doesn't match models

**Solution:**
```bash
# Remove volumes (WARNING: destroys data!)
docker-compose -f docker-compose.local.yml down -v

# Rebuild
docker-compose -f docker-compose.local.yml up -d --build

# Re-seed if needed
docker exec scheduler-local-backend python -m scripts.seed_people
docker exec scheduler-local-backend python -m scripts.seed_rotation_templates
```

---

## CORS and Frontend Issues

### 307 Redirect Causes CORS Errors

**Symptoms:**
- Browser console shows: `Access to XMLHttpRequest blocked by CORS policy`
- Network tab shows 307 redirect from `/api/...` to `/api/v1/...`
- Backend logs show successful request but browser blocks it

**Root Cause:** The backend redirects `/api/*` to `/api/v1/*` with HTTP 307. The redirect response doesn't include CORS headers, so the browser blocks it.

**Solution:** Configure frontend to use `/api/v1` directly:

1. **docker-compose.local.yml** - Set correct API URL:
```yaml
frontend:
  environment:
    NEXT_PUBLIC_API_URL: http://localhost:8000/api/v1  # Not /api
```

2. **frontend/src/lib/api.ts** - Update default fallback:
```typescript
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'
```

3. **Rebuild frontend** after changes:
```bash
docker-compose -f docker-compose.local.yml up -d --build frontend
```

### Frontend Environment Variables Not Updating

**Symptoms:**
- Changed `NEXT_PUBLIC_*` variable but frontend uses old value
- Works after container restart

**Root Cause:** Next.js bakes `NEXT_PUBLIC_*` variables into the build at compile time.

**Solution:**
```bash
# Must rebuild frontend image, not just restart
docker-compose -f docker-compose.local.yml up -d --build frontend
```

---

## Authentication Issues

### Login Succeeds But User Appears Unauthenticated

**Symptoms:**
- Login POST returns 200
- Subsequent requests return 401
- Cookie not being sent

**Debug Steps:**
1. Check browser dev tools > Application > Cookies
2. Verify `access_token` cookie exists
3. Check cookie properties (httpOnly, Secure, SameSite)

**Common Causes:**
- `withCredentials: true` missing from axios config
- Cookie domain mismatch
- HTTPS required but using HTTP

**Solution:**
Ensure API client sends credentials:
```typescript
const client = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,  // Required for httpOnly cookies
})
```

---

## SQLAlchemy Model Issues

### Reserved Column Name "metadata"

**Symptoms:**
```
sqlalchemy.exc.InvalidRequestError: Attribute name 'metadata' is reserved
```

**Root Cause:** `metadata` is a reserved attribute name in SQLAlchemy Base class.

**Solution:** Rename column to something descriptive:
```python
# Bad
metadata = Column(JSONB())

# Good
run_config = Column(JSONB())  # or config_data, settings_json, etc.
```

### Ambiguous Foreign Keys

**Symptoms:**
```
sqlalchemy.exc.AmbiguousForeignKeysError: Could not determine join condition
```

**Root Cause:** Multiple foreign keys to same table without explicit specification.

**Solution:** Use `foreign_keys` parameter in relationship:
```python
class APIKey(Base):
    owner_id = Column(UUID, ForeignKey('users.id'))
    created_by_id = Column(UUID, ForeignKey('users.id'))

    # Explicit foreign_keys to resolve ambiguity
    owner = relationship("User", foreign_keys=[owner_id])
    created_by = relationship("User", foreign_keys=[created_by_id])
```

### Stale Model Imports After Rename

**Symptoms:**
- `ImportError: cannot import name 'OldModelName'`
- `NameError: name 'OldModelName' is not defined`

**Root Cause:** Model was renamed but imports in other files still use old name.

**Solution:**
```bash
# Find all references to old name
grep -r "OldModelName" backend/app/

# Update each file to use new name
# Common locations:
#   - routes/*.py
#   - services/*.py
#   - schemas/*.py
#   - models/__init__.py
```

---

## Clean Rebuild Procedure

When all else fails, perform a complete clean rebuild:

```bash
# 1. Stop everything
docker-compose -f docker-compose.local.yml down

# 2. Remove project images
docker rmi autonomous-assignment-program-manager-backend 2>/dev/null || true
docker rmi autonomous-assignment-program-manager-frontend 2>/dev/null || true
docker rmi autonomous-assignment-program-manager-celery-worker 2>/dev/null || true
docker rmi autonomous-assignment-program-manager-celery-beat 2>/dev/null || true

# 3. Optional: Remove volumes if you want fresh database
# WARNING: This destroys all data!
# docker-compose -f docker-compose.local.yml down -v

# 4. Clean build cache
docker builder prune -af

# 5. Rebuild and start
docker-compose -f docker-compose.local.yml up -d --build

# 6. Wait for services to be healthy
sleep 20

# 7. Apply migrations
docker exec scheduler-local-backend alembic upgrade head

# 8. Verify
curl -s http://localhost:8000/health | jq .

# 9. Seed data if needed
docker exec scheduler-local-backend python -m scripts.seed_people
docker exec scheduler-local-backend python -m scripts.seed_rotation_templates
docker exec scheduler-local-backend python -m scripts.seed_blocks --year 2025 --block 10
```

---

## Issues Fixed in Session 14 (2025-12-22)

This section documents specific issues encountered and fixed:

### 1. Missing `explain_json` Column in Assignments Table

**Error:**
```
psycopg2.errors.UndefinedColumn: column assignments.explain_json does not exist
```

**Affected Endpoints:** `/api/v1/assignments`, `/api/v1/schedule/validate`

**Root Cause:** The Assignment model defined explainability columns that were never migrated to the database:
- `explain_json`
- `confidence`
- `score`
- `alternatives_json`
- `audit_hash`

**Fix:** Created migration `20251222_add_assignment_explainability_columns.py`

### 2. CORS Errors from 307 Redirect

**Error:** Browser blocked requests due to missing CORS headers on redirect response.

**Root Cause:** Frontend was using `/api` which redirected to `/api/v1`. The 307 response lacked CORS headers.

**Fix:** Updated `NEXT_PUBLIC_API_URL` to use `/api/v1` directly in:
- `docker-compose.local.yml`
- `frontend/src/lib/api.ts` (default fallback)

### 3. Redis Double Password in URL

**Error:** Redis connection failed with authentication error.

**Root Cause:** Redis URL had password both in URL and as separate parameter, causing double-encoding.

**Fix:** Updated `backend/app/core/config.py` to not append password when URL already contains it.

### 4. SQLAlchemy AmbiguousForeignKeysError

**Error:**
```
AmbiguousForeignKeysError: Could not determine join condition between parent/child tables on relationship APIKey.owner
```

**Fix:** Added explicit `foreign_keys=[owner_id]` to the relationship definition.

### 5. Reserved `metadata` Column Name

**Error:**
```
InvalidRequestError: Attribute name 'metadata' is reserved
```

**Fix:** Renamed `metadata` columns to descriptive names across 8 model files.

### 6. Missing `freeze_horizon_days` and `freeze_scope` in ApplicationSettings

**Error:**
```
psycopg2.errors.UndefinedColumn: column application_settings.freeze_horizon_days does not exist
```

**Affected Endpoints:** `/api/v1/settings`

**Root Cause:** ApplicationSettings model has freeze columns not in database.

**Fix:** Created migration `20251222_fix_settings_and_version_tables.py`

### 7. Version Table Naming Mismatch

**Error:**
```
psycopg2.errors.UndefinedTable: relation "schedule_runs_version" does not exist
```

**Affected Endpoints:** `/api/v1/schedule/generate`

**Root Cause:** SQLAlchemy-Continuum expects version tables named `{tablename}_version`.
The `schedule_runs` table expects `schedule_runs_version` but migration created `schedule_run_version` (singular).

**Fix:** Renamed table in migration `20251222_fix_settings_and_version_tables.py`:
```sql
ALTER TABLE schedule_run_version RENAME TO schedule_runs_version;
```

### 8. PropertyModTrackerPlugin Requires Missing `*_mod` Columns

**Error:**
```
psycopg2.errors.UndefinedColumn: column "start_date_mod" of relation "schedule_runs_version" does not exist
```

**Root Cause:** SQLAlchemy-Continuum's `PropertyModTrackerPlugin` adds boolean `*_mod` columns
to version tables to track which fields were modified. Our manual migration (009) didn't create these columns.

**Fix:** Disabled `PropertyModTrackerPlugin` in `backend/app/db/audit.py`:
```python
make_versioned(
    plugins=[],  # PropertyModTrackerPlugin disabled
    options={...}
)
```

To re-enable later, create migrations that add `*_mod` boolean columns for each versioned field.

---

## Known Harmless Warnings

### bcrypt `__about__` AttributeError

**Warning in logs:**
```
AttributeError: module 'bcrypt' has no attribute '__about__'
detected 'bcrypt' backend, version '<unknown>'
```

**Status:** Harmless - passlib trying to detect bcrypt version but bcrypt 4.x removed that attribute.

**Why it's OK:** Login still works. The workaround is automatically enabled.

**Reference:** See `docs/deployment/LESSONS_LEARNED_ROUND1.md` for full bcrypt/passlib history.

---

## Appendix: Useful Debug Logging

### Backend Request/Response Logging

Add to `backend/app/main.py`:
```python
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.debug(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    logger.debug(f"Response: {response.status_code}")
    return response
```

### Frontend API Logging

Already enabled in `frontend/src/lib/api.ts`:
```typescript
client.interceptors.request.use((config) => {
  console.log(`[api.ts] REQUEST: ${config.method?.toUpperCase()} ${config.url}`)
  return config
})
```

---

*Document maintained as lessons learned. Update when new issues are discovered and resolved.*
