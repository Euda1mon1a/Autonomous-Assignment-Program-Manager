# Block 10 Roadmap: Current Status & Actionable Plan

> **Created:** 2025-12-24
> **Purpose:** Evaluate Block 10 status, prioritize work, and coordinate Claude agents
> **Branch:** `claude/plan-block-10-roadmap-IDOo9`

---

## Agent Access Model

| Agent | Environment | PII Access | Primary Role |
|-------|-------------|------------|--------------|
| **Claude Code (IDE)** | Local terminal | Full access | DB operations, schedule generation, testing with real data |
| **Claude (Web)** | Browser | Sanitized only | Documentation, architecture, algorithm design, code review |
| **Human** | All | Full access | Approval, validation, strategic decisions |

**Key Principle:** Claude Code (IDE) handles all database and PII operations. Claude (Web) receives anonymized exports for analysis.

**Capabilities Reference:** See [SESSION_CAPABILITIES.md](SESSION_CAPABILITIES.md) for full skills, tools, and MCP inventory.

**Coordination Guide:** See [PARALLEL_CLAUDE_BEST_PRACTICES.md](../development/PARALLEL_CLAUDE_BEST_PRACTICES.md) for parallel work patterns.

---

## Available Capabilities Summary

### Skills (Invoke via `Skill` tool)

| Skill | Claude Web? | Claude Code (IDE)? |
|-------|-------------|-------------------|
| `acgme-compliance` | Yes | Yes |
| `code-review` | Yes | Yes |
| `security-audit` | Yes | Yes |
| `test-writer` | Yes (mock data) | Yes (real data) |
| `automated-code-fixer` | Yes | Yes |
| `safe-schedule-generation` | No (needs DB) | Yes |
| `swap-management` | No (needs DB) | Yes |
| `xlsx` / `pdf` | No (needs PII) | Yes |

### MCP Tools Status

| Status | Count | Examples |
|--------|-------|----------|
| **Functional** | 19 | `validate_schedule`, `detect_conflicts`, `health_check` |
| **Placeholder** | 10 | `analyze_homeostasis`, `get_static_fallbacks` |
| **Missing** | 5+ | `generate_schedule`, `execute_swap` |

### Execution Tools

| Tool | Claude Web Safe? |
|------|------------------|
| `Read`, `Write`, `Edit` | Yes (code/docs only) |
| `Bash` | Limited (no DB/PII) |
| `Glob`, `Grep` | Yes |
| `WebFetch`, `WebSearch` | Yes |

---

## Executive Summary

### Current Status: PRODUCTION READY (v1.0.0)

| Metric | Status | Details |
|--------|--------|---------|
| **Block 10 Generation** | Ready | Bug fixes completed (commit `de30b44`) |
| **ACGME Compliance** | Complete | 80-hour, 1-in-7, supervision ratios |
| **TODO Tracker** | 100% Complete | 25/25 items resolved |
| **Test Coverage** | 70%+ | 1,400+ frontend tests, comprehensive backend |
| **Documentation** | Comprehensive | 32+ markdown files |

### Block 10 Context

- **Academic Block 10**: March 10 - April 6 (4 weeks, 28 days)
- **Scheduling Units**: 56 half-days (28 days × 2 AM/PM blocks)
- **Recent Fixes**: Import errors, NightFloatPostCallConstraint, GraphQL enums

---

## Checkpoint System

### Checkpoint 1: Data Preparation (CLAUDE CODE IDE) ✅ COMPLETE

**Owner:** Claude Code (IDE) - has full PII access
**Completed:** 2025-12-22 (Session 14)

| Task | Status | Notes |
|------|--------|-------|
| Export residents from Airtable | ✅ Done | 17 residents (6 PGY1, 6 PGY2, 5 PGY3) |
| Export faculty from Airtable | ✅ Done | 12 faculty members |
| Export rotation templates | ✅ Done | 38 templates loaded |
| Export absences/leave | ✅ Done | 153 absences in DB |
| Seed database with test data | ✅ Done | Via `scripts/seed_data.py` |
| Verify DB connection | ✅ Done | Docker containers healthy |

**Completion Criteria:**
- [x] Database contains all personnel for Block 10 (29 people)
- [x] Rotation templates loaded (38 templates)
- [x] Known absences entered (153 absences)

---

### Checkpoint 2: Schedule Generation Test (CLAUDE CODE IDE) ⚠️ PARTIAL

**Owner:** Claude Code (IDE) generates and runs validation
**Status:** 71% coverage (weekends missing)

| Task | Owner | Status |
|------|-------|--------|
| Run Block 10 generation | Claude Code (IDE) | ✅ 80 assignments created |
| Validate ACGME compliance | Claude Code (IDE) | ⏳ Pending |
| Check coverage metrics | Claude Code (IDE) | ⚠️ 40/56 half-days (71%) |
| Export sanitized metrics | Claude Code (IDE) | ⏳ Pending |

**Current State (verified 2025-12-24):**
- 80 total assignments (40 primary + 40 supervising)
- 40/56 half-days covered = 71.4%
- **16 missing half-days = ALL WEEKENDS:**
  - 2026-03-14/15 (Sat/Sun)
  - 2026-03-21/22 (Sat/Sun)
  - 2026-03-28/29 (Sat/Sun)
  - 2026-04-04/05 (Sat/Sun)

**Root Cause Identified (2025-12-24):**
- Currently only **outpatient rotations** are being scheduled (Mon-Fri, 10 half-days/week)
- **Inpatient rotations** are NOT being loaded into solver (12/14 half-days including weekends)
- Inpatient has set clinic days for continuity → solver needs this as input constraint
- **Call** is separate from FMIT/NF and will be tackled separately

**NF/PC Over-Assignment Bug (verified 2025-12-24):**
```
| Rotation           | Assignments | Unique People | Expected |
|--------------------|-------------|---------------|----------|
| Night Float AM     | 70          | 29 (ALL)      | 1-2/week |
| Post-Call Recovery | 6           | 5             | Only post-NF |
| (null)             | 4           | 4             | Should have template |
```
- **Problem:** CP-SAT has no constraint limiting NF headcount
- **Effect:** Everyone gets assigned Night Float (should be 1-2 residents)
- **Solution:** NF/PC must be pre-assigned based on inpatient schedule, not solved freely

**Action Required (Claude Web - Checkpoint 3):**
- Design mechanism to load inpatient rotations into scheduler FIRST
- Inpatient constraints: 12/14 half-days on duty, 1 full day off per week
- NF/PC as **pre-solver locked assignments** (not optimized)
- Set clinic days for continuity (physical space limitations)
- Feed as pre-solver input to constraint engine

**Airtable Data Sources (Reference for Claude Web):**
| Table | Purpose | Notes |
|-------|---------|-------|
| `tbl ResidencyBlockSchedule` | Resident rotation assignments by block | Hardcoded inpatient rotations per block |
| `tbl Faculty Inpatient Schedule` | Faculty FMIT week assignments | May need to be hardcoded pre-solver |
| `airtable_block_schedule.json` | Local export (197KB) | Contains block-resident mappings |
| `airtable_blocks.json` | Block definitions | 13 blocks per academic year |

**N8N Pipeline Reference (10-phase workflow):**
- Phase 2: Smart Resident Association - fetches Residency Block Schedule
- `block_half` property exists for split-rotation logic (NF swaps mid-block)
- See `docs/data/N8N_WORKFLOW_SUMMARY.md` for full pipeline

---

### Sanitized Data Export for Claude Web (No PII)

**Rotation Templates by Activity Type (38 total):**
```
| activity_type | rotations                                    | is_block_half |
|---------------|----------------------------------------------|---------------|
| inpatient     | FMIT AM/PM, NICU, Night Float AM/PM          | NF/NICU: true |
| outpatient    | Clinic, Sports Med, Colposcopy, PCAT, etc.   | false         |
| procedures    | Botox, Vasectomy, Procedure AM/PM            | false         |
| recovery      | Post-Call Recovery                           | false         |
| education     | Lecture AM/PM, GRM AM/PM                     | false         |
| off           | OFF AM/PM                                    | false         |
```

**Current Block Usage (what solver is doing):**
```
| Block | Rotations Used                        | Problem                        |
|-------|---------------------------------------|--------------------------------|
| 9     | Procedure PM only                     | Missing inpatient assignments  |
| 10    | Night Float AM, Post-Call Recovery    | NF assigned to ALL 29 people   |
| 11    | FMIT AM, FMIT PM, Night Float AM      | Better - has FMIT              |
```

**Key Schema Fields:**
- `rotation_templates.activity_type` = inpatient|outpatient|procedures|recovery|education|off
- `rotation_templates.is_block_half_rotation` = true for NF/NICU (split mid-block)
- `rotation_templates.max_residents` = NULL (no headcount constraint!)

---

### Existing Pattern: `preserve_fmit` (Use as Template)

**Location:** `backend/app/scheduling/engine.py:148-154, 842-857`

```python
# Already implemented pattern for FMIT faculty preservation:
def generate_schedule(
    ...,
    preserve_fmit: bool = True,  # <-- Parameter exists!
):
    if preserve_fmit:
        fmit_assignments = self._load_fmit_assignments()
        preserve_ids = {a.id for a in fmit_assignments}
        # These IDs are protected from deletion during regeneration

def _load_fmit_assignments(self) -> list[Assignment]:
    """
    Detection logic:
        - person.type == 'faculty'
        - template.activity_type == 'inpatient'
    """
```

**Claude Web Task:** Extend this pattern to:
1. Add `preserve_resident_inpatient: bool = True` parameter
2. Create `_load_resident_inpatient_assignments()` method
3. Load from Airtable `tbl ResidencyBlockSchedule` → DB assignments
4. Add to `preserve_ids` so solver respects them

**CRITICAL Business Rules (from user clarification):**

```
═══════════════════════════════════════════════════════════════════
RESIDENT INPATIENT ASSIGNMENTS (per block)
═══════════════════════════════════════════════════════════════════

FMIT (Full-block inpatient):
  - 1 PGY1 on FMIT per block
  - 1 PGY2 on FMIT per block
  - 1 PGY3 on FMIT per block
  = 3 residents total on FMIT per block (one per year group)

FMIT HARDCODED CLINIC DAYS (continuity requirement):
  - PGY-1 FMIT: Clinic Wednesday AM (always)
  - PGY-2 FMIT: Clinic Tuesday PM (always)
  - PGY-3 FMIT: Clinic Monday PM (always)
  - Federal holiday / clinic closed? → defaults back to FMIT duty
  - Inverted 4th Wednesday? → clinics NOT assigned to interns (PGY-1)

NIGHT FLOAT (NF):
  - Only 1 resident on Night Float at a time
  - C30 Thursday PM BEFORE starting NF shift (orientation/prep)
  - Call happens during NF person's off day
  - Back-to-back NF blocks: ALLOWED (no constraint)

POST-CALL (PC):
  - PC is Thursday AFTER coming off NF
  - Inter-block PC is CRITICAL - cannot miss PC for someone ending NF
  - Must have logic to handle block boundaries

NICU + NF (half-block split):
  - NICU component: Clinic Friday PM (always)
  - Similar rule for ANY inpatient half-block rotation
  - Outpatient half-blocks: follow their own logic

═══════════════════════════════════════════════════════════════════
FACULTY FMIT (different logic)
═══════════════════════════════════════════════════════════════════
  - Follows WEEKLY rotation (not block-based)
  - See `tbl Faculty Inpatient Schedule` for week assignments
  - May need separate loading mechanism
```

**Constraint Files to Review:**
```
backend/app/scheduling/constraints/
├── fmit.py                  # FMIT-specific constraints
├── night_float_post_call.py # NF→PC transition rules
├── capacity.py              # OnePersonPerBlockConstraint (max 1 per block)
├── base.py                  # HardConstraint/SoftConstraint base classes
└── manager.py               # Constraint registration
```

**Completion Criteria:**
- [x] Schedule generated without errors
- [ ] < 5 ACGME violations (pending validation)
- [ ] > 80% coverage achieved (currently 71% - weekends needed?)
- [ ] Sanitized export ready for web analysis

---

### Checkpoint 3: Quality Analysis (CLAUDE WEB)

**Owner:** Claude (Web) - receives sanitized data only

| Task | Status | Notes |
|------|--------|-------|
| Analyze coverage patterns | Pending | From anonymized export |
| Review constraint satisfaction | Pending | Violation types, not names |
| Evaluate fairness metrics | Pending | Distribution statistics |
| Identify optimization opportunities | Pending | Algorithm improvements |
| **Design inpatient pre-loading** | Pending | Extend `preserve_fmit` pattern |
| **Design call solver integration** | Pending | See call constraints below |

**Completion Criteria:**
- [ ] Coverage analysis document created
- [ ] Optimization recommendations provided
- [ ] No PII in analysis outputs
- [ ] Inpatient pre-loading design documented
- [ ] Call constraint implementation plan

---

### Faculty Call Scheduling Context (for Claude Web)

**Call Schedule Overview:**
- **Fri/Sat overnight**: FMIT attending (mandatory)
- **Sun-Thu overnight**: Non-FMIT faculty pool (solver distributes)

**Call Constraints:**

| Constraint | Type | Status | Notes |
|------------|------|--------|-------|
| FMIT → Fri/Sat call | Hard | Pre-load | FMIT faculty takes mandatory weekend call |
| FMIT → No Sun-Thu call | Hard | Exists | Blocked during FMIT week |
| Post-FMIT → No Sun call | Hard | **NEW** | Thu FMIT ends → Fri PC → NOT Sun call |
| Alternating weeks | Soft | **NEW** | Avoid back-to-back call weeks for same faculty |
| Sunday equity | Soft | Exists | Separate tracking (worst day) |
| Mon-Thu equity | Soft | Exists | Combined pool |
| PD/APD avoid Tuesday | Soft | Exists | Academic commitments |
| Dept Chief prefers Wed | Soft | Exists | Personal preference |

**Existing Constraint Files:**
```
backend/app/scheduling/constraints/call_equity.py
├── SundayCallEquityConstraint     # Minimize max Sunday calls
├── WeekdayCallEquityConstraint    # Minimize max Mon-Thu calls
├── TuesdayCallPreferenceConstraint # PD/APD penalty for Tuesday
└── DeptChiefWednesdayPreferenceConstraint # Dept Chief bonus for Wednesday
```

**New Constraints Needed:**
1. `PostFMITSundayBlockingConstraint` - Hard: No Sunday call immediately after FMIT week
2. `CallSpacingConstraint` - Soft: Penalize back-to-back call weeks

**Future Enhancement (not Block 10 scope):**
- Decay factor for call/FMIT recency: `Penalty = f(days_since_last_FMIT, days_since_last_call)`

---

### Block 10 Faculty FMIT Schedule (Sanitized)

| Week | Dates | FMIT Faculty | Mandatory Call |
|------|-------|--------------|----------------|
| 1 | Mar 13-19 | FAC-CORE-01 | Fri 3/13, Sat 3/14 |
| 2 | Mar 20-26 | FAC-CORE-02 | Fri 3/20, Sat 3/21 |
| 3 | Mar 27-Apr 2 | FAC-CORE-01 | Fri 3/27, Sat 3/28 |
| 4 | Apr 3-9 | FAC-CORE-03 | Fri 4/3, Sat 4/4 |

**Inter-Block Handoffs (Sanitized):**

| Transition | Faculty | Timeline |
|------------|---------|----------|
| Block 9 → 10 | FAC-CORE-04 | FMIT ends Thu 3/12 → PC Fri 3/13 → Blocked Sun 3/15 |
| Block 10 → 11 | FAC-CORE-03 | FMIT ends Thu 4/9 → PC Fri 4/10 |
| Block 11 start | FAC-CORE-05 | Starts FMIT Fri 4/10 |

**Post-FMIT Sunday Protection (derived from schedule):**

| FMIT Faculty | FMIT Ends | PC Friday | Blocked from Sunday Call |
|--------------|-----------|-----------|--------------------------|
| FAC-CORE-01 | Thu 3/19 | Fri 3/20 | Sun 3/22 ❌ |
| FAC-CORE-02 | Thu 3/26 | Fri 3/27 | Sun 3/29 ❌ |
| FAC-CORE-01 | Thu 4/2 | Fri 4/3 | Sun 4/5 ❌ |
| FAC-CORE-03 | Thu 4/9* | - | (Block 11) |

*Block 10 ends Apr 8; FAC-CORE-03's post-FMIT is Block 11's concern.

**Sun-Thu Call Eligibility (per week):**
- Week 1 (Mar 15-19): All faculty EXCEPT FAC-CORE-01
- Week 2 (Mar 22-26): All faculty EXCEPT FAC-CORE-02, and FAC-CORE-01 blocked Sun 3/22
- Week 3 (Mar 29-Apr 2): All faculty EXCEPT FAC-CORE-01, and FAC-CORE-02 blocked Sun 3/29
- Week 4 (Apr 5-8): All faculty EXCEPT FAC-CORE-03, and FAC-CORE-01 blocked Sun 4/5

---

### Checkpoint 4: UI/UX Testing (CLAUDE CODE IDE)

**Owner:** Claude Code (IDE) - can test with real or mock data

| Task | Status | Notes |
|------|--------|-------|
| Add Block 10 date picker tests | Pending | Frontend component tests |
| Test schedule view rendering | Pending | Can use real data locally |
| Validate export functionality | Pending | Excel/PDF/ICS |
| Review 3D visualization | Pending | Canvas rendering tests |

**Completion Criteria:**
- [ ] All UI components render correctly
- [ ] Export produces valid files
- [ ] No JavaScript console errors

---

### Checkpoint 5: Production Readiness (HUMAN + CLAUDE)

**Owner:** Human approves, Claude Code (IDE) assists, Claude (Web) documents

| Task | Owner | Status |
|------|-------|--------|
| Final schedule review | Human | Visual inspection |
| Swap auto-matcher test | Claude Code (IDE) | With test faculty |
| Generate production export | Claude Code (IDE) | Excel for distribution |
| Document any issues | Claude (Web) | Update CHANGELOG |

**Completion Criteria:**
- [ ] Schedule approved by human
- [ ] Export delivered
- [ ] Issues documented for next iteration

---

## Work Distribution by Agent

### Claude Code (IDE) - Full Access Tasks

These tasks involve PII or database operations:

| # | Task | Effort | Notes |
|---|------|--------|-------|
| 1 | **Seed database with Block 10 data** | 1h | From Airtable exports |
| 2 | **Run schedule generation** | 30m | `--block 10` flag |
| 3 | **Test with real faculty data** | 2h | Swap matching, conflicts |
| 4 | **Generate production exports** | 1h | Excel for distribution |
| 5 | **Run integration tests** | 2h | Full stack with DB |
| 6 | **Debug ACGME violations** | 2h | Query specific assignments |
| 7 | **Test UI with real schedule** | 1h | Visual validation |

### Claude (Web) - Sanitized Data Tasks

These tasks require only anonymized data:

| # | Task | Effort | Input Required |
|---|------|--------|----------------|
| 8 | **Analyze coverage gaps** | 2h | `block10_metrics.json` |
| 9 | **Identify constraint hotspots** | 2h | Violation summary |
| 10 | **Recommend solver tuning** | 4h | Benchmark results |
| 11 | **Generate fairness report** | 2h | Distribution stats |
| 12 | **Document algorithm design** | 3h | Code review (no PII in code) |
| 13 | **Review MCP tool logic** | 4h | Implementation analysis |

### Claude (Web) - No Data Required

| # | Task | Effort | Notes |
|---|------|--------|-------|
| 14 | **Document solver algorithm** | 3h | `docs/architecture/solver.md` |
| 15 | **Consolidate API docs** | 4h | Merge scattered docs |
| 16 | **Update CLAUDE.md** | 1h | Add new patterns |
| 17 | **Create operator runbook** | 3h | For production ops |
| 18 | **Add TypeDoc to CI** | 2h | `.github/workflows/` |
| 19 | **Improve error messages** | 1h | `backend/app/core/exceptions.py` |

---

## Sanitized Data Requirements for Analysis

To enable Claude Code analysis without PII exposure, please provide:

### 1. Schedule Metrics Export (REQUIRED)

```json
{
  "block_number": 10,
  "total_half_days": 56,
  "coverage_percentage": 85.7,
  "violations_by_type": {
    "ACGME_80_HOUR": 0,
    "ACGME_1_IN_7": 1,
    "SUPERVISION_RATIO": 0,
    "DOUBLE_BOOKING": 0
  },
  "rotation_distribution": {
    "CLINIC": 120,
    "INPATIENT": 80,
    "PROCEDURES": 40,
    "FMIT": 20
  },
  "pgy_distribution": {
    "PGY1": 5,
    "PGY2": 4,
    "PGY3": 3
  }
}
```

### 2. Workload Distribution (REQUIRED)

```json
{
  "hours_per_person": {
    "min": 40.5,
    "max": 78.0,
    "mean": 62.3,
    "std_dev": 8.2
  },
  "assignments_per_person": {
    "min": 8,
    "max": 14,
    "mean": 11.2
  },
  "gini_coefficient": 0.12
}
```

### 3. Constraint Satisfaction Report (REQUIRED)

```json
{
  "constraints_checked": 15,
  "hard_constraints_passed": 14,
  "soft_constraints_passed": 12,
  "failed_constraints": [
    {
      "constraint": "MIN_REST_BETWEEN_SHIFTS",
      "count": 3,
      "severity": "soft"
    }
  ]
}
```

### 4. Solver Performance (OPTIONAL but helpful)

```json
{
  "solver_used": "CP-SAT",
  "solve_time_seconds": 12.5,
  "iterations": 1500,
  "memory_peak_mb": 256,
  "optimality_gap": 0.02
}
```

### 5. Anonymized Timeline (OPTIONAL)

```csv
date,half_day,rotation_type,pgy_level,is_covered
2026-03-10,AM,CLINIC,PGY1,true
2026-03-10,PM,INPATIENT,PGY2,true
2026-03-10,AM,PROCEDURES,PGY3,true
...
```

**Note:** Replace actual names with generic identifiers:
- Residents: `RES-001`, `RES-002`, etc.
- Faculty: `FAC-001`, `FAC-002`, etc.

---

## Priority Matrix: Now vs Later

### Do Now (This Session)

| Priority | Task | Owner |
|----------|------|-------|
| **P0** | Seed database with Block 10 data | Human |
| **P0** | Run schedule generation | Human |
| **P0** | Export sanitized metrics | Human |
| **P1** | Document solver algorithm | Claude |
| **P1** | Add date validation tests | Claude |

### Do Next (After Checkpoint 2)

| Priority | Task | Owner |
|----------|------|-------|
| **P1** | Analyze coverage gaps | Claude |
| **P1** | Review constraint violations | Claude |
| **P2** | Test swap auto-matcher | Human |
| **P2** | Generate fairness report | Claude |

### Backlog (v1.1.0 Scope)

| Priority | Task | Notes |
|----------|------|-------|
| **P2** | Email notifications | Q1 2026 target |
| **P2** | Bulk import improvements | Q1 2026 target |
| **P3** | Mobile app | Q2 2026 target |
| **P3** | AI/ML analytics | v2.0+ |

---

## Coordination Protocol

### Communication Channels

| Channel | Purpose | Example |
|---------|---------|---------|
| **This Document** | Checkpoint tracking | Update status in tables |
| **Git Commits** | Code changes | Clear commit messages |
| **CHANGELOG.md** | User-facing changes | Version notes |
| **SESSION_*.md** | Session summaries | Parallel work tracking |

### Handoff Pattern

```
Claude Code (IDE) completes Checkpoint N
    ↓
Claude Code (IDE) exports sanitized data
    ↓
Claude Code (IDE) updates this document (marks complete)
    ↓
Claude (Web) receives sanitized JSON
    ↓
Claude (Web) performs analysis
    ↓
Claude (Web) documents findings
    ↓
Human reviews and approves
    ↓
Proceed to Checkpoint N+1
```

### Parallel Work Pattern

```
┌─────────────────────────────────────────────────────────────┐
│  Claude Code (IDE)              │  Claude (Web)             │
├─────────────────────────────────┼───────────────────────────┤
│  Seed database (PII)            │  Document solver algo     │
│  Run schedule generation        │  Review MCP tool code     │
│  Debug violations               │  Update CLAUDE.md         │
│  → Export sanitized metrics ────┼→ Analyze coverage gaps    │
│  Test with real data            │  Generate fairness report │
│  Generate production exports    │  Write operator runbook   │
└─────────────────────────────────┴───────────────────────────┘
```

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| PII in exported data | Medium | High | Use anonymization scripts |
| Solver fails for Block 10 | Low | High | Fallback to greedy solver |
| ACGME violations | Medium | Medium | Iterative constraint tuning |
| Database corruption | Low | Critical | Backup before generation |

### Backup Commands

```bash
# Before any schedule generation
./scripts/backup-db.sh --docker

# Verify backup exists
ls -la backups/postgres/*.sql.gz | tail -1

# Restore if needed
docker compose exec -T db psql -U scheduler -d residency_scheduler < backup.sql
```

---

## Current Blockers

| # | Blocker | Owner | Resolution | Status |
|---|---------|-------|------------|--------|
| 1 | ~~Branch not pushed to remote~~ | Claude | Push with `-u origin` | ✅ Resolved |
| 2 | ~~DB not seeded with Block 10 data~~ | Human | Run seed script | ✅ Resolved |
| 3 | No sanitized export yet | Claude Code (IDE) | Export after ACGME validation | ⏳ Pending |
| 4 | ~~Weekend coverage missing~~ | Claude Code (IDE) | Root cause: inpatient rotations not loaded | ✅ Identified |
| 5 | ~~Backup stale (16h old)~~ | Claude Code (IDE) | Run `./scripts/backup-db.sh --docker` | ✅ Created |
| 6 | Inpatient rotation loading | Claude Web | Design pre-solver input for inpatient constraints | ⏳ CP3 Task |
| 7 | NF/PC headcount constraint | Claude Web | Add constraint: max 1-2 residents on NF per week | ⏳ CP3 Task |
| 8 | Block↔Rotation mapping | Claude Web | Verify `tbl ResidencyBlockSchedule` has block-rotation associations | ⏳ CP3 Research |
| 9 | Faculty FMIT pre-loading | Claude Web | Check if `tbl Faculty Inpatient Schedule` should be hardcoded | ⏳ CP3 Research |

---

## Version History

| Date | Author | Changes |
|------|--------|---------|
| 2025-12-24 | Claude | Initial roadmap creation |
| 2025-12-24 | Claude Code (IDE) | Updated CP1 ✅, CP2 ⚠️ partial (71% coverage, weekends missing) |
| 2025-12-24 | Claude Code (IDE) | Root cause: inpatient rotations not loaded. Backup created. Handoff to CP3. |
| 2025-12-24 | Claude Code (IDE) | Verified NF/PC bug: 70 NF assignments to ALL 29 people (no headcount constraint) |
| 2025-12-24 | Claude Code (IDE) | Added Airtable refs: tbl ResidencyBlockSchedule, tbl Faculty Inpatient Schedule |
| 2025-12-24 | Claude Code (IDE) | Added sanitized data export: 38 rotation templates, max_residents=NULL confirmed |
| 2025-12-24 | Claude Code (IDE) | Added preserve_fmit pattern as template; FMIT rules: 1 per PGY/block, faculty=weekly |
| 2025-12-24 | Claude Code (IDE) | FULL business rules: FMIT clinic days, NF=1, C30/PC timing, inter-block PC critical, NICU+NF |
| 2025-12-24 | Claude Code (IDE) | Added faculty call constraints (hard + soft), sanitized FMIT schedule, inter-block handoffs |
| 2025-12-24 | Claude Code (IDE) | New constraints needed: PostFMITSundayBlockingConstraint, CallSpacingConstraint |
| 2025-12-24 | Claude Code (IDE) | Future: decay factor for FMIT/call recency (not Block 10 scope) |

---

## Quick Reference

### Claude Code (IDE) - Full Access Commands
```bash
# Seed database with Block 10 data
cd backend && python scripts/seed_data.py

# Generate schedule
docker compose exec backend python -m app.scheduling.engine --block 10

# Run full test suite with real DB
cd backend && pytest

# Export sanitized metrics for Claude Web
python scripts/export_sanitized_metrics.py --block 10 --include-violations -o /tmp/block10_metrics.json

# Test with real data
cd frontend && npm run dev  # View actual schedule
```

### Claude (Web) - Sanitized Data Analysis
```
# Provide these files to Claude Web for analysis:
- block10_metrics.json (coverage, workload, violations)
- Anonymized timeline CSV (if needed)
- Solver benchmark results

# Claude Web can review code directly (no PII in source):
- backend/app/scheduling/*.py
- backend/app/resilience/*.py
- mcp-server/src/*.py
```

### Human - Approval & Strategy
```bash
# Review schedule visually
open http://localhost:3000/schedule

# Approve production export
# Review CHANGELOG updates
# Make strategic decisions
```

---

*This document is a living roadmap. Update checkpoint statuses as work progresses.*
