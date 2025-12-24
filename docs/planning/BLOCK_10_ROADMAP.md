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

### Checkpoint 1: Data Preparation (CLAUDE CODE IDE)

**Owner:** Claude Code (IDE) - has full PII access

| Task | Status | Notes |
|------|--------|-------|
| Export residents from Airtable | Pending | JSON format, local only |
| Export faculty from Airtable | Pending | JSON format, local only |
| Export rotation templates | Pending | JSON format |
| Export absences/leave | Pending | Block 10 date range |
| Seed database with test data | Pending | Via `scripts/seed_data.py` |
| Verify DB connection | Pending | `docker compose exec db psql` |

**Completion Criteria:**
- [ ] Database contains all personnel for Block 10
- [ ] Rotation templates loaded
- [ ] Known absences entered

---

### Checkpoint 2: Schedule Generation Test (CLAUDE CODE IDE)

**Owner:** Claude Code (IDE) generates and runs validation

| Task | Owner | Status |
|------|-------|--------|
| Run Block 10 generation | Claude Code (IDE) | `docker compose exec backend python -m app.scheduling.engine --block 10` |
| Validate ACGME compliance | Claude Code (IDE) | Direct DB queries |
| Check coverage metrics | Claude Code (IDE) | Generate report |
| Export sanitized metrics | Claude Code (IDE) | For Claude Web analysis |

**Completion Criteria:**
- [ ] Schedule generated without errors
- [ ] < 5 ACGME violations
- [ ] > 80% coverage achieved
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

**Completion Criteria:**
- [ ] Coverage analysis document created
- [ ] Optimization recommendations provided
- [ ] No PII in analysis outputs

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

| # | Blocker | Owner | Resolution |
|---|---------|-------|------------|
| 1 | Branch not pushed to remote | Claude | Push with `-u origin` |
| 2 | DB not seeded with Block 10 data | Human | Run seed script |
| 3 | No sanitized export yet | Human | Export after generation |

---

## Version History

| Date | Author | Changes |
|------|--------|---------|
| 2025-12-24 | Claude | Initial roadmap creation |

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
