# INCIDENT REPORT: Alembic Migration Sync Failure

## Classification

| Field | Value |
|-------|-------|
| **Incident ID** | INC-2026-001 |
| **Severity** | P2 (Infrastructure) |
| **Status** | RESOLVED |
| **Duration** | 2025-12-26 to 2026-01-01 (~6 days intermittent) |
| **Affected Systems** | Docker development environment, Alembic migrations |
| **Resolution PR** | #596 |

---

## Executive Summary

Development mode Docker volume mounting (`./backend:/app`) was silently overwriting container-resident Alembic migrations with potentially stale local copies. This caused broken migration chains and spurious "migration not found" errors on every container restart or rebuild, particularly affecting the `20251231_rotation_colors` migration. The issue manifested intermittently over 6 days before root cause analysis identified the volume mount as the culprit.

---

## Timeline

| Date | Time (HST) | Event | Evidence |
|------|------------|-------|----------|
| 2025-12-26 | -- | Custom rotation colors feature merged | PR #466, commit `413a7db6` |
| 2025-12-26 | -- | Alembic merge migration created for divergent heads | commit `7631bfc5`, `e46cd3bee350` |
| 2025-12-31 | -- | `rotation_colors` migration created in LOCAL BURN | PR #571, commit `47f2e508` |
| 2025-12-31 | -- | Intermittent migration errors observed | Session notes |
| 2026-01-01 | 12:17 | Session 046 Surgical Time Out initiated | Database backup created |
| 2026-01-01 | 12:22 | Root cause identified: volume mount overwrite | Commit `76f0fa77` |
| 2026-01-01 | 12:23 | Fix merged | PR #596 |
| 2026-01-01 | 13:54 | Full system recovery confirmed | Container health checks pass |

---

## Root Cause

### Technical Details

Docker Compose development configurations mount the entire backend directory into containers:

```yaml
# BEFORE fix (docker-compose.dev.yml and docker-compose.local.yml)
volumes:
  - ./backend:/app
  - /app/__pycache__  # Excluded
  # /app/alembic/versions was NOT excluded
```

This meant:

1. **On `docker compose build`**: Container image includes all migrations from the Dockerfile's COPY instruction
2. **On `docker compose up`**: Volume mount overlays local `./backend` over container's `/app`, including `./backend/alembic/versions` over `/app/alembic/versions`
3. **Consequence**: If local migrations were stale, missing, or from a different branch, container saw broken migration chain
4. **Symptoms**: `alembic upgrade head` failures, "Can't locate revision" errors, ghost migrations appearing/disappearing

### Why Detection Was Delayed

- Issue was **intermittent**: Only manifested when local and container migration states diverged
- **Masking**: Developers running `git pull` would sync migrations, temporarily fixing the issue
- **Misdirection**: Errors blamed on migration order, branch conflicts, or Alembic bugs rather than infrastructure

---

## Contributing Factors

1. **Parallel Development Branches**: Multiple sessions creating migrations on different branches led to divergent migration histories (necessitating merge migrations like `e46cd3bee350`)

2. **CCW Parallel Burns**: High-velocity Claude Code Worker burns created many changes rapidly, making it difficult to isolate when the issue started

3. **Volume Mount Pattern Inconsistency**: `__pycache__` was already excluded from volume mounts, but the same pattern wasn't applied to `alembic/versions`

4. **Missing Container State Visibility**: No monitoring for migration state divergence between host and container

---

## Resolution

### PR #596: Prevent Alembic Migrations from Being Overwritten by Volume Mounts

**Files Changed:**

1. **`docker-compose.dev.yml`**
   ```yaml
   volumes:
     - ./backend:/app
     - /app/__pycache__
     - /app/alembic/versions  # ADDED
   ```

2. **`docker-compose.local.yml`** (3 services updated)
   - `backend` service (line 126)
   - `celery-worker` service (line 166)
   - `celery-beat` service (line 206)

**Mechanism**: Anonymous volume exclusion (`- /app/alembic/versions`) tells Docker to NOT overlay that path with the bind mount, preserving the container's built-in migrations.

---

## Lessons Learned

1. **Volume Mount Exclusions Are Critical**: When bind-mounting entire directories for hot reload, stateful subdirectories (migrations, caches, generated files) must be explicitly excluded

2. **Container State vs Host State**: Docker development patterns that work for code files can break stateful directories like migrations

3. **Similar Pattern Already Existed**: `__pycache__` exclusion should have been a template for `alembic/versions` exclusion

4. **Intermittent Issues Need Infrastructure Review**: When debugging issues that "sometimes work," examine container/volume configuration before application logic

---

## Preventive Measures Implemented

1. **Volume Exclusions Added**: All three development Docker Compose files now exclude `alembic/versions` from bind mounts

2. **Documentation Created**: Session 046 handoff document captures the pattern for future reference

3. **Git Tag Created**: `pre-sterile-reset-20260101` marks the state before the surgical reset for potential rollback reference

---

## Recommended Follow-ups

- [ ] **Add CI Check**: Validate that `docker-compose.*.yml` files exclude `alembic/versions` from any `./backend:/app` volume mounts
- [ ] **Pre-commit Hook**: Consider adding a hook that warns when modifying Docker volume configurations without migration exclusions
- [ ] **Documentation**: Add volume mount best practices to `CLAUDE.md` or Docker documentation
- [ ] **Health Check Enhancement**: Add migration state validation to container health checks (compare expected head revision)
- [ ] **Consider Named Volumes**: For more explicit control, consider using named volumes for migrations instead of anonymous volume exclusions

---

## Artifacts

### Evidence Files

| File | Purpose |
|------|---------|
| `.claude/History/sessions/SESSION_046_SURGICAL_TIMEOUT.md` | Session narrative |
| `.claude/Scratchpad/SESSION_046_HANDOFF.md` | Surgical reset procedure |
| `.claude/dontreadme/sessions/SESSION_2025-12-26_ALEMBIC_MERGE.md` | Earlier merge migration context |
| `.claude/dontreadme/sessions/SESSION_2025-12-26_COLORS_AND_SPLITS.md` | Feature that surfaced the issue |

### Key Commits

| Commit | Description |
|--------|-------------|
| `413a7db6` | Added custom rotation colors (introduced migration complexity) |
| `7631bfc5` | Alembic merge migration for divergent heads |
| `47f2e508` | LOCAL BURN created rotation_colors migration |
| `8f14700c` | **Resolution**: Volume mount exclusions added |

### PRs

| PR | Title | Status |
|----|-------|--------|
| #466 | Session 15 Colors and Splits | Merged 2025-12-26 |
| #571 | LOCAL BURN blockers fix | Merged 2025-12-31 |
| #596 | **Fix: Prevent Alembic migrations from being overwritten** | Merged 2026-01-01 |
| #597 | Surgical Time Out - CCW import fixes | Merged 2026-01-01 |

---

## Appendix: Technical Deep Dive

### How Docker Volume Exclusions Work

```yaml
volumes:
  - ./backend:/app           # Bind mount: host -> container
  - /app/__pycache__         # Anonymous volume: container-only, NOT overlaid by bind mount
  - /app/alembic/versions    # Anonymous volume: container-only, NOT overlaid by bind mount
```

When Docker processes these volume declarations:

1. `./backend:/app` mounts the host's `./backend` directory to container's `/app`
2. `/app/__pycache__` creates an anonymous volume at that path, which takes precedence over the bind mount
3. The anonymous volume starts with content from the container image, not from the host

This pattern is documented in Docker's [volume documentation](https://docs.docker.com/storage/volumes/) under "Populate a volume using a container."

### Migration State Verification Command

```bash
# Check container's migration head vs expected
docker compose exec backend alembic heads
docker compose exec backend alembic current

# Compare to local
cd backend && alembic heads && alembic current
```

---

*Report Generated: 2026-01-01*
*Investigator: COORD_INTEL (Full-stack Forensics & Investigation)*
*Classification: Internal - Technical*
