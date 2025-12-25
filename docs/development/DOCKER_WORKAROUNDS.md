# Docker Workarounds: When Builds Fail

> **Created:** 2025-12-25
> **Context:** Block 10 development session encountered pip resolution failures

---

## Problem: Docker Build Fails with pip Resolution Errors

### Symptoms

```
ERROR: ResolutionTooDeep: 2000000
pip's dependency resolver tried to resolve dependencies too many times
```

This can occur when:
- Complex dependency trees in requirements.txt
- Network issues during pip install
- Conflicting version constraints

### Solution: Docker CP Workaround

Instead of rebuilding the entire image, inject updated files directly into running containers.

---

## The Docker CP Pattern

### 1. Identify What Changed

```bash
# Check which files need to be in the container
git diff --name-only HEAD~1 HEAD | grep "backend/app"
```

### 2. Copy Files Into Running Container

```bash
# Syntax: docker cp <host_path> <container>:<container_path>
docker cp backend/app/scheduling/constraints/manager.py \
  residency-scheduler-backend:/app/app/scheduling/constraints/manager.py
```

### 3. Restart the Container

```bash
docker-compose restart backend
```

---

## Real Example: Block 10 Constraint Files

During the 2025-12-25 session, Docker builds failed. We successfully injected constraint files:

```bash
# Copy all updated constraint files
docker cp backend/app/scheduling/constraints/manager.py \
  residency-scheduler-backend:/app/app/scheduling/constraints/manager.py

docker cp backend/app/scheduling/constraints/call_equity.py \
  residency-scheduler-backend:/app/app/scheduling/constraints/call_equity.py

docker cp backend/app/scheduling/constraints/fmit.py \
  residency-scheduler-backend:/app/app/scheduling/constraints/fmit.py

docker cp backend/app/scheduling/constraints/inpatient.py \
  residency-scheduler-backend:/app/app/scheduling/constraints/inpatient.py

docker cp backend/app/scheduling/constraints/night_float_post_call.py \
  residency-scheduler-backend:/app/app/scheduling/constraints/night_float_post_call.py

docker cp backend/app/scheduling/constraints/__init__.py \
  residency-scheduler-backend:/app/app/scheduling/constraints/__init__.py

# Restart to load new code
docker-compose restart backend
```

### Verification

```bash
# Check constraint registration in container
docker exec residency-scheduler-backend python3 -c "
from app.scheduling.constraints.manager import ConstraintManager
mgr = ConstraintManager.create_default()
print(f'Total constraints: {len(mgr.constraints)}')
for c in mgr.constraints:
    print(f'  - {c.__class__.__name__}')
"
```

---

## When to Use Docker CP vs Rebuild

| Scenario | Use Docker CP | Rebuild |
|----------|--------------|---------|
| Single file change | Yes | No |
| Multiple Python files | Yes | No |
| requirements.txt change | No | Yes |
| Dockerfile change | No | Yes |
| New package needed | No | Yes |
| Quick iteration | Yes | No |
| Production deployment | No | Yes |

---

## Finding Container Names

```bash
# List running containers
docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}"

# Common container names in this project
# - residency-scheduler-backend
# - residency-scheduler-frontend
# - residency-scheduler-db
# - residency-scheduler-redis
```

---

## Limitations

1. **Not persistent** - Container restart from image loses changes
2. **No dependency updates** - Can't add new pip packages
3. **Path sensitivity** - Must match exact container paths
4. **Development only** - Never use for production

---

## Alternative: Volume Mounts for Development

For frequent code changes, use volume mounts in `docker-compose.override.yml`:

```yaml
services:
  backend:
    volumes:
      - ./backend/app:/app/app:ro
```

This auto-syncs code changes without docker cp or rebuilds.

---

## Related Documentation

- [DEPLOYMENT_TROUBLESHOOTING.md](DEPLOYMENT_TROUBLESHOOTING.md) - General Docker issues
- [SESSION_HANDOFF_20251225.md](SESSION_HANDOFF_20251225.md) - Session context
