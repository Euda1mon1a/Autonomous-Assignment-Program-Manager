# Pattern: Docker Volume Exclusions for Stateful Directories

> **Pattern ID:** DOCKER-001
> **Category:** Infrastructure / Docker
> **Discovered:** 2026-01-01 (Incident INC-2026-001)
> **Status:** VALIDATED

---

## The Pattern

When bind-mounting directories for hot-reload in Docker development environments, **exclude stateful subdirectories** using anonymous volumes.

```yaml
volumes:
  - ./backend:/app              # Bind mount for hot-reload
  - /app/__pycache__            # Exclude: bytecode cache
  - /app/.pytest_cache          # Exclude: test cache
  - /app/alembic/versions       # Exclude: migrations (CRITICAL)
  - /app/node_modules           # Exclude: if applicable
```

---

## Why This Matters

### Stateful vs Stateless Files

| Type | Examples | Volume Mount? |
|------|----------|---------------|
| **Stateless Code** | `*.py`, `*.ts`, `*.html` | YES - hot reload |
| **Stateful Config** | `alembic/versions/`, `migrations/` | NO - use image |
| **Generated Cache** | `__pycache__/`, `.pytest_cache/` | NO - container-local |
| **Dependencies** | `node_modules/`, `venv/` | NO - use image or named volume |

### The Failure Mode

Without exclusions:
1. `docker build` bakes correct state into image
2. `docker compose up` overlays host directory
3. Host directory may be stale/different
4. Container sees wrong state → **FAILURE**

---

## Application to This Codebase

### Files Updated (PR #596)

| File | Exclusions Added |
|------|------------------|
| `docker-compose.dev.yml` | `/app/alembic/versions` |
| `docker-compose.local.yml` | `/app/alembic/versions` (3 services) |

### Services Affected

- `backend` - runs migrations on startup
- `celery-worker` - imports models that depend on migrations
- `celery-beat` - imports models that depend on migrations

---

## Detection Checklist

When debugging Docker development issues, check:

- [ ] Are stateful directories excluded from bind mounts?
- [ ] Do container and host have same file versions?
- [ ] Does rebuilding (`--build`) fix the issue?
- [ ] Does issue recur after restart but not rebuild?

If YES to last two → **Volume mount masking stateful files**

---

## Related Patterns

| Pattern | Description |
|---------|-------------|
| Named Volumes for Dependencies | Use `venv:/app/venv` instead of bind mount |
| Multi-stage Builds | Copy only needed files, exclude dev artifacts |
| .dockerignore | Prevent COPY of unwanted files |

---

## Cross-References

- **Incident Report:** `.claude/dontreadme/incidents/INC-2026-001_ALEMBIC_VOLUME_SYNC.md`
- **Human Docs:** `docs/troubleshooting/ALEMBIC_VOLUME_SYNC_ISSUE.md`
- **PR:** #596 - Prevent alembic migrations from being overwritten
- **Skill:** `.claude/skills/database-migration/SKILL.md`
- **Skill:** `.claude/skills/docker-containerization/troubleshooting.md`

---

## Agent Instructions

When working with Docker volume configurations:

1. **Before modifying docker-compose volumes:**
   - Check for existing exclusion patterns
   - Identify stateful directories that need exclusion

2. **When debugging migration issues:**
   - First check volume mount configuration
   - Compare `alembic heads` between host and container
   - Rebuild with `--no-cache` to test

3. **When creating new services:**
   - Copy volume exclusion pattern from existing services
   - Include at minimum: `__pycache__`, `alembic/versions`

---

*Pattern documented by COORD_INTEL, 2026-01-01*
