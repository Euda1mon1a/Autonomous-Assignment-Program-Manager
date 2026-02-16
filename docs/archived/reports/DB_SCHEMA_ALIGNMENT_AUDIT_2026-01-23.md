# DB-Schema Alignment Audit Report

> **Generated:** 2026-01-23 | **Session:** 136
> **Scope:** SQLAlchemy models ↔ Pydantic schemas ↔ Database tables
> **Methodology:** Cross-layer comparison of 87 models, 93 schemas, 87 tables

---

## Executive Summary

| Layer | Total | Synced | Drift |
|-------|-------|--------|-------|
| **Models ↔ Database** | 87 | 75 | 12 missing + 7 orphaned |
| **Models ↔ Schemas** | 87 | ~80 | ~7 misaligned |
| **Naming Convention** | N/A | ❌ MISSING | Critical gap |
| **Automated Tests** | 0 | ❌ NONE | No drift detection |

**Overall Risk: MODERATE** - Naming is consistent (snake_case throughout), but no enforcement mechanisms exist. Drift has already occurred.

---

## The Bridge Architecture

```
PostgreSQL (snake_case columns)
        ↓ SQLAlchemy ORM (1:1 mapping, no transformation)
Python Models (snake_case attributes)
        ↓ from_attributes=True (automatic ORM mapping)
Pydantic Schemas (snake_case fields)
        ↓ JSON serialization
API Response (snake_case keys)
        ↓ Axios interceptor (ONLY conversion point)
Frontend TypeScript (camelCase)
```

**Key Insight:** Unlike frontend ↔ backend (which has transformation bugs), DB ↔ backend has **drift bugs** - fields added to one layer but not propagated to others.

---

## Critical Findings

### C-1: No SQLAlchemy Naming Convention (CRITICAL)

**Location:** `backend/app/db/base.py`

**Current (MISSING):**
```python
class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass
```

**Should Be:**
```python
from sqlalchemy import MetaData

naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=naming_convention)
```

**Impact:**
- Constraint names are auto-generated gibberish (`fk_1a2b3c4d`)
- Alembic can't reliably detect constraint changes
- Database schema becomes unmaintainable

---

### C-2: No Model-Database Drift Tests (CRITICAL)

**Gap:** No pytest test validates that model definitions match database schema.

**Missing Test Pattern:**
```python
# test_models_match_database.py
def test_models_match_database():
    """Verify all model columns exist in database."""
    from sqlalchemy import inspect

    inspector = inspect(engine)
    for model in Base.__subclasses__():
        table_name = model.__tablename__
        db_columns = {col['name'] for col in inspector.get_columns(table_name)}
        model_columns = {col.name for col in model.__table__.columns}

        assert model_columns == db_columns, f"Drift in {table_name}"
```

---

### C-3: No Schema-Model Alignment Tests (CRITICAL)

**Gap:** No pytest test validates that Pydantic schema fields match SQLAlchemy model columns.

**Current State:** 11 core Response schemas have `from_attributes=True`, but nothing validates alignment.

---

## Model ↔ Database Drift (Existing)

From `SCHEMA_AUDIT_REPORT.md` (2026-01-11):

### Models Missing from Database (12)

| Table | Status | Notes |
|-------|--------|-------|
| `calendar_subscriptions` | ❌ No migration | Planned feature |
| `export_jobs` | ❌ No migration | Export system |
| `export_job_executions` | ❌ No migration | Export system |
| `oauth2_authorization_codes` | ❌ No migration | OAuth2 PKCE |
| `pkce_clients` | ❌ No migration | OAuth2 PKCE |
| `webhooks` | ❌ No migration | Webhook system |
| `webhook_deliveries` | ❌ No migration | Webhook system |
| `webhook_dead_letters` | ❌ No migration | Webhook system |
| `schema_versions` | ❌ No migration | Schema registry |
| `schema_change_events` | ❌ No migration | Schema registry |
| `state_machine_instances` | ❌ No migration | Workflow engine |
| `state_machine_transitions` | ❌ No migration | Workflow engine |

### Extra Tables in Database (7)

| Table | Status | Notes |
|-------|--------|-------|
| `alembic_version` | ✓ Expected | Alembic tracking |
| `absence_version` | ⚠️ Legacy | Old Continuum table |
| `chaos_experiments` | ? Unknown | Resilience testing? |
| `faculty_activity_permissions` | ? Unknown | Orphaned? |
| `metric_snapshots` | ? Unknown | Monitoring? |
| `schedule_diffs` | ? Unknown | Diff tracking? |
| `schedule_versions` | ? Unknown | Versioning? |

---

## Model ↔ Schema Alignment Analysis

### Core Domain Schemas (All Have `from_attributes=True`)

| Schema | Model | Fields Match | Notes |
|--------|-------|--------------|-------|
| PersonResponse | Person | ✓ | 13 fields aligned |
| AssignmentResponse | Assignment | ✓ | 12 fields aligned |
| BlockResponse | Block | ✓ | 6 fields aligned |
| RotationTemplateResponse | RotationTemplate | ✓ | 13 fields aligned |
| ActivityResponse | Activity | ⚠️ Partial | Missing `provides_supervision`, `counts_toward_physical_capacity` |
| AbsenceResponse | Absence | ✓ | 13 fields aligned |
| SwapRecordResponse | SwapRecord | ✓ | 11 fields aligned |
| ProcedureCredentialResponse | ProcedureCredential | ✓ | 12 fields aligned |
| BlockAssignmentResponse | BlockAssignment | ✓ | 12 fields aligned |

### Schemas Without `from_attributes=True`

| Schema | Reason | Risk |
|--------|--------|------|
| ScheduleResponse | Computed response, not ORM | Low |
| AuditLogResponse | Uses aliases for camelCase | Low |
| BlockMatrixResponse | Computed matrix, not ORM | Low |

### Potential Alignment Issues

1. **ActivityResponse** missing model fields:
   - `provides_supervision` (model has, schema missing)
   - `counts_toward_physical_capacity` (model has, schema missing)

2. **Activity schema field name mismatch:**
   - Schema has `activities` list field
   - Other schemas use `items` - inconsistent pattern

---

## Naming Convention Analysis

### What's Working ✓

| Aspect | Status | Evidence |
|--------|--------|----------|
| Column naming | ✓ snake_case | All 87 models consistent |
| Table naming | ✓ lowercase plural | `people`, `assignments`, `blocks` |
| Pydantic fields | ✓ snake_case | Matches model attributes |
| Enum values | ✓ snake_case | `one_to_one`, `absorb`, etc. |

### What's Missing ✗

| Aspect | Status | Impact |
|--------|--------|--------|
| Naming convention on Base | ❌ MISSING | Constraint names unmaintainable |
| Model-DB drift tests | ❌ MISSING | Drift goes undetected |
| Schema-Model tests | ❌ MISSING | Misalignment goes undetected |
| Live schema audit | ❌ Snapshot only | SCHEMA_AUDIT_REPORT.md dated 2026-01-11 |

---

## Remediation Plan

### Phase 1: Critical (Do Now - 2 hours)

| Task | File | Change |
|------|------|--------|
| Add naming convention | `backend/app/db/base.py` | Add `MetaData(naming_convention=...)` |
| Create model-DB test | `backend/tests/test_model_database_sync.py` | Query `information_schema`, compare to models |
| Create schema-model test | `backend/tests/test_schema_model_sync.py` | Compare Pydantic fields to SQLAlchemy columns |

### Phase 2: High (This Week - 4 hours)

| Task | File | Change |
|------|------|--------|
| Fix Activity schema | `backend/app/schemas/activity.py` | Add missing fields |
| Create pre-commit hook | `scripts/schema-model-sync.sh` | Run alignment check on commit |
| Automate schema audit | `scripts/generate-schema-audit.py` | Replace snapshot with live report |

### Phase 3: Medium (Pre-Production - 4 hours)

| Task | Status | Change |
|------|--------|--------|
| Resolve 12 missing tables | Decide: migrate or remove models | Create migrations or delete code |
| Investigate 7 extra tables | Audit for orphaned data | Document or create models |
| Add CI check | GitHub Actions | Run sync tests in CI |

---

## Test Verification

```bash
# After adding tests:

# 1. Model-Database sync
pytest backend/tests/test_model_database_sync.py -v
# Should fail on 12 missing tables until migrations added

# 2. Schema-Model sync
pytest backend/tests/test_schema_model_sync.py -v
# Should catch Activity schema missing fields

# 3. Pre-commit hook
git commit -m "test"
# Should run schema-model-sync.sh automatically
```

---

## Cross-References

| Finding | Related Report | Action |
|---------|----------------|--------|
| Missing webhooks tables | API Coverage Matrix | Routes exist, tables don't |
| Missing schema_versions | MCP Tools Audit | Schema registry incomplete |
| Activity schema gaps | Skills Audit | Test coverage gap |

---

## Comparison: Frontend-Backend vs DB-Backend Issues

| Aspect | Frontend ↔ Backend | DB ↔ Backend |
|--------|-------------------|--------------|
| **Transformation** | axios converts snake→camel | No transformation (1:1) |
| **Risk Type** | Case mismatch bugs | Drift bugs (missing fields) |
| **Enforcement** | Modron March hook ✓ | NONE ❌ |
| **Tests** | TypeScript compiler ✓ | NONE ❌ |
| **Documentation** | CLAUDE.md comprehensive ✓ | Sparse ❌ |

**Key Insight:** Frontend-backend has better enforcement than DB-backend, despite DB-backend being simpler.

---

## Appendix: Model Column Reference

### Core Models with Column Counts

| Model | Table | Columns | Relationships |
|-------|-------|---------|---------------|
| Person | `people` | 20 | 10 |
| Assignment | `assignments` | 16 | 4 |
| Block | `blocks` | 9 | 1 |
| Absence | `absences` | 13 | 2 |
| Activity | `activities` | 16 | 0 |
| RotationTemplate | `rotation_templates` | 18 | 6 |
| CallAssignment | `call_assignments` | 7 | 1 |
| HalfDayAssignment | `half_day_assignments` | 13 | 4 |
| SwapRecord | `swap_records` | 17 | 2 |
| User | `users` | 9 | 0 |
| Procedure | `procedures` | 12 | 1 |
| ProcedureCredential | `procedure_credentials` | 14 | 2 |

### Versioned Models (SQLAlchemy-Continuum)

- Assignment (`assignments_version`)
- Absence (`absences_version`)
- RotationTemplate (`rotation_templates_version`)
- SwapRecord (`swap_records_version`)

---

## Summary

**Good News:**
- Naming is consistent (snake_case throughout DB → model → schema)
- Core schemas have `from_attributes=True` for ORM mapping
- No transformation layer means simpler debugging
- Alembic migration naming is enforced

**Action Required:**
- 1 Critical infrastructure gap (naming convention)
- 2 Critical test gaps (model-DB, schema-model)
- 12 models missing from database
- 7 orphaned tables need investigation
- Activity schema missing 2 fields

**Estimated Total Effort:** 10 hours

---

*DB-Schema alignment audit based on 87 models, 93 schemas, and existing SCHEMA_AUDIT_REPORT.md.*
