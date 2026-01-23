# Scheduling Skills & Tools Reference

**Last Updated:** 2026-01-22
**Purpose:** Human-readable guide to all scheduling-related skills and tools

---

## Quick Reference: When to Use What

| Task | Primary Skill | Supporting Skills |
|------|---------------|-------------------|
| Generate new schedule | `/SCHEDULING` | `schedule-optimization`, `safe-schedule-generation` |
| Fill Excel template | `/tamc-excel-scheduling` | `tamc-cpsat-constraints`, `xlsx` |
| Validate ACGME compliance | `/acgme-compliance` | `schedule-validator` |
| Process swap request | `/swap-management` | `swap-analyzer`, `SWAP_EXECUTION` |
| Add new constraint | `/constraint-preflight` | `tamc-cpsat-constraints` |
| Debug solver issues | `schedule-optimization` | `systematic-debugger` |
| Export to Excel | `/xlsx` | `rosetta-stone` |

---

## Core Scheduling Skills

### 1. `/SCHEDULING` - Master Orchestrator

**When:** Generating full schedules (blocks, academic year)

**Five Phases:**
1. **Requirements Gathering** - Collect constraints, preferences, absences
2. **Constraint Propagation** - Apply ACGME rules, reduce search space
3. **Optimization** - Run CP-SAT solver
4. **Conflict Resolution** - Handle trade-offs
5. **Validation & Deployment** - Verify and deploy

**Key Concepts:**
- **Tier 1 (Absolute):** ACGME rules - non-negotiable
- **Tier 2 (Institutional):** Program policies - needs approval to override
- **Tier 3 (Optimization):** Preferences - best-effort

---

### 2. `/tamc-excel-scheduling` - Excel Template Expert

**When:** Working with Block Template2 sheets, filling schedules manually

**Key Data:**
- **Rows 9-25:** Residents (PGY-3: 9-13, PGY-2: 14-19, PGY-1: 20-25)
- **Rows 31-43:** Faculty (C19: 31-40, ADJ: 41-42, SPEC: 43)
- **Row 4:** Staff Call
- **Columns 6-61:** Schedule (AM/PM pairs)

**Critical Rules:**
| Rule | Description |
|------|-------------|
| Last Wednesday | AM=LEC, PM=ADV (no clinic) |
| Mid-block transition | Column 28 (start of week 3) |
| PGY-1 Wed AM | Continuity clinic (except TDY/NF) |
| LDNF clinic | Friday AM (not Wednesday!) |
| Weekend columns | 10-13, 24-27, 38-41, 52-55 → W |

---

### 3. `/tamc-cpsat-constraints` - Solver Constraint Reference

**When:** Building/debugging OR-Tools CP-SAT solver, understanding constraint logic

**Build Order:**
1. **Preload** - Lock FMIT, leave, conferences, holidays
2. **Call assignment** - Distribute with equity tracking
3. **Resident schedules** - Apply rotation patterns
4. **Faculty C/AT** - Fill remaining slots
5. **Admin time** - GME/DFM for remaining

**Hard Constraints (Cannot Violate):**
| Constraint | Description |
|------------|-------------|
| ACGME Supervision | AT demand must be met every half-day |
| Weekly Clinic Caps | Faculty MIN/MAX C per week |
| FMIT Blocking | No clinic during FMIT, Fri+Sat call only |
| Post-Call PCAT/DO | Next day blocked after non-FMIT call |
| No Back-to-Back Call | Need gap days between call assignments |
| Physical Capacity | Max 6 doing clinical work per half-day |

**AT Demand Calculation:**
```
PGY-1: 0.5 AT each
PGY-2: 0.25 AT each
PGY-3: 0.25 AT each
PROC/VAS: +1.0 AT (dedicated)
→ Round UP (can't have half a faculty)
```

---

### 4. `/schedule-optimization` - Solver Expert

**When:** Generating schedules, optimizing coverage, balancing workloads

**Solver Types:**
- **CP-SAT (OR-Tools):** Primary constraint solver
- **Greedy:** Quick initial solution
- **Hybrid:** Greedy → CP-SAT refinement

**Key Architecture:**
| Mode | Rotations | Solver Role |
|------|-----------|-------------|
| Block-Assigned | FMIT, NF, Inpatient | Pre-assigned, NOT optimized |
| Half-Day Optimized | Clinic, Specialty | Solver optimizes these |

**Objectives (Soft):**
- Fairness (Gini < 0.15)
- Preferences (>80% satisfied)
- Continuity (minimize handoffs)
- Resilience (N-1 backup)

---

### 5. `/acgme-compliance` - Regulatory Expert

**When:** Validating schedules, checking work hours, supervision ratios

**Core Rules:**

| Rule | Requirement | Threshold |
|------|-------------|-----------|
| 80-Hour | Max hours/week (4-week avg) | Warning: 75h, Violation: 80h |
| 1-in-7 | Day off every 7 days | 6 consecutive = warning |
| Supervision | PGY-1: 2:1, PGY-2/3: 4:1 | Hard constraint |
| Duty Period | Max shift length | 24h (28h with napping) |
| Post-Call | Rest after 24h call | Min 8 hours |
| Night Float | Max consecutive nights | 6 nights |

---

### 6. `/swap-management` - Swap Workflow Expert

**When:** Processing swap requests, finding compatible partners

**Swap Types:**
1. **One-to-One:** Direct exchange between two people
2. **Absorb:** One takes another's shift (no return)
3. **Three-Way:** Circular exchange among three

**Workflow:**
```
Request → Auto-Match → Partner Consent → Validate → Execute → Verify
```

**Emergency Protocol:**
1. Check backup pool first
2. Broadcast if no backups
3. Emergency absorb (skip consent)
4. Balance workload later

---

### 7. `/safe-schedule-generation` - Safety Gatekeeper

**When:** Any operation that modifies assignments table

**MANDATORY Pre-Flight:**
1. ✅ Check backend health
2. ✅ Verify data exists (people, templates)
3. ✅ Backup exists and recent (<2 hours)
4. ✅ User confirmation obtained

**Backup Rules:**
- Minimum 2 backups always
- First backup is "sacred" (never delete)
- 30-day retention
- Pre-operation backup REQUIRED

---

### 8. `/constraint-preflight` - Constraint Quality Gate

**When:** Adding or modifying scheduling constraints

**Checklist:**
1. ✅ Implement constraint class
2. ✅ Export in `__init__.py`
3. ✅ Register in `ConstraintManager.create_default()`
4. ✅ Register in `ConstraintManager.create_resilience_aware()`
5. ✅ Write registration test
6. ✅ Run `verify_constraints.py`

**Weight Hierarchy (Call Equity):**
```
SundayCallEquity: 10.0 (highest)
CallSpacing: 8.0
WeekdayCallEquity: 5.0
FridayCallAvoidance: 3.0
TuesdayCallPreference: 2.0 (lowest)
```

---

## Supporting Skills

### `/schedule-validator`
Validate schedules for ACGME compliance, coverage gaps, operational viability.

### `/schedule-verification`
Human review checklist for generated schedules.

### `/swap-analyzer`
Analyze swap compatibility and safety.

### `/SWAP_EXECUTION`
Execute swaps with safety checks, audit trails, rollback.

### `/xlsx`
Excel import/export for schedules.

### `/rosetta-stone`
Data format translation (xlsx ↔ xml ↔ db).

### `/solver-control`
Solver kill-switch and progress monitoring.

---

## Two Truths Architecture

**CRITICAL: Understand which data is authoritative.**

| Type | Tables | Role |
|------|--------|------|
| **Prescriptive** | `rotation_templates`, `weekly_patterns` | What SHOULD happen |
| **Descriptive** | `half_day_assignments` | What DID happen |

**Generation Flow:**
```
Prescriptive (templates) → Expansion Service → Descriptive (assignments)
```

**Export Flow:**
```
Descriptive (assignments) → XML → XLSX
```

**Source Priority:**
1. `preload` - FMIT, call, absences (NEVER overwritten)
2. `manual` - Explicit human override
3. `solver` - Computed by CP-SAT
4. `template` - Default from WeeklyPattern

---

## Faculty Clinic Caps

| Role | MIN C/wk | MAX C/wk | Admin |
|------|----------|----------|-------|
| C19 Faculty (standard) | 2 | 4 | GME |
| C19 Faculty (reduced) | 2 | 2 | GME |
| DFM Faculty | 1 | 1 | DFM |
| SM Faculty | 0 | 0 | SM (no C) |
| Administrative (APD, deployed) | 0 | 0 | GME |
| Adjunct Faculty | 0 | 0 | ADJ (FMIT/call only) |

**Note:** Caps apply to **C only**, NOT AT. AT is unlimited.
**Note:** Individual faculty caps are configured in the database `people` table.

---

## Rotation Patterns (Quick Reference)

| Rotation | AM | PM | Clinic Load |
|----------|----|----|-------------|
| FMC | C | C | 1.0 |
| FMIT | FMIT | FMIT | 0.2 (C-I only) |
| NF | OFF | NF | 0 |
| NEURO/ENDO | Rotation | C | 0.4 |
| SM | SM | C | 0.4 |
| POCUS | US | C | 0.4 |
| LDNF | OFF | LDNF | 0.2 (Fri AM) |
| SURG/GYN | Rotation | C | 0.4 |
| PROC | PR | C | 0.4 |
| IM | IM | IM | 0.2 (Wed AM) |
| PedsW | PedW | PedW | 0.2 (Wed AM) |
| PedsNF | OFF | PedNF | 0.2 (Wed AM) |
| KAP | Special | Special | 0.2 (Wed AM) |
| Hilo | TDY | TDY | 0 |

**Special Rules:**
- LDNF: Friday AM clinic (not Wednesday)
- KAP: Mon PM OFF, Tue OFF/OFF, Wed AM clinic
- Last Wed: All residents = LEC/ADV

---

## Common Commands

```bash
# Validate constraints
cd backend && python ../scripts/verify_constraints.py

# Run ACGME check
python -m app.scheduling.acgme_validator --schedule_id=current --full-report

# Export schedule to Excel
python -c "from app.services.xml_to_xlsx_converter import XMLToXlsxConverter; ..."

# Create backup
./scripts/backup-db.sh --docker

# Generate schedule (API)
curl -X POST http://localhost:8000/api/v1/schedule/generate \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"start_date": "2026-03-12", "end_date": "2026-04-08"}'
```

---

## Escalation Triggers

**Escalate to Program Director when:**
- Multiple ACGME violations
- Systemic patterns (recurring issues)
- Policy exceptions needed
- Resource insufficiency
- Resident health/safety concerns

**Escalate to Technical Team when:**
- Solver crashes/hangs
- Database issues
- Performance degradation (>10 min solve)
- New constraint type needed

---

## See Also

- `docs/architecture/HALF_DAY_ASSIGNMENT_MODEL.md` - Data model
- `docs/development/CODEX_SYSTEM_OVERVIEW.md` - System architecture
- `.claude/skills/*/SKILL.md` - Individual skill files
- `backend/app/scheduling/` - Solver implementation
