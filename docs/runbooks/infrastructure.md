# Runbook: Infrastructure Alerts

**Alert Names:** `HighCPUUsage`, `HighMemoryUsage`, `DiskSpaceLow`, `ContainerRestarts`
**Severity:** Warning/Critical
**Service:** Infrastructure

## Description

Infrastructure alerts monitor host and container resource utilization.

## Quick Reference

```bash
# System overview
docker stats --no-stream

# Disk usage
df -h

# Container status
docker compose ps

# Recent container events
docker events --since 10m --until now
```

## Alert-Specific Resolution

### HighCPUUsage

**Alert fires when:** CPU usage > 80% for 5 minutes

**Diagnosis:**
```bash
# Find high-CPU containers
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}" | sort -k2 -rn

# Check container processes
docker compose exec backend top -bn1 | head -20
```

**Resolution:**
1. Identify runaway process
2. Check for infinite loops or resource leaks
3. Scale horizontally if legitimate load
4. Restart problematic container

### HighMemoryUsage

**Alert fires when:** Memory usage > 85% for 5 minutes

**Diagnosis:**
```bash
# Memory by container
docker stats --no-stream --format "table {{.Name}}\t{{.MemUsage}}"

# Detailed memory breakdown
docker compose exec backend cat /proc/meminfo | head -10
```

**Resolution:**
1. Check for memory leaks
2. Review recent code changes
3. Restart container to free memory
4. Increase memory limits if needed

### DiskSpaceLow

**Alert fires when:** Disk usage > 85%

**Diagnosis:**
```bash
# Overall disk usage
df -h

# Find large files
du -sh /* 2>/dev/null | sort -rh | head -10

# Docker disk usage
docker system df
```

**Resolution:**
```bash
# Clean unused Docker resources
docker system prune -a --volumes

# Clean old logs
find /var/log -name "*.log" -mtime +7 -delete

# Clean old backups
find /opt/backups -mtime +30 -delete
```

### ContainerRestarts

**Alert fires when:** Container restarts > 3 times in 10 minutes

**Diagnosis:**
```bash
# Check restart count
docker inspect --format='{{.RestartCount}}' residency-scheduler-backend

# Check container events
docker events --filter container=residency-scheduler-backend --since 1h

# Check exit reason
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
# Check logs for error
docker logs --tail=200 residency-scheduler-backend | grep -i error
```

**Exit 137 (OOM):**
```bash
# Increase memory limit in docker-compose.yml
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 2G
```

## System Health Commands

```bash
# Full system check
echo "=== Docker Status ===" && docker compose ps
echo "=== Container Stats ===" && docker stats --no-stream
echo "=== Disk Usage ===" && df -h | grep -v tmpfs
echo "=== Memory ===" && free -h
echo "=== Load ===" && uptime
```

## Capacity Planning

| Metric | Warning | Critical | Action |
|--------|---------|----------|--------|
| CPU | > 70% | > 90% | Scale up/out |
| Memory | > 80% | > 95% | Add RAM or instances |
| Disk | > 80% | > 95% | Expand storage, cleanup |
| Connections | > 80% max | > 95% max | Tune pool, add replicas |

## Escalation

| Severity | Response Time | Actions |
|----------|---------------|---------|
| Warning | 1 hour | Investigate, plan remediation |
| Critical | 15 minutes | Immediate intervention |
| System down | Immediate | Page on-call, all-hands |

## Related Alerts

- `APIServiceDown`
- `DatabaseConnectionFailed`
- `ResilienceDefenseLevelOrange`

---

*Last Updated: December 2024*
