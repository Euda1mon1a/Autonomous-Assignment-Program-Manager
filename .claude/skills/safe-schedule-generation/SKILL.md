---
name: safe-schedule-generation
description: Safe schedule generation with mandatory backup. REQUIRES database backup before any write operations to schedule tables. Use when generating schedules, bulk assigning, or executing swaps.
model_tier: opus
parallel_hints:
  can_parallel_with: []
  must_serialize_with: [schedule-optimization, SCHEDULING, solver-control, swap-management]
  preferred_batch_size: 1
context_hints:
  max_file_context: 40
  compression_level: 1
  requires_git_context: false
  requires_db_context: true
escalation_triggers:
  - pattern: "backup.*fail|no.*backup"
    reason: "Backup failures block all schedule modifications"
  - pattern: "rollback|restore"
    reason: "Rollback operations require human oversight"
  - keyword: ["production", "live", "destroy", "clear"]
    reason: "Destructive operations require explicit human approval"
---

# Safe Schedule Generation Skill

**HARD GATE:** No schedule generation, bulk assignment, or destructive operation without verified backup.

## When This Skill Activates

- Generating new schedules via API or MCP
- Bulk assigning residents/faculty to rotations
- Executing swap requests
- Clearing or regenerating schedule blocks
- Any operation that modifies `assignments` table

## MANDATORY Pre-Flight Checklist

**ALL checks MUST pass before any database-modifying operation:**

### 1. Backup Verification
```bash
# Check most recent backup
ls -la backups/postgres/*.sql.gz | tail -1

# Verify backup is recent (created within last 2 hours)
find backups/postgres -name "*.sql.gz" -mmin -120 | head -1
```

**If no recent backup exists:**
```bash
./scripts/backup-db.sh --docker
```

### 2. Backend Health Check
```bash
curl -s http://localhost:8000/health | jq .
# Expected: {"status":"healthy","database":"connected"}
```

### 3. Data Verification
```bash
# Get auth token
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login/json \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}' | jq -r .access_token)

# Verify people exist
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/people?limit=5" | jq .total

# Verify rotation templates exist
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/rotation-templates" | jq 'length'
```

### 4. User Confirmation
Before proceeding, confirm with user:
> "Backup verified at [timestamp]. Proceed with schedule generation?"

## Backup Safety Rules

### Minimum Backup Policy
| Rule | Description |
|------|-------------|
| **Minimum 2 backups** | Never delete if only 2 remain |
| **Sacred backup** | First backup is protected, never auto-delete |
| **30-day retention** | Auto-cleanup requires user confirmation |
| **Pre-operation backup** | Always create before schedule modifications |

### Backup File Naming
```
residency_scheduler_YYYYMMDD_HHMMSS.sql.gz     # Regular backup
residency_scheduler_SACRED_20251223.sql.gz     # Protected baseline
residency_scheduler_pre-block-10_20260312.sql.gz  # Pre-operation marker
```

### Creating a Backup
```bash
# Standard backup (creates timestamped file, never overwrites)
./scripts/backup-db.sh --docker

# Verify
ls -la backups/postgres/ | tail -3
```

## Rollback Procedure

### Emergency Restore
If schedule generation fails or produces bad results:

```bash
# 1. Find the backup to restore
ls -la backups/postgres/*.sql.gz

# 2. Decompress (keeps original .gz)
gunzip -k backups/postgres/residency_scheduler_YYYYMMDD_HHMMSS.sql.gz

# 3. Restore to database
docker compose exec -T db psql -U scheduler -d residency_scheduler \
  < backups/postgres/residency_scheduler_YYYYMMDD_HHMMSS.sql

# 4. Verify restoration
docker compose exec db psql -U scheduler -d residency_scheduler \
  -c "SELECT COUNT(*) FROM assignments;"
```

### Partial Rollback (Specific Tables)
```bash
# Restore only assignments table
docker compose exec db psql -U scheduler -d residency_scheduler \
  -c "DELETE FROM assignments WHERE date BETWEEN '2026-03-12' AND '2026-04-08';"
# Then reimport from backup or regenerate
```

## Local Data Sources (PII - Never in Git)

If database needs complete reimport, source files are at:

| File | Location | Contents |
|------|----------|----------|
| Residents | `docs/data/airtable_residents.json` | Names, PGY levels |
| Faculty | `docs/data/airtable_faculty.json` | Names, roles |
| Resident Absences | `docs/data/airtable_resident_absences.json` | Leave, TDY |
| Faculty Absences | `docs/data/airtable_faculty_absences.json` | Time off |
| Rotations | `docs/data/airtable_rotation_templates.json` | Clinic definitions |
| Schedule | `docs/data/airtable_block_schedule.json` | Existing assignments |
| People CSV | `docs/data/people_import.csv` | Flat import format |

**CRITICAL:** These files contain real names. Never commit to repository.

## Schedule Generation Workflow

### Via Direct API
```bash
# 1. Create backup (MANDATORY)
./scripts/backup-db.sh --docker

# 2. Get auth token
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login/json \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}' | jq -r .access_token)

# 3. Generate schedule
curl -X POST http://localhost:8000/api/v1/schedule/generate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2026-03-12",
    "end_date": "2026-04-08",
    "algorithm": "cp_sat",
    "timeout_seconds": 120
  }'
```

### Via MCP Tool
```
Tool: generate_schedule
Input: {
  start_date: "2026-03-12",
  end_date: "2026-04-08",
  algorithm: "cp_sat",
  timeout_seconds: 120
}
```

**MCP tools MUST verify backup before execution.**

## Protected vs Safe Operations

### Database-Modifying (Require Backup)
| Operation | MCP Tool | Risk Level |
|-----------|----------|------------|
| Generate schedule | `generate_schedule` | HIGH |
| Execute swap | `execute_swap` | MEDIUM |
| Bulk assign | `bulk_assign` | HIGH |
| Clear assignments | N/A | CRITICAL |

### Read-Only (Always Safe)
| Operation | MCP Tool | Risk Level |
|-----------|----------|------------|
| Validate schedule | `validate_schedule` | NONE |
| Detect conflicts | `detect_conflicts` | NONE |
| Get swap candidates | `analyze_swap_candidates` | NONE |
| Check health | `health_check` | NONE |

## Success Metrics

After schedule generation, verify:

| Metric | Target | How to Check |
|--------|--------|--------------|
| ACGME Violations | < 5 | `validation.total_violations` |
| Coverage Rate | > 80% | `total_blocks_assigned / total_blocks` |
| N-1 Compliant | True | `resilience.n1_compliant` |
| No Errors | True | HTTP 200 response |

## Failure Recovery

### If Generation Fails Mid-Process
1. Note the error message
2. Do NOT retry immediately
3. Check backend health
4. Restore from backup if partial data written
5. Investigate root cause

### If Generation Produces Bad Schedule
1. Review violations in response
2. If > 10 violations: restore and adjust constraints
3. If < 10 violations: manual adjustment may be faster

### If Backend Crashes
```bash
# Restart backend
docker compose restart backend

# Verify health
curl http://localhost:8000/health

# Check if data corrupted
docker compose exec db psql -U scheduler -d residency_scheduler \
  -c "SELECT COUNT(*) FROM people;"
```

## Quick Reference Card

```
┌─────────────────────────────────────────────────────┐
│         SCHEDULE MODIFICATION DECISION TREE         │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Does this modify the database?                     │
│     NO  → Safe to proceed                           │
│     YES → Continue checks                           │
│                                                     │
│  Is there a recent backup (< 2 hours)?              │
│     NO  → CREATE BACKUP FIRST                       │
│     YES → Continue                                  │
│                                                     │
│  Is backend healthy?                                │
│     NO  → FIX BACKEND FIRST                         │
│     YES → Continue                                  │
│                                                     │
│  Has user confirmed?                                │
│     NO  → ASK USER                                  │
│     YES → Proceed with operation                    │
│                                                     │
│  After operation:                                   │
│     Check violations < 5                            │
│     Verify coverage > 80%                           │
│     If failed → RESTORE FROM BACKUP                 │
│                                                     │
└─────────────────────────────────────────────────────┘
```
