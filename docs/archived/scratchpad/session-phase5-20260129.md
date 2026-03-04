# Session Scratchpad: CP-SAT Phase 5 Implementation (2026-01-29)

## Session Summary
- **Phase 5.0 COMMITTED** - Schedule override layer (`5826b410`)
- **Phase 5.1 implemented by Codex** - Call overrides, cascade planner, GAP overrides
- **Test failures discovered** - Missing imports, schema issues, env mismatch
- **Partial fixes applied** - 2 of 4 tests now passing

---

## Current Status: P5.1 Tests Need Fixing

### Committed (Phase 5.0)
```
5826b410 feat(scheduling): CP-SAT Phase 5 - schedule override layer
```
- ✅ ScheduleOverride model (coverage, cancellation, gap)
- ✅ Admin-only routes (create, list, deactivate)
- ✅ Overlay integration (`include_overrides` param)
- ✅ Frontend types regenerated

### Uncommitted (Phase 5.1 - Codex work)
- Call overrides (model, schema, service, routes)
- Cascade planner (`/admin/schedule-overrides/cascade`)
- GAP override type for unfilled supervision slots
- Sacrifice hierarchy: GME/DFM → Clinic → Procedures → PROTECTED (FMIT/AT/PCAT/DO)
- Post-call PCAT/DO auto-GAP creation

---

## Test Status

| Test | Status | Issue |
|------|--------|-------|
| `test_overrides_require_auth` | ✅ PASS | |
| `test_cascade_creates_gap_for_post_call_pcat_do` | ✅ PASS | |
| `test_create_list_deactivate_and_overlay` | ❌ FAIL | List endpoint returns 400 |
| `test_gap_override_renders_gap` | ❌ FAIL | Assignment not found in overlay |

### Fixes Applied by Claude
1. ✅ Added `async def get()` to `tests/conftest.py` AsyncSessionWrapper
2. ✅ Added `from app.models.schedule_override import ScheduleOverride` to cascade service
3. ✅ Added `"gap"` to `CascadeOverrideStep.override_type` Literal

### Remaining Issues (for Codex)
- List endpoint returning 400 - need to debug validation error
- GAP not appearing in overlay response - `is_gap` field issue?

---

## Environment Discovery

**Critical finding:** Codex was using system Python, not venv

| Environment | Python | bcrypt | Status |
|-------------|--------|--------|--------|
| System `/usr/bin/python3` | 3.9.6 | 5.0.0 | ❌ Wrong |
| **backend/venv** | 3.11.14 | 4.3.0 | ✅ Correct |
| Docker | 3.12.12 | 4.3.0 | ✅ Correct |

**Solution for Codex:**
```bash
# Option A: Use venv
source backend/venv/bin/activate
pytest tests/routes/test_schedule_overrides.py -v

# Option B: Use Docker (recommended)
docker exec scheduler-local-backend pytest tests/routes/test_schedule_overrides.py -v
```

---

## Branch Status

- **Branch:** `cpsat-phase5`
- **Last commit:** `5826b410` (Phase 5.0)
- **Uncommitted:** P5.1 files (~15 files)

### Uncommitted Files (P5.1)
```
M  backend/app/api/routes/__init__.py
M  backend/app/api/routes/call_assignments.py
M  backend/app/api/routes/daily_manifest.py
M  backend/app/api/routes/schedule_overrides.py
M  backend/app/models/__init__.py
M  backend/app/models/schedule_override.py
M  backend/app/schemas/__init__.py
M  backend/app/schemas/cascade_override.py  # Fixed: added "gap"
M  backend/app/services/cascade_override_service.py  # Fixed: added import
M  backend/app/services/half_day_schedule_service.py
M  backend/tests/conftest.py  # Fixed: added async get()
?? backend/alembic/versions/20260129_add_call_overrides.py
?? backend/alembic/versions/20260129_add_gap_override_type.py
?? backend/app/api/routes/call_overrides.py
?? backend/app/models/call_override.py
?? backend/app/schemas/call_override.py
?? backend/app/services/call_override_service.py
?? backend/app/services/cascade_override_service.py
```

---

## Policy Decisions (Locked In)

### Sacrifice Hierarchy
1. GME/DFM (admin) - first to sacrifice
2. Faculty solo clinic - second
3. Procedure supervision (VAS/SM/BTX/COLPO) - third
4. **PROTECTED (never auto-sacrifice):** FMIT, AT, PCAT, DO

### Override Types
- `coverage` - replacement person fills slot
- `cancellation` - slot removed from schedule
- `gap` - slot unfilled, visible shortage (the "red cell")

### Cascade Rules
- Max depth: 2
- Auto-GAP for post-call PCAT/DO
- Adjuncts cannot cover AT/PCAT/DO
- Next-day protected conflicts: warn + 2.0 penalty

---

## For Next Session

1. **Codex must fix remaining 2 test failures**
   - Use venv OR Docker for testing
   - Debug list endpoint 400 error
   - Debug GAP overlay rendering

2. **After tests pass:** Commit P5.1, push, create PR

3. **Report location:** `/Users/aaronmontgomery/.claude/plans/toasty-singing-pixel.md`

---

## Key Files Reference

| File | Purpose |
|------|---------|
| `backend/app/services/cascade_override_service.py` | Cascade planner logic |
| `backend/app/models/schedule_override.py` | Override model (coverage/cancellation/gap) |
| `backend/app/models/call_override.py` | Call override model |
| `backend/tests/conftest.py` | Test fixtures (AsyncSessionWrapper) |
| `backend/tests/routes/test_schedule_overrides.py` | P5.1 tests |

---

*Session ready for compact. 2 tests passing, 2 need Codex fix with proper env.*
