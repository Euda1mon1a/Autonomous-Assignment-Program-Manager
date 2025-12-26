# Session Summary: Docker Rebuild & Block Structure

> **Date:** 2025-12-26 (HST)
> **Focus:** Container verification, schedule generation debugging, Block 0 creation

---

## Issues Investigated

### 1. Docker Container Rebuild Verification

**Question:** Were all containers rebuilt fresh?

**Findings:**
- All custom images built today (Dec 25 HST / Dec 26 UTC)
- Backend: 19:18, Celery: 19:10, Frontend: 18:30
- Base images (postgres:15-alpine, redis:7-alpine) are official Docker Hub pulls
- celery-beat "unhealthy" status is healthcheck timing mismatch, not actual failure

**Services Running:**
| Container | Status | Port |
|-----------|--------|------|
| backend | healthy | 8000 |
| celery-beat | unhealthy (cosmetic) | - |
| celery-worker | healthy | - |
| frontend | healthy | 3000 |
| db (postgres) | healthy | 5432 |
| redis | healthy | 6379 |

**Stopped:**
- mcp-server (crash loop issue)
- n8n (not needed)

---

### 2. .env Propagation

**Question:** Are environment variables propagating to containers?

**Verified:**
```bash
docker exec residency-scheduler-backend printenv | grep RATE_LIMIT
# Output: RATE_LIMIT_ENABLED=false
```

**Result:** Working correctly. The `RATE_LIMIT_ENABLED` variable added to docker-compose.yml is propagating.

---

### 3. Schedule Generation Bug

**Symptom:** Schedule generation failing with `UniqueViolation` error:
```
duplicate key value violates unique constraint "unique_person_per_block"
```

**Root Cause:** `backend/app/scheduling/engine.py` line 1186 defines `_delete_existing_assignments()` but it is **never called**.

The comment at line 186 says "see Step 5.5" but no Step 5.5 exists in the code.

**Workaround Applied:**
```sql
DELETE FROM assignments
WHERE block_id IN (
  SELECT id FROM blocks
  WHERE date >= '2026-03-12' AND date <= '2026-04-08'
);
-- Deleted 80 assignments
```

**Result:** After clearing, schedule generation succeeded (86 assignments).

**Fix Required:** Add call to `self._delete_existing_assignments(preserve_ids)` in the generate() method before inserting new assignments.

---

### 4. Academic Year Block Structure

**Question:** What is the block structure for the academic year?

**Structure Discovered:**

| Block | Start | End | Days | Pattern |
|-------|-------|-----|------|---------|
| 0 | Jul 1 (Tue) | Jul 2 (Wed) | 2 | Orientation |
| 1-12 | Thursday | Wednesday | 28 | Standard |
| 13 | Jun 4 (Thu) | Jun 30 (Tue) | 27 | AY cutoff |

**Key Rules:**
- Academic Year: July 1 - June 30
- Blocks always start Thursday, end Wednesday
- Exception: Block 0 (orientation) and Block 13 (AY end cutoff)
- Each day has AM and PM blocks (2 blocks per day)
- Total: 730 blocks for full AY

---

## Changes Made

### Database Changes

**Block 0 Added:**
```sql
INSERT INTO blocks (id, date, time_of_day, block_number, is_weekend, is_holiday)
VALUES
  (gen_random_uuid(), '2025-07-01', 'AM', 0, false, false),
  (gen_random_uuid(), '2025-07-01', 'PM', 0, false, false),
  (gen_random_uuid(), '2025-07-02', 'AM', 0, false, false),
  (gen_random_uuid(), '2025-07-02', 'PM', 0, false, false);
```

**Purpose:**
- Cover Jul 1-2 before Block 1 starts (Jul 3)
- Orientation/admin days
- Provides pattern for leap year flexibility

---

## Uncommitted File Changes

| File | Change |
|------|--------|
| `backend/Dockerfile` | Added libmagic1, legacy-resolver for pip |
| `backend/app/main.py` | Conditional rate limiting toggle |
| `backend/app/schemas/rotation_template.py` | Schema updates |
| `backend/docker-entrypoint.sh` | Added celery support |
| `backend/requirements.txt` | Deduplicated scipy/ndlib |
| `docker-compose.yml` | Added RATE_LIMIT_ENABLED env var |
| `scripts/generate_blocks.py` | Script updates |
| `test_schedule.sh` | New test script for schedule generation |

---

## Pending Work

1. **Fix engine.py bug** - Add `_delete_existing_assignments()` call
2. **Create Alembic migration** - For Block 0 logic (reproducibility)
3. **Document block structure** - In docs/architecture/
4. **Commit Docker changes** - To feature branch

---

## Leap Year Consideration

Block 0 pattern provides flexibility for leap years:
- AY 2027-2028 includes Feb 29, 2028 (366 days)
- Extra day can be absorbed by extending Block 0 or creating adjustment block
- Keeps Blocks 1-13 at consistent lengths

---

## Commands Used

```bash
# Check container status
docker compose ps -a

# Check image build times
docker images --format "table {{.Repository}}\t{{.CreatedAt}}" | grep autonomous

# Verify env propagation
docker exec residency-scheduler-backend printenv | grep RATE_LIMIT

# Check block structure
docker exec residency-scheduler-db psql -U scheduler -d residency_scheduler -c "
SELECT block_number, MIN(date), MAX(date), COUNT(*)/2 as days
FROM blocks GROUP BY block_number ORDER BY block_number;"

# Clear assignments for regeneration
docker exec residency-scheduler-db psql -U scheduler -d residency_scheduler -c "
DELETE FROM assignments WHERE block_id IN (
  SELECT id FROM blocks WHERE date >= '2026-03-12' AND date <= '2026-04-08'
);"

# Test schedule generation
bash test_schedule.sh
```
