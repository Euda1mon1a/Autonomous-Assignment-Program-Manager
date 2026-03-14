# Constraint Catalog Summary

> **doc_type:** scheduling_policy
> **Source:** `constraint_configurations` table (DB is source of truth since PR #1297)
> **Last Updated:** 2026-03-13
> **Purpose:** Quick reference for all scheduling constraints

---

## Overview

- **53 Constraints** registered in `ConstraintManager.create_default()`
- **~21 Hard Constraints** — must be satisfied; violations make schedule infeasible
- **~32 Soft Constraints** — optimization objectives; violations add weighted penalty
- **44 Enabled / 9 Disabled** (as of 2026-03-13)
- **Configuration:** `constraint_configurations` table in PostgreSQL. Editable via API, read by engine at schedule generation.

### Architecture (PR #1297)

```
ConstraintManager.create_default()  → instantiate 53 constraint classes
         ↓
seed_constraints.py                 → populate DB rows (run once)
         ↓
constraint_configurations table     ← API routes read/write (frontend)
         ↓
engine._sync_constraints_from_db()  → overlay DB enabled/weight at init
         ↓
Solver uses synced constraints
```

**Important:** The DB table is the single source of truth for enabled/weight. The old `ConstraintConfigManager` / `get_constraint_config()` system is deprecated and should NOT be used for solver-visible state.

---

## Constraints by Category

### ACGME (4) — NEVER DISABLE

| Name | Type | Priority | Weight | What It Prevents |
|------|------|----------|--------|-----------------|
| **80HourRule** | Soft | CRITICAL | 1000 | >80 hours/week over 4-week rolling average |
| **1in7Rule** | Soft | CRITICAL | 1000 | Working 7 consecutive days without 24h break |
| **Availability** | Hard | CRITICAL | - | Assignments during leave, TDY, absence |
| **SupervisionRatio** | Soft | CRITICAL | 1000 | Inadequate faculty-to-resident supervision |

### CALL (14)

| Name | Type | Priority | Weight | Enabled |
|------|------|----------|--------|---------|
| **CallAvailability** | Hard | CRITICAL | - | Yes |
| **OvernightCallCoverage** | Hard | CRITICAL | - | Yes |
| **NightFloatPostCall** | Hard | CRITICAL | - | Yes |
| **FMITMandatoryCall** | Hard | CRITICAL | - | No |
| **FMITWeekBlocking** | Hard | CRITICAL | - | No |
| **AdjunctCallExclusion** | Hard | HIGH | - | Yes |
| **OvernightCallGeneration** | Hard | HIGH | - | No |
| **PostCallAutoAssignment** | Hard | HIGH | - | Yes |
| **PostFMITRecovery** | Hard | HIGH | - | Yes |
| **FMITCallProximity** | Soft | HIGH | 10000 | Yes |
| **NoConsecutiveCall** | Soft | HIGH | 50 | Yes |
| **PostFMITSundayBlocking** | Soft | HIGH | 80 | Yes |
| **CallSpacing** | Soft | MEDIUM | 8 | Yes |
| **CallNightBeforeLeave** | Soft | LOW | 2 | Yes |

### CAPACITY (3)

| Name | Type | Priority | Weight | Enabled |
|------|------|----------|--------|---------|
| **ResidentInpatientHeadcount** | Hard | CRITICAL | - | Yes |
| **ClinicCapacity** | Hard | HIGH | - | Yes |
| **MaxPhysiciansInClinic** | Hard | HIGH | - | Yes |

### COVERAGE (1)

| Name | Type | Priority | Weight | Enabled |
|------|------|----------|--------|---------|
| **Coverage** | Soft | HIGH | 1000 | Yes |

### EQUITY (8)

| Name | Type | Priority | Weight | Enabled |
|------|------|----------|--------|---------|
| **EscalatingCallEquity** | Soft | HIGH | 40 | Yes |
| **WeekendWork** | Hard | HIGH | - | Yes |
| **Equity** | Soft | MEDIUM | 10 | Yes |
| **FacultyClinicEquity** | Soft | MEDIUM | 15 | Yes |
| **SundayCallEquity** | Soft | MEDIUM | 50 | Yes |
| **WeekdayCallEquity** | Soft | MEDIUM | 25 | Yes |
| **HolidayCallEquity** | Soft | MEDIUM | 7 | Yes |
| **Continuity** | Soft | LOW | 5 | Yes |

### FACULTY (8)

| Name | Type | Priority | Weight | Enabled |
|------|------|----------|--------|---------|
| **FacultyDayAvailability** | Hard | CRITICAL | - | Yes |
| **FacultySupervision** | Soft | CRITICAL | 100 | Yes |
| **FacultyPrimaryDutyClinic** | Hard | HIGH | - | Yes |
| **FacultyRoleClinic** | Hard | HIGH | - | Yes |
| **FacultyClinicCap** | Soft | HIGH | 50 | Yes |
| **SMFacultyNoRegularClinic** | Hard | HIGH | - | No |
| **SMResidentFacultyAlignment** | Hard | HIGH | - | No |
| **FacultyCallPreference** | Soft | LOW | 1 | Yes |

### RESILIENCE (5)

| Name | Type | Priority | Weight | Enabled |
|------|------|----------|--------|---------|
| **UtilizationBuffer** | Soft | HIGH | 20 | Yes |
| **N1Vulnerability** | Soft | HIGH | 25 | No |
| **HubProtection** | Soft | MEDIUM | 15 | Yes |
| **ZoneBoundary** | Soft | MEDIUM | 12 | No |
| **PreferenceTrail** | Soft | LOW | 8 | No |

### SCHEDULING (10)

| Name | Type | Priority | Weight | Enabled |
|------|------|----------|--------|---------|
| **ProtectedSlot** | Hard | CRITICAL | - | Yes |
| **InvertedWednesday** | Soft | HIGH | 50 | Yes |
| **ResidentWeeklyClinic** | Soft | HIGH | 50 | No |
| **WednesdayAMInternOnly** | Hard | HIGH | - | Yes |
| **WednesdayPMSingleFaculty** | Soft | HIGH | 50 | Yes |
| **ActivityRequirement** | Soft | MEDIUM | 50 | Yes |
| **HalfDayRequirement** | Soft | MEDIUM | 50 | Yes |
| **GraduationRequirements** | Soft | LOW | 5 | Yes |
| **TuesdayCallPreference** | Soft | LOW | 2 | Yes |
| **DeptChiefWednesdayPreference** | Soft | LOW | 1 | Yes |

---

## Managing Constraints

### API (DB-backed, persisted)

```
GET    /api/v1/constraints              — list all 53
GET    /api/v1/constraints/enabled      — list enabled
GET    /api/v1/constraints/disabled     — list disabled
GET    /api/v1/constraints/{name}       — get one
PATCH  /api/v1/constraints/{name}       — update enabled/weight
POST   /api/v1/constraints/{name}/enable
POST   /api/v1/constraints/{name}/disable
POST   /api/v1/constraints/preset/{preset}
```

### Presets

| Preset | Effect |
|--------|--------|
| `minimal` | Enable only ACGME + Coverage, disable rest |
| `strict` | Enable all, double soft weights |
| `resilience_tier1` | Enable HubProtection + UtilizationBuffer |
| `resilience_tier2` | Enable all 5 resilience constraints |
| `call_scheduling` | Enable all call-related constraints |

---

## Related Documents

- `docs/architecture/CONSTRAINT_CATALOG.md` — Full reference
- `docs/architecture/DISABLED_CONSTRAINTS_AUDIT.md` — Why 9 are disabled
- All constraint code in `backend/app/scheduling/constraints/`
