***REMOVED*** Runbook: High Error Rate

**Alert Names:** `HighErrorRate`, `CriticalErrorRate`
**Severity:** Warning/Critical
**Service:** Backend

***REMOVED******REMOVED*** Description

These alerts fire when the API error rate (5xx responses) exceeds thresholds:
- **Warning**: Error rate > 5% for 5 minutes
- **Critical**: Error rate > 15% for 2 minutes

***REMOVED******REMOVED*** Impact

- Users experiencing failures
- Data operations may be partially failing
- Potential data integrity concerns
- User trust and productivity affected

***REMOVED******REMOVED*** Quick Diagnosis

```bash
***REMOVED*** 1. Check backend logs for errors
docker compose logs --tail=200 backend | grep -i "error\|exception\|traceback"

***REMOVED*** 2. Check error metrics
curl -s http://localhost:8000/metrics | grep http_requests_total | grep status=\"5

***REMOVED*** 3. Get recent error details
docker compose logs --since 10m backend 2>&1 | grep -A 5 "ERROR"

***REMOVED*** 4. Check system resources
docker stats --no-stream
```

***REMOVED******REMOVED*** Resolution Steps

***REMOVED******REMOVED******REMOVED*** Step 1: Identify Error Pattern

```bash
***REMOVED*** Group errors by endpoint
docker compose logs --since 30m backend 2>&1 | \
  grep "ERROR" | \
  awk '{print $NF}' | \
  sort | uniq -c | sort -rn | head -10
```

Common patterns:
- Single endpoint failing → Specific bug or dependency issue
- All endpoints failing → Infrastructure or database issue
- Intermittent across endpoints → Resource exhaustion

***REMOVED******REMOVED******REMOVED*** Step 2: Check Dependencies

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

***REMOVED******REMOVED******REMOVED*** Step 3: Common Error Types and Fixes

***REMOVED******REMOVED******REMOVED******REMOVED*** Database Connection Errors

**Symptoms:** `sqlalchemy.exc.OperationalError`, `connection refused`

**Fix:**
```bash
***REMOVED*** Check database
docker compose ps db
docker compose logs db | tail -20

***REMOVED*** Restart if needed
docker compose restart db
sleep 30
docker compose restart backend
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Memory Errors

**Symptoms:** `MemoryError`, `OOM killed`

**Fix:**
```bash
***REMOVED*** Check memory usage
docker stats --no-stream

***REMOVED*** If out of memory, restart with increased limits
docker compose down backend
***REMOVED*** Edit docker-compose.yml to increase memory
docker compose up -d backend
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Validation Errors (4xx vs 5xx)

**Check if errors are actually client errors:**
```bash
curl -s http://localhost:8000/metrics | grep http_requests_total | grep status=\"4
```

If 4xx errors are high → Check client/API contract changes

***REMOVED******REMOVED******REMOVED******REMOVED*** Timeout Errors

**Symptoms:** `asyncio.TimeoutError`, `Request timed out`

**Fix:**
```bash
***REMOVED*** Check for slow queries
docker compose exec db psql -U scheduler -c "
SELECT pid, now() - query_start AS duration, query
FROM pg_stat_activity
WHERE state = 'active' AND query_start < now() - interval '10 seconds';"

***REMOVED*** Kill long-running queries
docker compose exec db psql -U scheduler -c "
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'active' AND query_start < now() - interval '60 seconds';"
```

***REMOVED******REMOVED******REMOVED*** Step 4: Emergency Mitigation

If root cause cannot be quickly identified:

```bash
***REMOVED*** 1. Enable rate limiting to reduce load
curl -X POST http://localhost:8000/api/admin/rate-limit/strict

***REMOVED*** 2. Restart backend to clear any stuck state
docker compose restart backend

***REMOVED*** 3. If database-related, restart database
docker compose restart db
sleep 30
docker compose restart backend
```

***REMOVED******REMOVED******REMOVED*** Step 5: Verify Recovery

```bash
***REMOVED*** Watch error rate decrease
watch -n 5 'curl -s http://localhost:8000/metrics | grep http_requests_total | grep status=\"5'

***REMOVED*** Check health endpoint
curl http://localhost:8000/health

***REMOVED*** Run a few test requests
curl http://localhost:8000/api/people?limit=5
```

***REMOVED******REMOVED*** Error Investigation Commands

```bash
***REMOVED*** Get full stack trace for recent errors
docker compose logs --since 5m backend 2>&1 | grep -A 20 "Traceback"

***REMOVED*** Count errors by type
docker compose logs --since 1h backend 2>&1 | \
  grep "ERROR" | \
  sed 's/.*ERROR/ERROR/' | \
  cut -d: -f1-2 | \
  sort | uniq -c | sort -rn

***REMOVED*** Check if specific endpoint is failing
curl -v http://localhost:8000/api/schedule/generate -X POST -H "Content-Type: application/json" -d '{}'
```

***REMOVED******REMOVED*** Escalation

| Error Rate | Duration | Action |
|------------|----------|--------|
| 5-15% | > 5 min | Investigate, notify team |
| 15-30% | > 2 min | Page on-call, active mitigation |
| > 30% | Any | All-hands, consider failover |

***REMOVED******REMOVED*** Prevention

1. **Pre-deployment testing**
   - Run full test suite before deploys
   - Use staging environment for validation

2. **Gradual rollouts**
   - Deploy to canary first
   - Monitor error rates during rollout

3. **Health checks**
   - Ensure health checks verify all dependencies
   - Set appropriate timeout/retry policies

***REMOVED******REMOVED*** Related Alerts

- `APIServiceDown`
- `HighLatencyP95`
- `DatabaseConnectionFailed`

---

*Last Updated: December 2024*
