# Session 14 Lessons Learned: Deployment Debugging

> **Date:** 2025-12-22
> **Duration:** Extended debugging session
> **Outcome:** Multiple schema and configuration issues discovered and fixed

---

## Executive Summary

This session involved debugging a cascade of deployment issues after a PII scrub and model updates. The issues fell into three categories:

1. **Database Schema Mismatches** - Models had columns that didn't exist in database
2. **SQLAlchemy-Continuum Misconfiguration** - Version tables didn't match expected schema
3. **Rate Limiting Cascade** - Failed requests triggered rate limits, causing frontend seizure

---

## Issues Discovered and Fixed

### 1. Missing `explain_json` Column in Assignments Table

**Error:**
```
psycopg2.errors.UndefinedColumn: column assignments.explain_json does not exist
```

**Root Cause:** Assignment model had explainability columns added but no migration created:
- `explain_json` (JSONB)
- `confidence` (Float)
- `score` (Float)
- `alternatives_json` (JSONB)
- `audit_hash` (String)

**Fix:** Created migration `20251222_add_assignment_explainability_columns.py`

**Lesson:** When adding columns to models, always create corresponding Alembic migration.

---

### 2. Missing `freeze_horizon_days` and `freeze_scope` in ApplicationSettings

**Error:**
```
psycopg2.errors.UndefinedColumn: column application_settings.freeze_horizon_days does not exist
```

**Root Cause:** ApplicationSettings model had freeze columns without migration.

**Fix:** Added columns in migration `20251222_fix_settings_and_version_tables.py`

---

### 3. Version Table Naming Mismatch

**Error:**
```
psycopg2.errors.UndefinedTable: relation "schedule_runs_version" does not exist
```

**Root Cause:** SQLAlchemy-Continuum expects version tables named `{tablename}_version`.

| Main Table | Expected Version Table | Actual (Wrong) |
|------------|------------------------|----------------|
| `schedule_runs` | `schedule_runs_version` | `schedule_run_version` |
| `assignments` | `assignments_version` | `assignment_version` |

**Fix:** Renamed tables in migration:
```sql
ALTER TABLE schedule_run_version RENAME TO schedule_runs_version;
ALTER TABLE assignment_version RENAME TO assignments_version;
```

**Lesson:** When manually creating version tables, match the exact SQLAlchemy-Continuum naming convention. The version table name should match the main table name exactly (including plural form) with `_version` suffix.

---

### 4. PropertyModTrackerPlugin Requires `*_mod` Columns

**Error:**
```
psycopg2.errors.UndefinedColumn: column "start_date_mod" of relation "schedule_runs_version" does not exist
```

**Root Cause:** SQLAlchemy-Continuum's `PropertyModTrackerPlugin` adds boolean `*_mod` columns to track which fields were modified. Our manual migrations didn't create these columns.

**Fix:** Disabled `PropertyModTrackerPlugin` in `backend/app/db/audit.py`:
```python
make_versioned(
    plugins=[],  # PropertyModTrackerPlugin disabled
    options={...}
)
```

**Lesson:** If using PropertyModTrackerPlugin, must create corresponding `*_mod` boolean columns for each versioned field, OR disable the plugin.

---

### 5. CORS Errors Masking Backend Crashes

**Symptom:** Browser shows "CORS blocked" but real issue is backend 500 error.

**Root Cause:** When backend crashes before response, CORS middleware never adds headers.

**Lesson:** "CORS blocked" often means backend crashed. Check `docker logs scheduler-local-backend` for the real error.

---

### 6. 307 Redirect Drops CORS Headers

**Symptom:** Login page CORS errors on `/api/auth/me`.

**Root Cause:** Backend redirects `/api/*` to `/api/v1/*` with 307. Redirect response has no CORS headers.

**Fix:** Frontend must use `/api/v1` directly:
- `docker-compose.local.yml`: `NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1`
- `frontend/src/lib/api.ts`: Default to `/api/v1`

---

### 7. Rate Limit Cascade Causing Frontend Seizure

**Symptom:** Frontend flickering/seizing, stuck in render loop.

**Root Cause:**
1. Schedule generation failed multiple times (14 retries in console)
2. Each retry counted against rate limit (200/minute)
3. Rate limit hit → all requests blocked including `/auth/me`
4. AuthContext couldn't complete → `isLoading` stuck at `true`
5. Page re-renders infinitely waiting for auth

**Fix:**
1. Flush Redis: `docker exec scheduler-local-redis redis-cli -a local_dev_redis_pass FLUSHALL`
2. Disable rate limiting for local dev: `RATE_LIMIT_ENABLED: "false"` in docker-compose.local.yml

**Lesson:** Rate limits can cascade and break unrelated functionality. Disable for local development.

---

### 8. Frontend Render Loop (RESOLVED)

**Symptom:** Frontend continuously renders `{ isAuthenticated: false, isLoading: true }`

**Root Cause:** The axios response interceptor in `frontend/src/lib/api.ts` redirected to `/login` on any 401 error - including when already on the login page! This created an infinite loop:

1. Login page loads → AuthContext checks auth via `validateToken()`
2. Backend returns 401 (not authenticated - this is expected)
3. Axios interceptor sees 401 → `window.location.href = '/login'`
4. Page reloads → Go back to step 1

**Fix:** Skip redirect if already on login page:
```typescript
// In frontend/src/lib/api.ts
if (apiError.status === 401 && !window.location.pathname.includes('/login')) {
  window.location.href = '/login'
}
```

**Lesson:** When implementing automatic auth redirects, always check if already on the login page to avoid infinite loops.

---

## Files Modified This Session

### Migrations Created
1. `backend/alembic/versions/20251222_add_assignment_explainability_columns.py`
2. `backend/alembic/versions/20251222_fix_settings_and_version_tables.py`

### Configuration Changes
1. `backend/app/db/audit.py` - Disabled PropertyModTrackerPlugin
2. `docker-compose.local.yml` - Added `RATE_LIMIT_ENABLED: "false"`
3. `frontend/src/lib/api.ts` - Default URL to `/api/v1` (earlier session)
4. `frontend/src/lib/api.ts` - Fixed 401 redirect loop by checking if already on login page
5. `frontend/next.config.js` - Disabled React StrictMode temporarily for debugging

### Documentation Created/Updated
1. `docs/development/DEPLOYMENT_TROUBLESHOOTING.md` - Comprehensive troubleshooting guide
2. `docs/development/SESSION_14_LESSONS_LEARNED.md` - This document

---

## Recommended Clean Rebuild Procedure

```bash
# 1. Stop everything
docker-compose -f docker-compose.local.yml down

# 2. Remove all project images
docker rmi autonomous-assignment-program-manager-backend 2>/dev/null || true
docker rmi autonomous-assignment-program-manager-frontend 2>/dev/null || true
docker rmi autonomous-assignment-program-manager-celery-worker 2>/dev/null || true
docker rmi autonomous-assignment-program-manager-celery-beat 2>/dev/null || true

# 3. Remove volumes (fresh database)
docker-compose -f docker-compose.local.yml down -v

# 4. Prune build cache
docker builder prune -af

# 5. Rebuild everything
docker-compose -f docker-compose.local.yml up -d --build

# 6. Wait for services
sleep 30

# 7. Apply all migrations
docker exec scheduler-local-backend alembic upgrade head

# 8. Verify backend health
curl -s http://localhost:8000/health | jq .

# 9. Seed data
docker exec scheduler-local-backend python -m scripts.seed_people
docker exec scheduler-local-backend python -m scripts.seed_rotation_templates
docker exec scheduler-local-backend python -m scripts.seed_blocks --year 2025 --block 10

# 10. Test login
# Open http://localhost:3000 and login with admin/admin123
```

---

## Prevention Checklist for Future Sessions

Before deploying changes:

- [ ] All model changes have corresponding Alembic migrations
- [ ] Run `alembic upgrade head` after any model changes
- [ ] If using SQLAlchemy-Continuum, version tables match main table columns
- [ ] Frontend uses `/api/v1` directly (not `/api`)
- [ ] Rate limiting disabled for local development
- [ ] Test backend health endpoint before frontend testing
- [ ] Check backend logs if frontend shows CORS errors

---

## Technical Debt Identified

1. **PropertyModTrackerPlugin disabled** - Should either:
   - Create migrations to add `*_mod` columns to version tables, OR
   - Permanently remove the plugin and document the decision

2. **Manual version table migrations** - Consider using Continuum's auto-generation:
   ```python
   # In alembic/env.py, configure Continuum to auto-generate
   ```

3. **Frontend auth loop** - Investigate root cause:
   - React StrictMode behavior
   - Next.js HMR conflicts with auth state
   - Potential circular dependency in auth flow

---

*Document created during Session 14 debugging. Update as issues are resolved.*
