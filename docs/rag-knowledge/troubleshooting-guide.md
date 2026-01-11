# Troubleshooting Guide

## Overview

This guide covers common issues and solutions for the Residency Scheduler. Use the symptom-based sections to quickly find solutions.

## Quick Diagnostic Commands

```bash
# Check container health
docker ps --format "table {{.Names}}\t{{.Status}}"

# View logs
docker logs scheduler-local-backend --tail 50

# Check database connectivity
curl http://localhost:8000/api/v1/health/ready

# Check if file exists in container
docker exec scheduler-local-backend ls -la /app/path/to/file
```

## Installation Issues

### Database Connection Failed

**Symptoms:**
```
Error: Connection refused to localhost:5432
```

**Causes:**
- PostgreSQL not running
- Wrong connection string
- Firewall blocking port

**Solutions:**
```bash
# Docker
docker-compose up -d db
docker-compose logs db

# Local
sudo systemctl start postgresql
sudo systemctl status postgresql
```

### Redis Connection Failed

**Symptoms:**
```
Error: Connection refused to localhost:6379
```

**Solutions:**
```bash
# Docker
docker-compose up -d redis

# Local
redis-server
```

### Port Already in Use

**Symptoms:**
```
Error: Address already in use: 8000
```

**Solution:**
```bash
# Find process using port
lsof -i :8000

# Kill process
kill -9 <PID>
```

## API Issues

### "API Returns Wrong Data" (Undefined Properties)

**Root Cause:** TypeScript interface uses snake_case but axios converts to camelCase.

**Debugging:**
1. Check Network tab - raw response shows snake_case
2. Check console.log(response.data) - shows camelCase
3. Check TypeScript interface - must use camelCase

**Fix:**
```typescript
// ❌ Wrong
interface Person {
  pgy_level: number;
  created_at: string;
}

// ✓ Correct
interface Person {
  pgyLevel: number;
  createdAt: string;
}
```

### 401 Unauthorized

**Causes:**
- Token expired
- Invalid credentials
- Cookie not sent

**Solutions:**
- Re-login to get new token
- Check `withCredentials: true` in axios config
- Verify cookie is set (DevTools → Application → Cookies)

### 422 Validation Error

**Cause:** Request data doesn't match Pydantic schema.

**Debug:**
```python
# Check the error detail
{
    "detail": [
        {
            "loc": ["body", "pgy_level"],
            "msg": "ensure this value is greater than or equal to 1",
            "type": "value_error.number.not_ge"
        }
    ]
}
```

**Fix:** Ensure request data matches schema requirements.

## Database Issues

### Migration Errors

**Symptoms:**
```
Error: Can't locate revision
```

**Solution:**
```bash
cd backend
alembic downgrade base
alembic upgrade head
```

### Migration Name Too Long

**Symptoms:**
Container fails to start with migration error.

**Cause:** Migration revision ID exceeds 64 characters.

**Fix:**
```bash
# Good (under 64 chars)
20260109_add_person_pgy

# Bad (too long)
20260109_add_person_pgy_level_field_for_resident_tracking_purposes
```

### "Column Does Not Exist"

**Debugging:**
```bash
# Check migration applied
docker exec scheduler-local-backend alembic current

# Check migration files exist
ls backend/alembic/versions/

# Force re-apply
docker exec scheduler-local-backend alembic stamp head
docker exec scheduler-local-backend alembic upgrade head
```

## Docker Issues

### Container Won't Start

```bash
# Check status
docker-compose ps

# View logs
docker-compose logs <service_name>

# Rebuild
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### "Works Locally, Fails in Docker"

**Checklist:**
1. Different Python version? Host might be 3.9, container is 3.11
2. Missing dependency? Check requirements.txt/package.json
3. Environment variable missing? Check docker-compose.local.yml
4. File not synced? Volume mount might be stale - run `docker compose restart`
5. Port conflict? Another service using the same port

### Container Staleness

**Symptoms:**
- File exists on host but container reports "file not found"
- Code changes not reflected

**Fix:**
```bash
# Rebuild specific service
docker compose -f docker-compose.yml -f docker-compose.local.yml up -d --build backend
```

### Celery-Beat Unhealthy

**Causes:**
- Stale scheduler file
- Redis password mismatch
- Database schema mismatch

**Fix:**
```bash
# Clear stale scheduler file
docker compose exec celery-beat rm -f /app/celerybeat-schedule

# Restart
docker compose restart celery-beat
```

### Environment Variable Mismatch

**Symptoms:**
- Containers start but can't connect to Redis/DB
- "Authentication failed" in logs

**Fix:**
```bash
# Full teardown
docker compose down -v
docker system prune -f

# Rebuild
docker compose build --no-cache
docker compose up -d
```

## Schedule Generation Issues

### "No Valid Schedule Found"

**Causes:**
1. Insufficient staff - not enough people to cover requirements
2. Constraint conflicts - impossible requirements
3. Algorithm timeout - complex schedule needs more time

**Solutions:**
- Review absence calendar for coverage gaps
- Relax constraint priorities
- Try different algorithm (Greedy vs CP-SAT)
- Increase generation timeout

### Schedule Generation Slow

**Debug:**
```bash
# Check database connections
docker-compose exec db psql -U postgres -c "SELECT count(*) FROM pg_stat_activity;"

# Clear Redis cache
docker-compose exec redis redis-cli FLUSHALL
```

## Frontend Issues

### Frontend Slow

**Checklist:**
- Check browser console for errors
- Clear browser cache
- Check network tab for slow requests
- Look for unnecessary re-renders (React DevTools)

### TanStack Query Not Updating

**Cause:** Stale cache or missing invalidation.

**Fix:**
```typescript
// Invalidate after mutation
onSuccess: () => {
  queryClient.invalidateQueries({ queryKey: ['people'] });
},
```

## Git Issues

### Committed to Wrong Branch

```bash
# Save your changes
git stash

# Switch to correct branch
git checkout correct-branch

# Apply changes
git stash pop
```

### Need to Undo Last Commit (Not Pushed)

```bash
# Keep changes, undo commit
git reset --soft HEAD~1

# Discard changes entirely
git reset --hard HEAD~1
```

### Diverged from Main

```bash
# Rebase onto latest main (preferred)
git fetch origin main
git rebase origin/main

# If conflicts are too messy, merge instead
git merge origin/main
```

## Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Invalid/expired token | Re-login |
| `403 Forbidden` | Insufficient permissions | Check user role |
| `404 Not Found` | Resource doesn't exist | Verify ID/URL |
| `422 Validation Error` | Invalid request data | Check request format |
| `429 Too Many Requests` | Rate limited | Wait and retry |
| `500 Internal Server Error` | Server error | Check backend logs |

## Health Checks

```bash
# Backend health
curl http://localhost:8000/health

# All services status
docker-compose ps

# Database connectivity
docker-compose exec backend python -c "
from app.db.session import engine
with engine.connect() as conn:
    print('Database connected!')
"
```

## Pre-PR Checklist

- [ ] TypeScript interfaces use camelCase for API response fields
- [ ] All async functions have `await` on DB operations
- [ ] Migration name is ≤64 characters
- [ ] No secrets in code or logs
- [ ] Tests pass: `pytest` and `npm test`
- [ ] Linting passes: `ruff check` and `npm run lint`
- [ ] No `console.log` left in production code
- [ ] Error handling doesn't leak sensitive info

## Getting Help

If your issue isn't listed here:

1. **Search** existing GitHub issues
2. **Check** application logs: `docker-compose logs -f`
3. **Open** a new issue with:
   - Steps to reproduce
   - Expected vs actual behavior
   - Error messages and logs
   - Environment details (OS, browser, versions)
