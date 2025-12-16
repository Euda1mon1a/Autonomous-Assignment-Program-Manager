***REMOVED*** Runbook: Infrastructure Alerts

**Alert Names:** `HighCPUUsage`, `HighMemoryUsage`, `DiskSpaceLow`, `ContainerRestarts`
**Severity:** Warning/Critical
**Service:** Infrastructure

***REMOVED******REMOVED*** Description

Infrastructure alerts monitor host and container resource utilization.

***REMOVED******REMOVED*** Quick Reference

```bash
***REMOVED*** System overview
docker stats --no-stream

***REMOVED*** Disk usage
df -h

***REMOVED*** Container status
docker compose ps

***REMOVED*** Recent container events
docker events --since 10m --until now
```

***REMOVED******REMOVED*** Alert-Specific Resolution

***REMOVED******REMOVED******REMOVED*** HighCPUUsage

**Alert fires when:** CPU usage > 80% for 5 minutes

**Diagnosis:**
```bash
***REMOVED*** Find high-CPU containers
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}" | sort -k2 -rn

***REMOVED*** Check container processes
docker compose exec backend top -bn1 | head -20
```

**Resolution:**
1. Identify runaway process
2. Check for infinite loops or resource leaks
3. Scale horizontally if legitimate load
4. Restart problematic container

***REMOVED******REMOVED******REMOVED*** HighMemoryUsage

**Alert fires when:** Memory usage > 85% for 5 minutes

**Diagnosis:**
```bash
***REMOVED*** Memory by container
docker stats --no-stream --format "table {{.Name}}\t{{.MemUsage}}"

***REMOVED*** Detailed memory breakdown
docker compose exec backend cat /proc/meminfo | head -10
```

**Resolution:**
1. Check for memory leaks
2. Review recent code changes
3. Restart container to free memory
4. Increase memory limits if needed

***REMOVED******REMOVED******REMOVED*** DiskSpaceLow

**Alert fires when:** Disk usage > 85%

**Diagnosis:**
```bash
***REMOVED*** Overall disk usage
df -h

***REMOVED*** Find large files
du -sh /* 2>/dev/null | sort -rh | head -10

***REMOVED*** Docker disk usage
docker system df
```

**Resolution:**
```bash
***REMOVED*** Clean unused Docker resources
docker system prune -a --volumes

***REMOVED*** Clean old logs
find /var/log -name "*.log" -mtime +7 -delete

***REMOVED*** Clean old backups
find /opt/backups -mtime +30 -delete
```

***REMOVED******REMOVED******REMOVED*** ContainerRestarts

**Alert fires when:** Container restarts > 3 times in 10 minutes

**Diagnosis:**
```bash
***REMOVED*** Check restart count
docker inspect --format='{{.RestartCount}}' residency-scheduler-backend

***REMOVED*** Check container events
docker events --filter container=residency-scheduler-backend --since 1h

***REMOVED*** Check exit reason
docker inspect --format='{{.State.ExitCode}}' residency-scheduler-backend
docker logs --tail=50 residency-scheduler-backend
```

**Common exit codes:**
- `0`: Normal exit
- `1`: Application error
- `137`: OOM killed (SIGKILL)
- `143`: SIGTERM (graceful shutdown)

**Resolution by exit code:**

**Exit 1 (Application error):**
```bash
***REMOVED*** Check logs for error
docker logs --tail=200 residency-scheduler-backend | grep -i error
```

**Exit 137 (OOM):**
```bash
***REMOVED*** Increase memory limit in docker-compose.yml
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 2G
```

***REMOVED******REMOVED*** System Health Commands

```bash
***REMOVED*** Full system check
echo "=== Docker Status ===" && docker compose ps
echo "=== Container Stats ===" && docker stats --no-stream
echo "=== Disk Usage ===" && df -h | grep -v tmpfs
echo "=== Memory ===" && free -h
echo "=== Load ===" && uptime
```

***REMOVED******REMOVED*** Capacity Planning

| Metric | Warning | Critical | Action |
|--------|---------|----------|--------|
| CPU | > 70% | > 90% | Scale up/out |
| Memory | > 80% | > 95% | Add RAM or instances |
| Disk | > 80% | > 95% | Expand storage, cleanup |
| Connections | > 80% max | > 95% max | Tune pool, add replicas |

***REMOVED******REMOVED*** Escalation

| Severity | Response Time | Actions |
|----------|---------------|---------|
| Warning | 1 hour | Investigate, plan remediation |
| Critical | 15 minutes | Immediate intervention |
| System down | Immediate | Page on-call, all-hands |

***REMOVED******REMOVED*** Related Alerts

- `APIServiceDown`
- `DatabaseConnectionFailed`
- `ResilienceDefenseLevelOrange`

---

*Last Updated: December 2024*
