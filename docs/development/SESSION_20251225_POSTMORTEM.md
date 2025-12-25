# Session Postmortem: 2025-12-25 Block 10 Development

> **Date:** 2025-12-25
> **Duration:** Extended session (multiple context windows)
> **Outcome:** SUCCESS - Block 10 schedule generation verified

---

## Executive Summary

Session began with database in broken state (schema mismatch from prior session's backup restore). After full database rebuild and constraint code injection via docker cp, successfully generated and validated Block 10 schedule with all 25 constraints active.

---

## What Went Well

### 1. Backup Isolation Design

**Saved the day:** Backups stored at `backups/postgres/` on local filesystem, completely separate from Docker volume `postgres_data`.

When we ran `docker volume rm postgres_data`, all backups remained intact. This isolation was intentional and proved critical.

**Lesson:** Keep backups outside of containerized storage.

### 2. Database Rebuild (Option A) Success

Full rebuild worked cleanly:
```
docker-compose down
docker volume rm autonomous-assignment-program-manager_postgres_data
docker-compose up -d db redis backend celery-worker celery-beat frontend
alembic upgrade head  # 30 migrations applied
```

**Result:** Clean schema, no mismatch issues.

### 3. Constraint Verification Tooling

The pre-flight verification script (`scripts/verify_constraints.py`) and CI tests (`test_constraint_registration.py`) correctly identified missing constraints.

When only 18 constraints were registered (missing Block 10), the tools caught it immediately.

### 4. Docker CP Workaround

When Docker build failed with pip resolution errors, the docker cp pattern worked flawlessly:
- Copied 6 constraint files into running container
- Restarted backend
- All 25 constraints registered

**Time saved:** ~15 minutes (vs rebuilding images).

### 5. Schedule Generation Success

Block 10 schedule generation:
- 87 assignments created
- 0 violations
- 112.5% coverage
- 0 conflicts
- 0 ACGME overrides

**Validates:** All Block 10 constraints working correctly.

---

## What Didn't Go Well

### 1. Schema Mismatch Discovery

**Issue:** Database backup was from newer schema than current database state.

**Root cause:** Prior session restored backup without verifying Alembic version compatibility.

**Impact:** 2+ hours debugging cryptic API errors before identifying schema mismatch.

**Prevention:** Implemented schema version tracking (new feature this session).

### 2. Docker Build Failures

**Issue:** `pip install` failed with "ResolutionTooDeep" error.

**Root cause:** Complex dependency tree in requirements.txt, possibly transient network issues.

**Impact:** Couldn't rebuild Docker images normally.

**Workaround:** Used docker cp pattern instead.

**Future fix:** Consider pinning all transitive dependencies.

### 3. docker-compose.local.yml Bug

**Issue:** Local override file had migration bug (ON CONFLICT without unique constraint).

**Root cause:** Stale configuration from earlier development.

**Impact:** 10 minutes debugging before reverting to standard docker-compose.yml.

**Fix:** Removed buggy override file.

### 4. Password Complexity Rejection

**Issue:** Initial admin password "admin123" rejected.

**Root cause:** Password policy requires 12+ chars with 3 of 4 character types.

**Impact:** Minor - just needed stronger password.

**Resolution:** Used "SecureP@ss1234" (meets all requirements).

### 5. Seed Scripts Not in Container

**Issue:** Seed scripts assume local Python environment, not containerized.

**Root cause:** Scripts use `requests` to call API, not database directly.

**Workaround:** Installed requests locally, ran from host machine.

**Future fix:** Add seed scripts to container or provide container-native seeding.

---

## Key Decisions Made

### Decision 1: Full Rebuild vs Restore

**Chose:** Full rebuild (Option A)

**Rationale:**
- Guarantees clean schema state
- No risk of hidden inconsistencies
- Fresh seed data is synthetic (no PII concerns)

### Decision 2: Docker CP vs Rebuild Images

**Chose:** Docker CP

**Rationale:**
- Faster (seconds vs 10+ minutes)
- Avoids pip resolution issues
- Sufficient for development iteration

### Decision 3: Exclude n8n from Docker Compose

**Chose:** Exclude n8n service

**Rationale:**
- n8n unused in current workflow
- Generates significant log noise
- Reduces resource usage

---

## Metrics

| Metric | Value |
|--------|-------|
| Database migrations applied | 30 |
| People seeded | 28 |
| Rotation templates seeded | 32 |
| Blocks seeded | 730 |
| Constraints registered | 25 |
| Block 10 constraints | 6 |
| Schedule assignments generated | 87 |
| Validation violations | 0 |
| Docker cp operations | 6 files |

---

## Action Items Generated

### Completed This Session

- [x] Database rebuild with clean schema
- [x] Block 10 constraint verification
- [x] Schedule generation test
- [x] Schema version tracking feature (columns added, migration created)
- [x] Backup script enhanced with version metadata capture

### Future Work

- [ ] Implement restore-time version validation
- [ ] Add container-native seed scripts
- [ ] Pin all transitive pip dependencies
- [ ] Clean up docker-compose.local.yml

---

## Artifacts Created

### New Files

| File | Purpose |
|------|---------|
| `docs/development/DOCKER_WORKAROUNDS.md` | Docker cp pattern documentation |
| `docs/development/SCHEMA_VERSION_TRACKING.md` | Version tracking feature docs |
| `docs/development/BLOCK10_CONSTRAINTS_TECHNICAL.md` | Constraint implementation details |
| `docs/development/SESSION_20251225_POSTMORTEM.md` | This document |
| `docs/development/LOCAL_DEVELOPMENT_RECOVERY.md` | Recovery procedures |
| `backend/alembic/versions/20251225_add_schema_versioning.py` | Schema versioning migration |

### Modified Files

| File | Change |
|------|--------|
| `backend/app/models/settings.py` | Added alembic_version, schema_timestamp columns |
| `scripts/backup-db.sh` | Added capture_version_metadata() function |

---

## Timeline

| Time | Event |
|------|-------|
| Start | Discovered schema mismatch from prior session |
| +15m | Identified backup location safe from volume rm |
| +30m | Completed database rebuild |
| +45m | Admin user registered, seeds applied |
| +60m | Discovered only 18 constraints (Block 10 missing) |
| +75m | Docker build failed, switched to docker cp |
| +90m | All 25 constraints registered |
| +105m | Block 10 schedule generated successfully |
| +120m | Schema versioning feature implemented |
| +135m | Documentation creation started |

---

## Lessons for Future Sessions

1. **Always verify Alembic version before backup restore**
2. **Docker cp is a valid development workaround**
3. **Keep backups on local filesystem, not in Docker volumes**
4. **Run constraint verification before schedule generation**
5. **Exclude unused services from docker-compose up**

---

## Related Documentation

- [SESSION_HANDOFF_20251225.md](SESSION_HANDOFF_20251225.md) - Full handoff notes
- [DOCKER_WORKAROUNDS.md](DOCKER_WORKAROUNDS.md) - Docker cp pattern
- [SCHEMA_VERSION_TRACKING.md](SCHEMA_VERSION_TRACKING.md) - Version tracking feature
- [BLOCK10_CONSTRAINTS_TECHNICAL.md](BLOCK10_CONSTRAINTS_TECHNICAL.md) - Constraint details
