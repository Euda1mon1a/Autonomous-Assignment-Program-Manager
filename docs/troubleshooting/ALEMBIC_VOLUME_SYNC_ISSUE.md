# Alembic Migration Volume Sync Issue

> **Status:** RESOLVED (PR #596)
> **Severity:** P2 - Infrastructure
> **Affected:** Docker development environments

---

## Quick Fix

If you encounter Alembic migration errors like:
- "Can't locate revision"
- "Target database is not up to date"
- Migrations appearing/disappearing between restarts

**Check that your docker-compose file excludes alembic/versions from volume mounts:**

```yaml
# docker-compose.dev.yml or docker-compose.local.yml
services:
  backend:
    volumes:
      - ./backend:/app
      - /app/__pycache__
      - /app/alembic/versions  # THIS LINE IS CRITICAL
```

If missing, add `/app/alembic/versions` and restart:

```bash
docker compose down
docker compose up -d --build
```

---

## What Happened

### The Problem

Docker volume mounts were overwriting container migrations with local copies:

```
Host: ./backend/alembic/versions/ (possibly stale)
         ↓ volume mount
Container: /app/alembic/versions/ (gets overwritten)
         ↓
Alembic sees wrong migration chain → ERRORS
```

### Why It Was Hard to Find

- **Intermittent**: Only broke when local and container migrations diverged
- **Self-healing**: Running `git pull` would temporarily sync migrations
- **Misdirection**: Errors blamed on migration code, not Docker config

---

## The Fix

PR #596 added volume exclusions to all development Docker Compose files:

| File | Services Updated |
|------|------------------|
| `docker-compose.dev.yml` | backend |
| `docker-compose.local.yml` | backend, celery-worker, celery-beat |

The exclusion pattern `- /app/alembic/versions` creates an anonymous volume that:
1. Preserves container's built-in migrations (from Docker image)
2. Ignores host directory (prevents overwriting)
3. Persists across container restarts

---

## Prevention Checklist

Before creating new migrations:

```bash
# 1. Pull latest from main
git pull origin main

# 2. Verify single head
docker compose exec backend alembic heads
# Should show exactly ONE head

# 3. Check current state
docker compose exec backend alembic current

# 4. Create migration
docker compose exec backend alembic revision --autogenerate -m "description"

# 5. Verify again
docker compose exec backend alembic heads
```

---

## Common Scenarios

### Scenario 1: "Multiple Heads Detected"

```bash
# Check heads
docker compose exec backend alembic heads

# If multiple heads, create merge migration
docker compose exec backend alembic merge -m "merge heads" <head1> <head2>
docker compose exec backend alembic upgrade head
```

### Scenario 2: "Revision Not Found" After Container Restart

```bash
# Rebuild container to include latest migrations
docker compose down
docker compose build --no-cache backend
docker compose up -d
```

### Scenario 3: Local and Container Out of Sync

```bash
# Compare local vs container
cd backend && alembic heads  # Local
docker compose exec backend alembic heads  # Container

# If different, rebuild container
docker compose up -d --build backend
```

---

## Technical Details

### How Volume Exclusions Work

```yaml
volumes:
  - ./backend:/app           # Bind mount: overlays host onto container
  - /app/alembic/versions    # Anonymous volume: excludes this path from overlay
```

The anonymous volume syntax (`/path` without host path) tells Docker:
- Create a container-managed volume for this path
- Initialize it with content from the Docker image
- Do NOT overlay it with the bind mount

### Why This Matters for Migrations

Migrations are **stateful configuration**:
- Created on host, committed to git
- Baked into Docker image at build time
- Must match database state exactly

Volume mounts are designed for **code hot-reload**:
- Great for Python/JS files that change during development
- Bad for stateful files that need to match image build

---

## Related Documentation

- [Migration Procedures](../database/MIGRATION_PROCEDURES.md)
- [Docker Compose Configuration](../development/docker-setup.md)
- [Incident Report (Internal)](.claude/dontreadme/incidents/INC-2026-001_ALEMBIC_VOLUME_SYNC.md)

---

## Timeline

| Date | Event |
|------|-------|
| 2025-12-26 | First merge migration needed for divergent heads |
| 2025-12-31 | Intermittent errors observed during development |
| 2026-01-01 | Root cause identified, PR #596 merged |
| 2026-01-01 | All development environments updated |

---

*Last Updated: 2026-01-01*
