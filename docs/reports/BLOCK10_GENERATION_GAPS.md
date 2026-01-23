# Block 10 Schedule Generation: Gap Analysis

**Date:** 2026-01-23
**Purpose:** Document all known gaps that could cause Block 10 generation to fail
**Success Probability:** 45-55% (single attempt, no debugging)

---

## Executive Summary

A fresh Claude Code session with `/startupO-lite` attempting to generate Block 10 has moderate success probability. The main risks are:

1. **Data completeness** (70% success) - Missing activity codes cause silent failures
2. **Authentication** (80% success) - Token/session state uncertainty
3. **Expansion logic** (75% success) - Edge cases in pattern expansion

---

## 1. Infrastructure Gaps

### 1.1 Container Requirements

| Container | Status | Failure Mode |
|-----------|--------|--------------|
| `residency-scheduler-db` | **CRITICAL** | "Connection refused" - generation impossible |
| `residency-scheduler-backend` | **CRITICAL** | API unavailable |
| `residency-scheduler-mcp` | Recommended | No MCP tools, must use API directly |
| `residency-scheduler-redis` | Optional | Cache miss, slower but functional |
| `residency-scheduler-frontend` | Optional | Not needed for API-based generation |

**Gap:** `/startupO-lite` checks container status but does NOT auto-start stopped containers.

**Mitigation:**
```bash
# If containers not running:
docker compose up -d
# Wait for health checks:
docker compose ps
```

### 1.2 Database Connection Pool

```
DATABASE_URL format: postgresql+asyncpg://user:pass@host:5432/residency_scheduler
Pool size: 10 connections
Max overflow: 20 connections
Timeout: 30 seconds
Pre-ping: Enabled
```

**Gap:** Pool exhaustion if previous session left connections open.

**Detection:**
```bash
docker exec residency-scheduler-db psql -U scheduler -d residency_scheduler \
  -c "SELECT COUNT(*) FROM pg_stat_activity WHERE state = 'active';"
```

---

## 2. Data Completeness Gaps

### 2.1 Required Tables

| Table | Required Rows | Block 10 Specific | If Missing |
|-------|---------------|-------------------|------------|
| `activities` | 83+ | All codes needed | Silent NULL assignments |
| `people` | 33 | 17 residents + 14 faculty (non-adjunct) + 2 adjunct | FK violations |
| `block_assignments` | 17 | One per resident | No expansion possible |
| `rotation_templates` | 87 | Referenced by assignments | NULL template_id |
| `weekly_patterns` | 433 | ~15 templates have patterns | Default fallback |
| `absences` | 14 | Overlapping Block 10 dates | Absence conflicts |

### 2.2 Critical Activity Codes (No Fallback)

**MUST EXIST in `activities` table (no fallback path):**

| Code | Purpose | Impact if Missing |
|------|---------|-------------------|
| `LEC-PM` | Wednesday PM lecture | Protected time missing |
| `LEC` | Last Wednesday AM lecture | Last Wednesday AM missing |
| `ADV` | Last Wednesday PM advising | Last Wednesday PM missing |
| `C` | Clinic | Intern continuity + clinic patterns fail |
| `C-I` | Inpatient clinic | FMIT clinic assignments missing |
| `CALL` | On-call | Call schedule broken |
| `PCAT` | Post-call attending time | Supervision gaps |
| `DO` | Direct observation | Post-call pattern incomplete |
| `FMIT` | FM Inpatient Team | Inpatient expansion fails |
| `NF` | Night Float | NF pattern expansion fails |
| `IM` | Internal Medicine | IM expansion fails |
| `PedW` | Peds Ward | PedW expansion fails |
| `aSM` | Academic Sports Med | SM Wednesday AM missing |

**Required base absence codes (fallback for -AM/-PM templates):**
`W`, `LV`, `OFF`, `HOL` (and `DEP`, `TDY` if used in absences).

**Gap:** No pre-flight check verifies required activities or placeholder templates exist.

**Audit Query (activities):**
```sql
-- Find missing required activity codes (code OR display_abbreviation)
SELECT required.code
FROM (
  VALUES
    ('LEC-PM'), ('LEC'), ('ADV'), ('C'), ('C-I'),
    ('CALL'), ('PCAT'), ('DO'),
    ('FMIT'), ('NF'), ('IM'), ('PedW'), ('aSM'),
    ('W'), ('LV'), ('OFF'), ('HOL')
) AS required(code)
WHERE NOT EXISTS (
  SELECT 1 FROM activities a
  WHERE a.code = required.code OR a.display_abbreviation = required.code
);
```

### 2.3 Required Placeholder Rotation Templates

These templates must exist in `rotation_templates` for 56-slot expansion:

`W-AM`, `W-PM`, `LV-AM`, `LV-PM`, `OFF-AM`, `OFF-PM`, `HOL-AM`, `HOL-PM`,
`LEC-PM`, `LEC`, `ADV`, `C`

**Audit Query (templates):**
```sql
SELECT required.abbrev
FROM (
  VALUES
    ('W-AM'), ('W-PM'), ('LV-AM'), ('LV-PM'),
    ('OFF-AM'), ('OFF-PM'), ('HOL-AM'), ('HOL-PM'),
    ('LEC-PM'), ('LEC'), ('ADV'), ('C')
) AS required(abbrev)
WHERE NOT EXISTS (
  SELECT 1 FROM rotation_templates rt
  WHERE rt.abbreviation = required.abbrev
);
```

### 2.4 Foreign Key Integrity

**CASCADE chains (data loss risk):**

```
Person DELETED
  └─→ block_assignments DELETED (CASCADE)
       └─→ half_day_assignments DELETED (via person_id CASCADE)

RotationTemplate DELETED
  └─→ block_assignments.rotation_template_id SET NULL
  └─→ weekly_patterns DELETED (CASCADE)
  └─→ rotation_activity_requirements DELETED (CASCADE)

Activity DELETED
  └─→ BLOCKED by RESTRICT (safe - cannot delete in-use activities)
```

**Integrity Check:**
```sql
-- Find orphaned block_assignments (NULL template)
SELECT COUNT(*) FROM block_assignments
WHERE rotation_template_id IS NULL;

-- Find weekly_patterns with NULL activity
SELECT COUNT(*) FROM weekly_patterns
WHERE activity_id IS NULL;
```

---

## 3. Code Gaps (Stubbed/Incomplete)

### 3.1 Stubbed Functions

**File:** `backend/app/services/sync_preload_service.py`

| Function | Line | Status | Impact |
|----------|------|--------|--------|
| `_load_conferences()` | ~99 | STUBBED | HAFP/USAFP not blocked |
| `_load_protected_time()` | ~101 | STUBBED | SIM/PI/MM not blocked |

**Risk:** These slots may be double-booked with clinic assignments.

**Code Evidence:**
```python
# Lines 99-101 in sync_preload_service.py
# self._load_conferences()    # STUBBED
# self._load_protected_time() # STUBBED
```

### 3.2 Weekly Patterns Coverage

**Statistics:**
- 87 rotation templates exist
- ~15 have explicit `weekly_patterns` defined
- 72 templates rely on default fallback logic

**Gap:** Default fallback may not match intended schedule patterns.

**Audit Query:**
```sql
-- Templates with patterns
SELECT rt.abbreviation, COUNT(wp.id) as pattern_count
FROM rotation_templates rt
LEFT JOIN weekly_patterns wp ON rt.id = wp.rotation_template_id
GROUP BY rt.id, rt.abbreviation
ORDER BY pattern_count ASC;
```

### 3.3 Activity Solver Integrated (Best-Effort)

**File:** `backend/app/scheduling/engine.py`

- `CPSATActivitySolver` runs after call solver when `expand_block_assignments=true`
- Timeout is capped at 30s; failure logs a warning but does **not** fail generation
- Gap: If the activity solver fails, you can end with template/placeholder coverage
  and miss clinic/LEC/ADV placement without a hard stop

**Mitigation:** Treat activity solver failure as a hard error in preflight/runbook.

### 3.4 Export Pipeline Pattern Duplication

**Current State:**
```
block_assignment_expansion_service.py
  └─→ ROTATION_PATTERNS dict (defines LDNF=Fri clinic, KAP=Mon/Tue off, etc.)
  └─→ Writes to half_day_assignments

schedule_xml_exporter.py
  └─→ SAME ROTATION_PATTERNS dict (DUPLICATED)
  └─→ Reads from block_assignments, re-computes patterns
```

**Risk:** Export could diverge from what was actually generated.

**Needed Fix:** Create `half_day_xml_exporter.py` that reads from `half_day_assignments` only.

---

## 4. Pre-Flight Verification Checklist

Run these checks BEFORE attempting generation:

### 4.0 One-Command Gate
```bash
./scripts/preflight-block10.sh
```

### 4.1 Container Health
```bash
docker ps --format "table {{.Names}}\t{{.Status}}" | grep scheduler
# All should show "healthy"
```

### 4.2 Database Connectivity
```bash
curl -s http://localhost:8000/health | jq .
# Should return: {"status":"healthy","database":"connected"}
```

### 4.3 People Roster Sanity
```bash
docker exec residency-scheduler-db psql -U scheduler -d residency_scheduler \
  -c "SELECT type, COUNT(*) FROM people GROUP BY type;"
# Expected (Block 10): 17 residents, 14 faculty (non-adjunct), 2 adjunct
```

### 4.4 Activity Code Audit
```bash
docker exec residency-scheduler-db psql -U scheduler -d residency_scheduler \
  -c "SELECT COUNT(*) FROM activities;"
# Should return: 83+ (Block 10 baseline)
```

### 4.5 Placeholder Template Audit
```bash
docker exec residency-scheduler-db psql -U scheduler -d residency_scheduler \
  -c "SELECT rt.abbreviation FROM rotation_templates rt WHERE rt.abbreviation IN ('W-AM','W-PM','LV-AM','LV-PM','OFF-AM','OFF-PM','HOL-AM','HOL-PM','LEC-PM','LEC','ADV','C') ORDER BY rt.abbreviation;"
# Should return all 12 abbreviations
```

### 4.6 Block 10 Assignments
```bash
docker exec residency-scheduler-db psql -U scheduler -d residency_scheduler \
  -c "SELECT COUNT(*) FROM block_assignments WHERE block_number=10 AND academic_year=2025;"
# Should return: 17
```

### 4.7 NULL Activity Check
```bash
docker exec residency-scheduler-db psql -U scheduler -d residency_scheduler \
  -c "SELECT COUNT(*) FROM weekly_patterns WHERE activity_id IS NULL;"
# Should return: 0
```

### 4.8 Create Backup
```bash
# Via MCP tool (if available):
mcp__residency-scheduler__create_backup_tool(reason="Pre-Block10-generation")

# Or via script:
./scripts/backup-db.sh --docker
```

---

## 5. Post-Generation Validation

### 5.1 Assignment Count
```bash
docker exec residency-scheduler-db psql -U scheduler -d residency_scheduler \
  -c "SELECT COUNT(*) FROM half_day_assignments WHERE date >= '2026-03-12' AND date <= '2026-04-08';"
# Expected: (resident_count + faculty_non_adjunct_count) × 56
# (Adjunct faculty are excluded by default in generation)
#
# Get counts:
# docker exec residency-scheduler-db psql -U scheduler -d residency_scheduler \
#   -c \"SELECT
#         SUM(CASE WHEN type='resident' THEN 1 ELSE 0 END) AS residents,
#         SUM(CASE WHEN type='faculty' AND (faculty_role != 'adjunct' OR faculty_role IS NULL) THEN 1 ELSE 0 END) AS faculty_non_adjunct
#       FROM people;\"
```

### 5.2 NULL Activity Check
```bash
docker exec residency-scheduler-db psql -U scheduler -d residency_scheduler \
  -c "SELECT COUNT(*) FROM half_day_assignments WHERE activity_id IS NULL AND date >= '2026-03-12';"
# Should return: 0
```

### 5.3 Source Distribution
```bash
docker exec residency-scheduler-db psql -U scheduler -d residency_scheduler \
  -c "SELECT source, COUNT(*) FROM half_day_assignments WHERE date >= '2026-03-12' GROUP BY source ORDER BY COUNT(*) DESC;"
# Expected: Use as a sanity check only (counts vary by preload volume and solver outcome)
```

### 5.4 ACGME Validation
```bash
# Via MCP tool:
mcp__residency-scheduler__validate_schedule_tool(
  start_date="2026-03-12",
  end_date="2026-04-08"
)
```

---

## 6. Recommended Mitigations

### Before Generation
1. Run all pre-flight checks above
2. Create database backup
3. Verify authentication token is valid

### During Generation
1. Use `timeout_seconds=120` (not default 60)
2. Set `expand_block_assignments=true`
3. Monitor logs for "Activity not found" warnings

### After Generation
1. Run all post-generation validation checks
2. Export to XML before xlsx (checkpoint validation)
3. If NULL activities found, investigate and re-run

---

## Related Documents

- [BLOCK10_EDGE_CASES.md](BLOCK10_EDGE_CASES.md) - Edge case scenarios
- [BLOCK10_999_SUCCESS_PLAN.md](BLOCK10_999_SUCCESS_PLAN.md) - 99.9% success plan
- [session-133-schedule-generation-status.md](../scratchpad/session-133-schedule-generation-status.md) - Session notes
- [HALF_DAY_ASSIGNMENT_MODEL.md](../architecture/HALF_DAY_ASSIGNMENT_MODEL.md) - Data model
