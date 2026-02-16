# GUI Health Audit Report

> **Date:** 2026-01-19
> **Auditor:** Claude Code (Chrome browser automation)
> **Scope:** Full stack health check + GUI page audit

---

## Executive Summary

**Stack Status:** GREEN (all 7 containers healthy, 21+ hours uptime)

**Critical Finding:** Frontend displays "no data" because current date range (Jan 19 - Feb 18, 2026) has **0 assignments**. Block 10 data (Mar 12 - Apr 8, 2026) has **1008 assignments** ready.

**Issues Found:** 3 bugs, 2 data issues

---

## Database Status

| Table | Count | Status |
|-------|-------|--------|
| people | 33 | ✅ |
| assignments | 5,240 | ✅ |
| blocks | 1,516 | ✅ |
| rotation_templates | 87 | ✅ |
| absences | 129 | ⚠️ 2 invalid types |
| call_assignments | 366 | ✅ |

### Assignment Distribution

| Date Range | Assignments |
|------------|-------------|
| Today (Jan 19 - Feb 18, 2026) | **0** |
| Block 10 (Mar 12 - Apr 8, 2026) | **1008** |
| All 2026 | 4,192 |

**Root Cause:** Schedule was generated for future blocks (Block 10+), but current date range has no assignments yet.

---

## Page-by-Page Audit

### Working Pages ✅

| Page | URL | Status | Notes |
|------|-----|--------|-------|
| Dashboard | `/` | ✅ Works | Shows "All Clear" compliance, some sections loading |
| Compliance Hub | `/compliance` | ✅ Works | 80-hr, 1-in-7, Supervision all Passing |
| Admin Scheduling Lab | `/admin/scheduling` | ✅ Works | Full controls, 22+ constraints visible |
| Admin Rotations | `/admin/rotations` | ✅ Works | 87 templates, full editing UI |
| Admin Labs | `/admin/labs` | ✅ Works | 5 visualization categories |
| Admin Block Explorer | `/admin/block-explorer` | ✅ Works | Loaded successfully |

### Degraded Pages ⚠️

| Page | URL | Status | Issue |
|------|-----|--------|-------|
| Schedule | `/schedule` | ⚠️ Degraded | "Failed to load schedule data" - no data in current range |
| People Hub | `/people` | ⚠️ Degraded | Shows "0 people" + Loading - API may be slow |
| Heatmap | `/heatmap` | ⚠️ Degraded | Stuck on "Checking authentication..." |
| Resilience Overseer | `/admin/resilience-overseer` | ⚠️ Degraded | Stuck on "Initializing Resilience Systems" |

### Broken Pages ❌

| Page | URL | Status | Error |
|------|-----|--------|-------|
| Resilience Hub | `/admin/resilience-hub` | ❌ Error | `TypeError: Cannot read properties of undefined (reading 'bgColor')` in DefenseLevel component |

---

## Bugs Identified

### BUG-001: Resilience Hub DefenseLevel Crash (HIGH)

**Location:** `/admin/resilience-hub`
**Error:** `TypeError: Cannot read properties of undefined (reading 'bgColor')`
**Component:** `DefenseLevel`
**Cause:** Missing null check when API returns undefined defense level data
**Fix:** Add optional chaining or null check in DefenseLevel component

### BUG-002: Invalid Absence Types (MEDIUM)

**Location:** Backend API `/api/v1/absences`
**Error:** `absence_type must be one of ('vacation', 'deployment', ...)`
**Data Issue:** Database contains `training` (6 records) and `military_duty` (1 record)
**Allowed Types:** `vacation`, `deployment`, `tdy`, `medical`, `family_emergency`, `conference`, `bereavement`, `emergency_leave`, `sick`, `convalescent`, `maternity_paternity`
**Fix Options:**
1. Add `training` and `military_duty` to the Pydantic enum
2. Migrate existing data to valid types (e.g., `training` → `conference`, `military_duty` → `tdy`)

### BUG-003: Resilience Overseer Timeout (MEDIUM)

**Location:** `/admin/resilience-overseer`
**Symptom:** Stuck on "Initializing Resilience Systems - Connecting to backend services..."
**Cause:** Likely slow backend response or WebSocket connection issue
**Fix:** Add timeout handling and fallback UI state

---

## Data Issues

### DATA-001: No Assignments in Current View

**Issue:** Current date range (Jan 19 - Feb 18, 2026) has 0 assignments
**Impact:** Schedule page, Dashboard widgets show empty/error state
**Resolution:**
- Navigate to Block 10 date range (Mar 12 - Apr 8, 2026) to see data
- Or generate assignments for current date range

### DATA-002: Absence Type Enum Mismatch

**Issue:** 7 records with types not in schema enum
**Records:**
- `training`: 6 records
- `military_duty`: 1 record
**Impact:** Absences API returns validation error, absences list may fail to load

---

## Performance Observations

**Docker Stats (at time of audit):**

| Container | CPU | Memory | Notes |
|-----------|-----|--------|-------|
| frontend | 3.9% | 1.6GB | High Block I/O (1.98GB writes) - hot reload |
| backend | 0.4% | 1.7GB | Healthy |
| mcp | 5.3% | 153MB | Active |
| db | 0% | 58MB | Very light |
| redis | 1% | 9.5MB | Well under limit |

**Slowness Source:** Docker Desktop bind mounts on macOS (filesystem virtualization overhead), NOT resource exhaustion.

---

## Recommended Actions

### Immediate (Block 10 Focus)

1. **Navigate to Block 10 dates** in Scheduling Lab to see existing data
2. **Fix BUG-002** - Add `training` and `military_duty` to absence_type enum OR migrate data

### Short-term

3. **Fix BUG-001** - Add null checks to DefenseLevel component
4. **Fix BUG-003** - Add timeout/fallback to Resilience Overseer

### Optional

5. Generate assignments for current date range if needed for testing
6. Consider switching to Docker named volumes if slowness is blocking

---

## Verification Commands

```bash
# Check database counts
docker exec scheduler-local-db psql -U scheduler -d residency_scheduler -c "
SELECT 'people', COUNT(*) FROM people
UNION ALL SELECT 'assignments', COUNT(*) FROM assignments
UNION ALL SELECT 'blocks', COUNT(*) FROM blocks;"

# Check Block 10 assignments
docker exec scheduler-local-db psql -U scheduler -d residency_scheduler -c "
SELECT COUNT(*) FROM assignments a
JOIN blocks b ON a.block_id = b.id
WHERE b.date BETWEEN '2026-03-12' AND '2026-04-08';"

# Check invalid absence types
docker exec scheduler-local-db psql -U scheduler -d residency_scheduler -c "
SELECT DISTINCT absence_type, COUNT(*) FROM absences GROUP BY absence_type;"
```

---

## Files to Fix

| Bug | File | Line (approx) |
|-----|------|---------------|
| BUG-001 | `frontend/src/features/resilience/DefenseLevel.tsx` | bgColor access |
| BUG-002 | `backend/app/schemas/absence.py` | AbsenceType enum |
| BUG-003 | `frontend/src/app/admin/resilience-overseer/page.tsx` | Initialization timeout |

---

*Generated by GUI Health Audit - Claude Code Chrome automation*
