***REMOVED*** Runbook: API Service Down

**Alert Name:** `APIServiceDown`
**Severity:** Critical
**Service:** Backend

***REMOVED******REMOVED*** Description

This alert fires when the Residency Scheduler backend API becomes unreachable for more than 1 minute.

***REMOVED******REMOVED*** Impact

- Users cannot access the scheduling application
- Schedule generation is unavailable
- API integrations will fail
- Mobile app will show errors

***REMOVED******REMOVED*** Quick Diagnosis

```bash
***REMOVED*** 1. Check if the backend container is running
docker compose ps backend

***REMOVED*** 2. Check backend container logs
docker compose logs --tail=100 backend

***REMOVED*** 3. Check if the health endpoint responds
curl -v http://localhost:8000/health

***REMOVED*** 4. Check system resources
docker stats --no-stream
```

***REMOVED******REMOVED*** Resolution Steps

***REMOVED******REMOVED******REMOVED*** Step 1: Verify Container Status

```bash
docker compose ps
```

**If container is stopped:**
```bash
docker compose up -d backend
```

**If container is restarting:**
```bash
***REMOVED*** Check logs for crash reason
docker compose logs --tail=200 backend | grep -i "error\|exception\|fatal"
```

***REMOVED******REMOVED******REMOVED*** Step 2: Check Database Connectivity

```bash
***REMOVED*** Verify database is healthy
docker compose exec db pg_isready -U scheduler

***REMOVED*** Check database connections
docker compose exec db psql -U scheduler -c "SELECT count(*) FROM pg_stat_activity;"
```

**If database is down:**
```bash
docker compose restart db
***REMOVED*** Wait for health check
sleep 30
docker compose restart backend
```

***REMOVED******REMOVED******REMOVED*** Step 3: Check Memory/CPU

```bash
docker stats --no-stream backend db
```

**If out of memory:**
- Scale down non-essential services
- Increase container memory limits in docker-compose.yml
- Consider horizontal scaling

***REMOVED******REMOVED******REMOVED*** Step 4: Check Network

```bash
***REMOVED*** Verify network connectivity between services
docker compose exec backend ping -c 3 db
docker compose exec backend nc -zv db 5432
```

***REMOVED******REMOVED******REMOVED*** Step 5: Manual Service Restart

If above steps don't identify the issue:

```bash
docker compose down backend
docker compose up -d backend
docker compose logs -f backend
```

***REMOVED******REMOVED*** Escalation

If not resolved within 15 minutes:
1. Page team lead
2. Notify stakeholders via Slack ***REMOVED***incidents channel
3. Consider failover procedures if applicable

***REMOVED******REMOVED*** Post-Incident

1. Document root cause in incident report
2. Update runbook if new failure mode discovered
3. Consider preventive measures (monitoring, scaling, etc.)

***REMOVED******REMOVED*** Related Alerts

- `HighErrorRate`
- `HealthCheckFailing`
- `DatabaseConnectionFailed`

---

*Last Updated: December 2024*
