# Docker Cleanup Checklist

> **Created:** 2026-01-12
> **Status:** Pending backup before cleanup
> **Potential Savings:** ~117 GB

---

## Pre-Cleanup: BACKUP FIRST

```bash
# Backup database before any cleanup
pg_dump -h localhost -U scheduler scheduler > backup_$(date +%Y%m%d).sql

# Or via Docker
docker exec scheduler-local-db pg_dump -U scheduler scheduler > backup_$(date +%Y%m%d).sql
```

---

## 1. Old Tagged Images (~95 GB reclaimable)

### Check Contents First

```bash
# List old images (9+ days old)
docker images --format "{{.Repository}}:{{.Tag}}\t{{.Size}}\t{{.CreatedSince}}" | grep -E "(immaculate|sacred)"

# See what's using each image
docker ps -a --format "{{.Image}}\t{{.Names}}\t{{.Status}}"
```

### Images to Review

| Image | Tag | Size | Decision |
|-------|-----|------|----------|
| backend | immaculate-empty | 3.35GB | [ ] Keep / [ ] Delete |
| backend | immaculate-loaded | 3.35GB | [ ] Keep / [ ] Delete |
| backend | sacred-612 | 3.35GB | [ ] Keep / [ ] Delete |
| mcp-server | immaculate-empty | 756MB | [ ] Keep / [ ] Delete |
| mcp-server | immaculate-loaded | 756MB | [ ] Keep / [ ] Delete |
| mcp-server | sacred-612 | 756MB | [ ] Keep / [ ] Delete |
| celery-worker | immaculate-empty | 3.35GB | [ ] Keep / [ ] Delete |
| celery-worker | immaculate-loaded | 3.35GB | [ ] Keep / [ ] Delete |
| celery-worker | sacred-612 | 3.35GB | [ ] Keep / [ ] Delete |
| celery-beat | immaculate-empty | 3.35GB | [ ] Keep / [ ] Delete |
| celery-beat | immaculate-loaded | 3.35GB | [ ] Keep / [ ] Delete |
| celery-beat | sacred-612 | 3.35GB | [ ] Keep / [ ] Delete |
| frontend | immaculate-empty | 431MB | [ ] Keep / [ ] Delete |
| frontend | immaculate-loaded | 431MB | [ ] Keep / [ ] Delete |

### Cleanup (after review)

```bash
# Remove specific image
docker rmi backend:immaculate-empty

# Or remove all unused images older than 7 days
docker image prune -a --filter "until=168h"
```

---

## 2. Anonymous Volumes (~194 MB reclaimable)

### Check Contents First

```bash
# List anonymous volumes (hex names)
docker volume ls -f "name=^[0-9a-f]"

# Inspect each to see what it contains
docker volume inspect 3c38ec09339fe864b66a40fe3998f7fb64cf33f82a38b7f2fc6125e0c08773ab

# See mount point and check contents
docker run --rm -v VOLUME_NAME:/data alpine ls -la /data
```

### Volumes to Review

| Volume ID (truncated) | Mountpoint | Decision |
|-----------------------|------------|----------|
| 3c38ec09339f... | ? | [ ] Keep / [ ] Delete |
| 5d8abe6c9661... | ? | [ ] Keep / [ ] Delete |
| 9b187b6ae441... | ? | [ ] Keep / [ ] Delete |
| 69e05a076999... | ? | [ ] Keep / [ ] Delete |
| 6619a2f46cfa... | ? | [ ] Keep / [ ] Delete |
| 6794fcc1f555... | ? | [ ] Keep / [ ] Delete |

### Cleanup (after review)

```bash
# Remove specific volume
docker volume rm VOLUME_NAME

# Or remove all unused volumes (CAREFUL - checks if attached to container)
docker volume prune
```

---

## 3. Build Cache (~21 GB reclaimable)

### Check Contents First

```bash
# See build cache usage
docker builder du

# See cache entries
docker builder du --verbose | head -50
```

### Cleanup

```bash
# Remove unused build cache
docker builder prune

# Remove ALL build cache (more aggressive)
docker builder prune -a
```

---

## 4. Stopped Containers

### Check Contents First

```bash
# List stopped containers
docker ps -a -f "status=exited"

# Check logs before removing
docker logs scheduler-local-n8n --tail 50
```

### Containers to Review

| Container | Status | Decision |
|-----------|--------|----------|
| scheduler-local-n8n | Exited (4 days) | [ ] Keep / [ ] Delete |

### Cleanup (after review)

```bash
# Remove specific container
docker rm scheduler-local-n8n

# Remove all stopped containers
docker container prune
```

---

## 5. Unhealthy Container Investigation

```bash
# Check why backend is unhealthy
docker inspect scheduler-local-backend --format='{{json .State.Health}}'

# Check recent logs
docker logs scheduler-local-backend --tail 100

# Restart if needed
docker restart scheduler-local-backend
```

---

## Full Cleanup Script (AFTER all reviews complete)

```bash
#!/bin/bash
# docker-cleanup.sh - Run ONLY after backup and review

echo "=== Starting Docker Cleanup ==="

# 1. Remove reviewed images
# docker rmi backend:immaculate-empty backend:immaculate-loaded backend:sacred-612
# docker rmi mcp-server:immaculate-empty mcp-server:immaculate-loaded mcp-server:sacred-612
# ... etc

# 2. Remove orphaned volumes
# docker volume prune -f

# 3. Remove build cache
# docker builder prune -f

# 4. Remove stopped containers
# docker container prune -f

echo "=== Cleanup Complete ==="
docker system df
```

---

## Named Volumes (DO NOT DELETE)

These contain actual data:

| Volume | Purpose | ⚠️ |
|--------|---------|-----|
| postgres_data / postgres_local_data | Database | CRITICAL |
| redis_data / redis_local_data | Cache | Important |
| n8n_data / n8n_local_data | Workflows | If using n8n |
| backend_local_venv | Python venv | Rebuild-able |
| scheduler-local-db-data | DB data | CRITICAL |

---

## Post-Cleanup Verification

```bash
# Check disk usage after cleanup
docker system df

# Verify containers still running
docker ps

# Test endpoints
curl http://localhost:8000/health
curl http://localhost:3000
```
