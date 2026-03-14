# Overnight Work Plan — 2026-03-14

> **Status:** Ready for execution | **Source:** Gemini audit chain + Claude session
> **Context files:** `HARDCODED_TO_POSTGRES_ROADMAP.md`, `.claude/plans/polished-inventing-boot.md`
> **Branch:** Start from `main` (HEAD after PR #1305)

---

## What Was Done Today (PRs #1293-#1305)

| Track | Status | Key Files Changed |
|-------|--------|-------------------|
| Task history learning (Phases 1-6) | DONE | task_history_service.py, api routes, MCP tools, /recall skill |
| GlassWorm supply chain defense | DONE | 3 scripts, security.yml |
| Constraint config → DB (engine reads) | DONE | engine.py, constraints.py, seed_constraints.py |
| Constraint docs decontamination | DONE | RAG summary, CATALOG, ENABLEMENT_GUIDE |
| ACGME reads ApplicationSettings | DONE | acgme.py (80HourRule, 1in7Rule, SupervisionRatio) |
| Preload classification columns | DONE | rotation_template.py + migration + rotation_codes.py |
| Primary duty config → Postgres | DONE | primary_duty_config.py + migration + primary_duty.py |
| Block 13 regeneration | DONE | MUC for MILITARY, 0 violations |

## What Remains (Priority Order)

### 1. Fix Stale Primary Duty Tests (BLOCKING — do first)

5 test failures from removed JSON loader contract:

**File:** `tests/scheduling/test_primary_duty_constraint.py`
- 2 tests call `load_primary_duties_config()` with a JSON path — update to pass a mock db_session or use `duty_configs={}` directly

**File:** `tests/scheduling/constraints/test_primary_duty.py`
- 3 tests use the old JSON/path interface — same fix

**Fix pattern:**
```python
# OLD (broken):
configs = load_primary_duties_config(json_path="test_data.json")

# NEW:
# Option A: Pass configs directly (no DB needed for unit tests)
constraint = FacultyPrimaryDutyClinicConstraint(duty_configs={})

# Option B: Mock db_session
from unittest.mock import MagicMock
mock_session = MagicMock()
mock_session.query.return_value.all.return_value = []
configs = load_primary_duties_config(db_session=mock_session)
```

**Also:** Delete `from_airtable_record()` classmethod on PrimaryDutyConfig (line 76) — it's dead code. Tests that use it should be updated.

### 2. Primary Duty CRUD API Routes (HIGH)

The `primary_duty_configs` table exists but has no API routes. Coordinators can't edit from the UI.

**Create:** `backend/app/api/routes/primary_duty_configs.py`

```python
# Endpoints needed:
GET    /api/v1/primary-duty-configs/           — list all
GET    /api/v1/primary-duty-configs/{id}       — get one
PATCH  /api/v1/primary-duty-configs/{id}       — update clinic_min/max, available_days
POST   /api/v1/primary-duty-configs/           — create new
DELETE /api/v1/primary-duty-configs/{id}       — delete
```

**Pattern:** Follow `constraints.py` (DB-direct, no intermediate service). Auth: `get_current_active_user` + `require_admin()`.

**Register:** Add to `backend/app/api/routes/__init__.py`

**Schemas:** Create `backend/app/schemas/primary_duty_config.py` with Create/Update/Response models.

### 3. Expose Preload Classification in Rotation Template API (HIGH)

The 5 new columns on `rotation_templates` (is_offsite, is_lec_exempt, is_continuity_exempt, is_saturday_off, preload_activity_code) are not in the API schemas or frontend types.

**Files to update:**
- `backend/app/schemas/rotation_template.py` — add 5 fields to response schema
- `frontend/src/types/api-generated.ts` — regenerate: `cd frontend && npm run generate:types`
- `frontend/src/app/admin/` — add fields to rotation template admin form (if one exists)

### 4. Hard→Soft Constraint Refactor — ACGME Batch (MEDIUM)

Convert 3 ACGME constraints from HardConstraint to SoftConstraint:

**File:** `backend/app/scheduling/constraints/acgme.py`

For each:
1. Change base class: `class EightyHourRuleConstraint(HardConstraint)` → `class EightyHourRuleConstraint(SoftConstraint)`
2. Add `weight=1000` to `__init__()`
3. In `add_to_cpsat()`: replace `model.Add(sum <= max)` with indicator variable + penalty:
   ```python
   # Instead of: model.Add(block_sum <= self.max_blocks_per_window)
   # Use:
   violation = model.NewBoolVar(f"80hr_violation_{window}")
   model.Add(block_sum <= self.max_blocks_per_window).OnlyEnforceIf(violation.Not())
   model.Add(block_sum > self.max_blocks_per_window).OnlyEnforceIf(violation)
   penalty_vars.append(violation)
   ```
4. Add to objective: `model.Minimize(sum(penalty_vars) * weight)`

**Test:** Regenerate Block 13 after each conversion — verify solver still produces valid schedule.

**Constraints to convert (in order):**
- `EightyHourRuleConstraint` (weight=1000)
- `OneInSevenRuleConstraint` (weight=1000)
- `SupervisionRatioConstraint` (weight=1000)

### 5. Hard→Soft — Remaining 13 Constraints (LARGE)

After ACGME batch proves the pattern works, convert remaining policy constraints. See `HARDCODED_TO_POSTGRES_ROADMAP.md` Track 1 for the full list with recommended weights.

**Order:**
1. Faculty policy: FacultyPrimaryDutyClinic, FacultyDayAvailability, FacultyRoleClinic (weight=100)
2. Call policy: OvernightCallCoverage, OvernightCallGeneration, NightFloatPostCall (weight=200-500)
3. Scheduling: WednesdayAMInternOnly, PostFMITRecovery (weight=50-200)
4. FMIT: FMITWeekBlocking, FMITMandatoryCall (weight=200)
5. SM: SMResidentFacultyAlignment, SMFacultyNoRegularClinic (weight=50)
6. AdjunctCallExclusion → move to eligibility filter (not a constraint)

---

## Key File Locations

| File | What |
|------|------|
| `backend/app/scheduling/constraints/acgme.py` | ACGME constraints (lines 189, 519, 795) |
| `backend/app/scheduling/constraints/manager.py` | Constraint registration (create_default) |
| `backend/app/scheduling/constraints/primary_duty.py` | Primary duty constraints (DB-backed) |
| `backend/app/models/primary_duty_config.py` | Primary duty DB model |
| `backend/app/models/rotation_template.py` | Rotation template with preload columns |
| `backend/app/services/preload/rotation_codes.py` | Preload activity code logic |
| `backend/app/scheduling/engine.py` | Engine init (settings + constraints) |
| `backend/seed_constraints.py` | Constraint DB seeder |
| `docs/planning/HARDCODED_TO_POSTGRES_ROADMAP.md` | Full 6-track plan |

## Verification Checklist (per PR)

- [ ] `cd backend && pytest tests/ -x -q` — 595+ pass (ignore cache test)
- [ ] `alembic upgrade head` + `alembic downgrade -1` + `upgrade head` (if migration)
- [ ] Pre-commit hooks pass
- [ ] Block 13 regeneration produces 0 violations (for solver changes)
- [ ] `cd frontend && npm run lint` (if frontend changes)

## Do NOT Touch

- `backend/app/core/config.py` — configuration
- `backend/app/core/security.py` — auth
- `backend/app/db/` — DB session/base
- Existing migrations — never edit, create new ones
- `.env` — never read or commit
