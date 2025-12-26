# Schedule Generation Runbook

> **Purpose:** Step-by-step guide for directing Claude Code to verify infrastructure and generate a schedule with human-readable verification.

---

## Quick Reference Commands

Copy these prompts to direct Claude Code:

```
Step 1: "Check if all Docker containers are running and healthy"
Step 2: "Verify database connectivity and show me the counts of people, blocks, and rotations"
Step 3: "Run the health check endpoints and show me the results"
Step 4: "Generate a schedule for Block 10 (2026-03-10 to 2026-04-06) using the CP-SAT algorithm"
Step 5: "Verify the generated schedule and show me any violations"
Step 6: "Show me a human-readable summary of the schedule"
```

---

## Detailed Steps

### Step 1: Verify Docker Containers

**Prompt to Claude Code:**
```
Check all Docker containers are running. Show me:
1. Container names and their status
2. Health check status for db, redis, backend, and celery-worker
3. Any containers that are not healthy
```

**What Claude Code should run:**
```bash
docker-compose ps
docker-compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Health}}"
```

**Expected Output (Healthy):**
| Container | Status | Health |
|-----------|--------|--------|
| db | Up | healthy |
| redis | Up | healthy |
| backend | Up | running |
| celery-worker | Up | healthy |
| celery-beat | Up | running |
| mcp-server | Up | healthy |
| frontend | Up | running |

**If NOT healthy:**
```bash
# Restart unhealthy containers
docker-compose restart <container-name>

# View logs for troubleshooting
docker-compose logs -f <container-name>
```

---

### Step 2: Verify Database Connectivity

**Prompt to Claude Code:**
```
Connect to the database and show me:
1. Can you connect successfully?
2. How many people (residents/faculty) exist?
3. How many blocks are defined?
4. How many rotation templates exist?
5. Are there any existing assignments?
```

**What Claude Code should run:**
```bash
# Test database connection
docker-compose exec db psql -U scheduler -d residency_scheduler -c "SELECT 1 as connected;"

# Count core entities
docker-compose exec db psql -U scheduler -d residency_scheduler -c "
SELECT
  (SELECT COUNT(*) FROM persons) as people_count,
  (SELECT COUNT(*) FROM blocks) as blocks_count,
  (SELECT COUNT(*) FROM rotation_templates) as rotation_templates_count,
  (SELECT COUNT(*) FROM assignments) as assignments_count;
"

# Show people breakdown by role
docker-compose exec db psql -U scheduler -d residency_scheduler -c "
SELECT role, COUNT(*) FROM persons GROUP BY role ORDER BY role;
"
```

**Expected Output (Healthy):**
```
 people_count | blocks_count | rotation_templates_count | assignments_count
--------------+--------------+--------------------------+-------------------
           15 |          730 |                       12 |               500
```

**Minimum Requirements:**
- `people_count` > 0 (need residents/faculty)
- `blocks_count` > 0 (need time slots)
- `rotation_templates_count` > 0 (need rotation types)

---

### Step 3: Run Health Check Endpoints

**Prompt to Claude Code:**
```
Call the backend health check endpoints and show me:
1. Is the backend alive? (/api/v1/health/live)
2. Is the backend ready to accept requests? (/api/v1/health/ready)
3. What's the detailed health status? (/api/v1/health/detailed)
```

**What Claude Code should run:**
```bash
# Liveness (basic)
curl -s http://localhost:8000/api/v1/health/live | python -m json.tool

# Readiness (with dependencies)
curl -s http://localhost:8000/api/v1/health/ready | python -m json.tool

# Detailed (all services)
curl -s http://localhost:8000/api/v1/health/detailed | python -m json.tool
```

**Expected Output (Healthy):**
```json
{
  "status": "healthy",
  "services": {
    "database": {"status": "healthy", "latency_ms": 2.5},
    "redis": {"status": "healthy", "latency_ms": 1.2},
    "celery": {"status": "healthy", "workers": 1}
  }
}
```

**If NOT healthy:**
- `database: unhealthy` → Check postgres container logs
- `redis: unhealthy` → Check redis container logs
- `celery: unhealthy` → Restart celery-worker container

---

### Step 4: Generate a Schedule

**Prompt to Claude Code:**
```
Generate a schedule for Block 10 (March 10 - April 6, 2026) using:
- CP-SAT algorithm (best quality)
- 5-minute timeout
- All PGY levels (1, 2, 3)

Show me the API response and whether it succeeded.
```

**What Claude Code should run:**
```bash
# Generate with idempotency key to prevent duplicates
curl -X POST http://localhost:8000/api/v1/schedule/generate \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: block10-$(date +%Y%m%d-%H%M%S)" \
  -d '{
    "start_date": "2026-03-10",
    "end_date": "2026-04-06",
    "algorithm": "cp_sat",
    "pgy_levels": [1, 2, 3],
    "timeout_seconds": 300
  }' | python -m json.tool
```

**Response Codes:**
| Code | Meaning | Action |
|------|---------|--------|
| 200 | Success - all assignments created | Proceed to verification |
| 207 | Partial success - some violations | Review violations, may be acceptable |
| 422 | Failed - could not generate | Check error message, adjust constraints |
| 409 | Conflict - duplicate request | Idempotency key already used |

**Expected Response (Success):**
```json
{
  "status": "success",
  "assignments_created": 168,
  "violations": [],
  "coverage": {
    "total_slots": 168,
    "filled_slots": 168,
    "percentage": 100.0
  },
  "execution_time_seconds": 45.2
}
```

---

### Step 5: Verify the Generated Schedule

**Prompt to Claude Code:**
```
Verify the generated schedule:
1. Run ACGME compliance validation
2. Check for any violations or conflicts
3. Run the schedule verification script
Show me any issues found.
```

**What Claude Code should run:**
```bash
# API validation endpoint
curl -s "http://localhost:8000/api/v1/schedule/validate?start_date=2026-03-10&end_date=2026-04-06" \
  | python -m json.tool

# Comprehensive verification script
docker-compose exec backend python ../scripts/verify_schedule.py \
  --block 10 \
  --start 2026-03-10 \
  --end 2026-04-06
```

**Expected Output (Clean):**
```
=== Block 10 Schedule Verification ===
Date Range: 2026-03-10 to 2026-04-06 (28 days)

FMIT Rotation Check:
  ✓ No back-to-back FMIT weeks for faculty
  ✓ FMIT faculty have Fri+Sat call coverage
  ✓ Post-FMIT Sundays blocked appropriately

Night Float Check:
  ✓ Exactly 1 resident on Night Float each night

ACGME Compliance:
  ✓ 80-hour weekly limit: All residents compliant
  ✓ 1-in-7 day off rule: All residents compliant
  ✓ Supervision ratios: All requirements met

Conflict Check:
  ✓ No double-bookings detected
  ✓ No absence conflicts (leave/TDY respected)

OVERALL: ✓ PASSED - Schedule is valid
```

**If violations found:**
```
VIOLATIONS FOUND:
  ✗ PGY1-03: Exceeds 80 hours in week of 2026-03-15 (82.5 hrs)
  ✗ PGY2-01: Missing day off in 7-day period ending 2026-03-20

Recommended Actions:
  1. Review assignments for PGY1-03 on 2026-03-15 to 2026-03-21
  2. Add rest day for PGY2-01 before 2026-03-20
```

---

### Step 6: Human-Readable Schedule Summary

**Prompt to Claude Code:**
```
Show me a human-readable summary of the schedule:
1. Coverage by rotation type
2. Work distribution by resident
3. Any warnings or concerns
Format it as a table I can review.
```

**What Claude Code should run:**
```bash
# Get schedule data
curl -s "http://localhost:8000/api/v1/schedule/2026-03-10/2026-04-06" \
  | python -m json.tool

# Or query directly for summary
docker-compose exec db psql -U scheduler -d residency_scheduler -c "
-- Coverage by rotation
SELECT
  rt.name as rotation,
  COUNT(a.id) as assignments,
  COUNT(DISTINCT p.id) as unique_people
FROM assignments a
JOIN rotation_templates rt ON a.rotation_template_id = rt.id
JOIN persons p ON a.person_id = p.id
JOIN blocks b ON a.block_id = b.id
WHERE b.date BETWEEN '2026-03-10' AND '2026-04-06'
GROUP BY rt.name
ORDER BY assignments DESC;

-- Work distribution by person
SELECT
  p.name as person,
  p.role,
  COUNT(a.id) as total_assignments,
  SUM(CASE WHEN rt.name LIKE '%Call%' THEN 1 ELSE 0 END) as call_shifts
FROM persons p
LEFT JOIN assignments a ON p.id = a.person_id
LEFT JOIN blocks b ON a.block_id = b.id
LEFT JOIN rotation_templates rt ON a.rotation_template_id = rt.id
WHERE b.date BETWEEN '2026-03-10' AND '2026-04-06'
GROUP BY p.id, p.name, p.role
ORDER BY p.role, total_assignments DESC;
"
```

**Expected Output:**
```
=== Coverage by Rotation ===
| Rotation          | Assignments | Unique People |
|-------------------|-------------|---------------|
| Inpatient         | 56          | 6             |
| Clinic            | 48          | 12            |
| Night Float       | 28          | 2             |
| FMIT              | 20          | 4             |
| Procedures        | 16          | 8             |

=== Work Distribution ===
| Person   | Role     | Total | Call Shifts |
|----------|----------|-------|-------------|
| PGY1-01  | RESIDENT | 24    | 4           |
| PGY1-02  | RESIDENT | 24    | 4           |
| PGY2-01  | RESIDENT | 22    | 3           |
| ...      | ...      | ...   | ...         |

=== Balance Analysis ===
✓ Standard deviation of assignments: 1.8 (good balance)
✓ No resident has >6 call shifts (limit: 7)
✓ Call shifts evenly distributed across weekends
```

---

## Troubleshooting

### Container Won't Start
```bash
# View logs
docker-compose logs <container-name>

# Rebuild container
docker-compose up -d --build <container-name>

# Reset everything
docker-compose down -v
docker-compose up -d
```

### Database Connection Failed
```bash
# Check if postgres is accepting connections
docker-compose exec db pg_isready -U scheduler

# Reset database (WARNING: destroys data)
docker-compose exec db psql -U scheduler -d postgres -c "DROP DATABASE residency_scheduler;"
docker-compose exec db psql -U scheduler -d postgres -c "CREATE DATABASE residency_scheduler;"
docker-compose exec backend alembic upgrade head
```

### Schedule Generation Timeout
```bash
# Try with longer timeout
curl -X POST http://localhost:8000/api/v1/schedule/generate \
  -d '{"timeout_seconds": 600, ...}'

# Or use greedy algorithm (faster, lower quality)
curl -X POST http://localhost:8000/api/v1/schedule/generate \
  -d '{"algorithm": "greedy", ...}'
```

### Violations After Generation
```bash
# Check specific violations
curl -s "http://localhost:8000/api/v1/schedule/validate?start_date=2026-03-10&end_date=2026-04-06"

# Run conflict detection with resolution suggestions
curl -s http://localhost:8000/api/v1/schedule/conflicts/2026-03-10/2026-04-06
```

---

## Pre-Generation Checklist

Before running schedule generation, verify:

- [ ] All containers are running (`docker-compose ps`)
- [ ] Database has people loaded (`persons` table not empty)
- [ ] Database has blocks defined (`blocks` table not empty)
- [ ] Rotation templates exist (`rotation_templates` table not empty)
- [ ] Health endpoints return healthy status
- [ ] No active solver already running (`/api/v1/scheduler/runs/active`)

---

## Post-Generation Checklist

After schedule generation:

- [ ] API returned 200 or 207 status
- [ ] Coverage percentage > 95%
- [ ] ACGME validation passed (no violations)
- [ ] Verification script shows all green checks
- [ ] Work distribution is balanced across residents
- [ ] Call shifts are evenly distributed
- [ ] No absence conflicts (leave/TDY respected)

---

## Emergency: Abort Running Solver

If schedule generation is taking too long or behaving unexpectedly:

```bash
# Find active runs
curl -s http://localhost:8000/api/v1/scheduler/runs/active

# Abort specific run
curl -X POST http://localhost:8000/api/v1/scheduler/runs/{run_id}/abort \
  -H "Content-Type: application/json" \
  -d '{"reason": "Manual abort - taking too long", "requested_by": "admin"}'
```

---

## Related Documentation

- [Solver Algorithm](../architecture/SOLVER_ALGORITHM.md) - How the scheduling engine works
- [ACGME Compliance](../../CLAUDE.md#acgme-compliance-rules) - Compliance requirements
- [Safe Schedule Generation Skill](../../.claude/skills/safe-schedule-generation/SKILL.md) - AI-assisted generation with backup
