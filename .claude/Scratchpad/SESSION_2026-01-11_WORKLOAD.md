# Session 2026-01-11: Integrated Workload Constraint

## Summary

Implemented faculty workload fairness automation to replace manual distribution.

## What Was Done

### 1. IntegratedWorkloadConstraint (COMPLETE)

**File:** `backend/app/scheduling/constraints/integrated_workload.py`

Tracks 5 workload categories:
- Call (overnight) - weight 1.0
- FMIT weeks - weight 3.0
- Clinic half-days - weight 0.5
- Admin half-days (GME, DFM) - weight 0.25
- Academic half-days (LEC, ADV) - weight 0.25

Features:
- Min-max fairness optimization
- Excludes titled faculty (PD, APD, OIC, Dept Chief) by default
- Per-category min/max/mean/spread stats
- Variance-based penalty for solver
- CP-SAT and PuLP support

### 2. Constraint Registration (COMPLETE)

**File:** `backend/app/scheduling/constraint_registry.py`

Added IntegratedWorkloadConstraint to registry under EQUITY category.

### 3. FairnessAuditService (COMPLETE)

**File:** `backend/app/services/fairness_audit_service.py`

Provides:
- `generate_audit_report(start_date, end_date)` - full workload audit
- Per-category statistics (call, FMIT, clinic, admin, academic)
- Jain's fairness index (0-1)
- Outlier detection (>1.25x or <0.75x mean)
- Individual faculty workload breakdown

## What's Left

### 1. API Endpoints (NOT STARTED)

Need to create `backend/app/api/routes/fairness.py`:
```
GET /api/fairness/audit?start_date=...&end_date=...
GET /api/fairness/faculty/{id}/history
```

### 2. Tests (NOT STARTED)

Need tests for:
- IntegratedWorkloadConstraint
- FairnessAuditService

### 3. Frontend Dashboard (NOT STARTED)

Display workload fairness in GUI.

## Files Created/Modified

| File | Status |
|------|--------|
| `backend/app/scheduling/constraints/integrated_workload.py` | CREATED |
| `backend/app/scheduling/constraint_registry.py` | MODIFIED |
| `backend/app/services/fairness_audit_service.py` | CREATED |

## Branch

`feature/session-20260111-b`

## Commit Pending

Changes not yet committed. Ready for:
```bash
git add backend/app/scheduling/constraints/integrated_workload.py \
        backend/app/scheduling/constraint_registry.py \
        backend/app/services/fairness_audit_service.py
git commit -m "feat: Add IntegratedWorkloadConstraint and FairnessAuditService"
```

## Context from Earlier

### HUMAN_TODO Updates Needed
- Remove "Resident NF Call" and "Resident LND Call" (don't exist)
- Mark "Faculty FMIT and Call Equity" as addressed by IntegratedWorkloadConstraint

### Codex Tasks
Already set up in `.codex/AGENTS.md`:
1. MCP CI test failures
2. Seaborn warning cleanup
3. MCP 401 token refresh

## Decision: Clinic Equity

User clarified that clinic assignments are role-based (PD=0, APD=2, OIC=2, etc.), so a separate ClinicEquityConstraint is NOT needed. The IntegratedWorkloadConstraint handles Core faculty equity implicitly.

## Workload Formula

```python
workload_score = (
    call_count × 1.0 +
    fmit_weeks × 3.0 +
    clinic_halfdays × 0.5 +
    admin_halfdays × 0.25 +
    academic_halfdays × 0.25
)
```

Min-max fairness: minimize maximum workload score across faculty.
