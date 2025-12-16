# Runbook: High Error Rate

**Alert Names:** `HighErrorRate`, `CriticalErrorRate`
**Severity:** Warning/Critical
**Service:** Backend

## Description

These alerts fire when the API error rate (5xx responses) exceeds thresholds:
- **Warning**: Error rate > 5% for 5 minutes
- **Critical**: Error rate > 15% for 2 minutes

## Impact

- Users experiencing failures
- Data operations may be partially failing
- Potential data integrity concerns
- User trust and productivity affected

## Quick Diagnosis

```bash
# 1. Check backend logs for errors
docker compose logs --tail=200 backend | grep -i "error\|exception\|traceback"

# 2. Check error metrics
curl -s http://localhost:8000/metrics | grep http_requests_total | grep status=\"5

# 3. Get recent error details
docker compose logs --since 10m backend 2>&1 | grep -A 5 "ERROR"

# 4. Check system resources
docker stats --no-stream
```

## Resolution Steps

### Step 1: Identify Error Pattern

```bash
# Group errors by endpoint
docker compose logs --since 30m backend 2>&1 | \
  grep "ERROR" | \
  awk '{print $NF}' | \
  sort | uniq -c | sort -rn | head -10
```

Common patterns:
- Single endpoint failing → Specific bug or dependency issue
- All endpoints failing → Infrastructure or database issue
- Intermittent across endpoints → Resource exhaustion

### Step 2: Check Dependencies

**Database connectivity:**
```bash
docker compose exec backend python -c "
from app.db.session import engine
with engine.connect() as conn:
    print('Database OK')
"
```

**Redis connectivity:**
```bash
docker compose exec backend python -c "
import redis
r = redis.from_url('redis://redis:6379/0')
print('Redis OK:', r.ping())
"
```

### Step 3: Common Error Types and Fixes

#### Database Connection Errors

**Symptoms:** `sqlalchemy.exc.OperationalError`, `connection refused`

**Fix:**
```bash
# Check database
docker compose ps db
docker compose logs db | tail -20

# Restart if needed
docker compose restart db
sleep 30
docker compose restart backend
```

#### Memory Errors

**Symptoms:** `MemoryError`, `OOM killed`

**Fix:**
```bash
# Check memory usage
docker stats --no-stream

# If out of memory, restart with increased limits
docker compose down backend
# Edit docker-compose.yml to increase memory
docker compose up -d backend
```

#### Validation Errors (4xx vs 5xx)

**Check if errors are actually client errors:**
```bash
curl -s http://localhost:8000/metrics | grep http_requests_total | grep status=\"4
```

If 4xx errors are high → Check client/API contract changes

#### Timeout Errors

**Symptoms:** `asyncio.TimeoutError`, `Request timed out`

**Fix:**
```bash
# Check for slow queries
docker compose exec db psql -U scheduler -c "
SELECT pid, now() - query_start AS duration, query
FROM pg_stat_activity
WHERE state = 'active' AND query_start < now() - interval '10 seconds';"

# Kill long-running queries
docker compose exec db psql -U scheduler -c "
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'active' AND query_start < now() - interval '60 seconds';"
```

### Step 4: Emergency Mitigation

If root cause cannot be quickly identified:

```bash
# 1. Enable rate limiting to reduce load
curl -X POST http://localhost:8000/api/admin/rate-limit/strict

# 2. Restart backend to clear any stuck state
docker compose restart backend

# 3. If database-related, restart database
docker compose restart db
sleep 30
docker compose restart backend
```

### Step 5: Verify Recovery

```bash
# Watch error rate decrease
watch -n 5 'curl -s http://localhost:8000/metrics | grep http_requests_total | grep status=\"5'

# Check health endpoint
curl http://localhost:8000/health

# Run a few test requests
curl http://localhost:8000/api/people?limit=5
```

## Error Investigation Commands

```bash
# Get full stack trace for recent errors
docker compose logs --since 5m backend 2>&1 | grep -A 20 "Traceback"

# Count errors by type
docker compose logs --since 1h backend 2>&1 | \
  grep "ERROR" | \
  sed 's/.*ERROR/ERROR/' | \
  cut -d: -f1-2 | \
  sort | uniq -c | sort -rn

# Check if specific endpoint is failing
curl -v http://localhost:8000/api/schedule/generate -X POST -H "Content-Type: application/json" -d '{}'
```

## Escalation

| Error Rate | Duration | Action |
|------------|----------|--------|
| 5-15% | > 5 min | Investigate, notify team |
| 15-30% | > 2 min | Page on-call, active mitigation |
| > 30% | Any | All-hands, consider failover |

## Prevention

1. **Pre-deployment testing**
   - Run full test suite before deploys
   - Use staging environment for validation

2. **Gradual rollouts**
   - Deploy to canary first
   - Monitor error rates during rollout

3. **Health checks**
   - Ensure health checks verify all dependencies
   - Set appropriate timeout/retry policies

## Related Alerts

- `APIServiceDown`
- `HighLatencyP95`
- `DatabaseConnectionFailed`

---

*Last Updated: December 2024*
