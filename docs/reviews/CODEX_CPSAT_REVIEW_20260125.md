# Codex CP-SAT Pipeline Review

**Date:** 2026-01-25
**Reviewer:** Claude Code (read-only)
**Branch:** `cpsat-pipeline-next`
**Commits Reviewed:** 12 (Codex) + 2 (Claude Code)

---

## Summary

Codex implemented substantial preload infrastructure for the CP-SAT canonical pipeline, including:
- Protected rotation patterns (LEC/ADV, Wednesday patterns, intern continuity)
- Off-site TDY patterns (Hilo, Okinawa, Kapiolani)
- Night float patterns (NF, PEDNF, LDNF)
- Call assignment editing with auto post-call regeneration
- Row mapping enforcement in export

**Overall Assessment:** Solid implementation. Well-structured code with good test coverage for new patterns.

---

## Commits by Category

### 1. Preload Infrastructure (Core Work)

**`314c7751` feat(scheduling): preload protected patterns incl OKI**
- **+841 LOC** across preload services
- Added rotation alias normalization (`_ROTATION_ALIASES`)
- Defined exempt rotation sets for LEC, continuity clinic, off-site
- Implemented pattern generators:
  - `_get_hilo_codes()` - Thu/Fri clinic before, Tue clinic after TDY
  - `_get_kap_codes()` - Kapiolani L&D with Mon PM off, Tue off
  - `_get_ldnf_codes()` - L&D NF with Friday clinic
  - `_get_nf_codes()` - Standard NF/PEDNF off-AM patterns
- Mid-block transition support via `_resolve_rotation_code_for_date()`
- Compound rotation parsing (`NEURO-1ST-NF-2ND`, `NEURO/NF`, `NEURO+NF`)

**Key Design Decision:** Okinawa uses same pattern as Hilo (Thu/Fri clinic before, return-Tue clinic after).

### 2. Testing

**`98fc4935` test(scheduling): cover OKI preloads + sqlite JSONB**
- New test file: `test_sync_preload_protected_patterns.py` (222 LOC)
- Tests cover:
  - Wednesday patterns (intern continuity AM, LEC PM)
  - Last Wednesday (LEC AM, ADV PM)
  - Hilo pre/post clinic pattern
  - NF split block weekends

**`314c7751`** also includes test updates to `test_pipeline_order.py`

### 3. Call Assignment Editing

**`ea0387ab` feat(editing): override locks + auto post-call**
- Added `auto_generate_post_call` flag to call update schema
- `_clear_post_call_assignments()` - removes stale PCAT/DO before regeneration
- Bulk update support with post-call regeneration
- Pattern: Update call → clear old post-call → regenerate new post-call

### 4. Export Pipeline

**`988764f3` feat(export): enforce row mappings**
- Strict row mapping in `canonical_schedule_export_service.py`
- `xml_to_xlsx_converter.py` updated with fail-fast on missing mapping

**`6cdaab89` fix(api): allow block 0 half-day queries**
- Block 0 (orientation) was being rejected by API validation
- Fix: Allow `block_number >= 0` instead of `> 0`

### 5. Infrastructure/Docs

| Commit | Change |
|--------|--------|
| `9f0a6c44` | Roadmap export status update |
| `7c4f29ee` | Modron March type check alignment |
| `43f1d1ad` | Frontend types regeneration |
| `4b82439e` | Roadmap status update |
| `610c3eab` | `.env.codex` setup for Codex |
| `1dc87d13` | PD scheduling readiness review |

---

## Code Quality Observations

### Strengths

1. **Good separation of concerns** - Rotation logic isolated in helper methods
2. **Comprehensive alias handling** - Multiple spellings normalized to canonical codes
3. **Mid-block transition support** - Properly handles compound rotations
4. **Test coverage** - New test file covers critical patterns
5. **Fail-fast approach** - Export enforces row mapping instead of silent skip

### Areas for Future Improvement

1. **Code duplication** - `preload_service.py` and `sync_preload_service.py` have identical pattern logic (~300 LOC duplicated). Consider extracting to shared module.

2. **Magic numbers** - `day_index in (0, 1)` and `day_index == 19` for Hilo could use named constants:
   ```python
   HILO_PRE_CLINIC_DAYS = {0, 1}  # Thu/Fri before TDY
   HILO_RETURN_DAY = 19  # 4th Tuesday
   ```

3. **Hardcoded activity codes** - Codes like "C", "LEC", "ADV", "TDY" are string literals. Consider enum or constant module.

4. **Missing docstrings** - Some helper methods lack docstrings (e.g., `_is_lec_exempt`)

5. **OKI documentation** - The Okinawa=Hilo pattern assumption should be documented in `BLOCK_SCHEDULE_RULES.md`

---

## Roadmap Status (from `CP_SAT_PIPELINE_ROADMAP.md`)

| Phase | Status | Notes |
|-------|--------|-------|
| 0. Preconditions | ✅ Done | Pipeline merged |
| 1. Preloads | ✅ Done | All protected patterns implemented |
| 2. CP-SAT Block/Call | ⚠️ Issue | Block 10 infeasibility (missing templates) |
| 3. Post-call Sync | ✅ Done | PCAT/DO sync implemented |
| 4. Activity Solver | ⏳ Partial | Requirements records incomplete |
| 5. JSON Export | ✅ Done | Strict row mapping |
| 6. JSON→XLSX | ✅ Done | Merged-cell safe |
| 7. Frontend Export | ⚠️ Blocked | Auth bypass issue (CRITICAL #1) |

---

## Known Issues Identified

1. **Block 10 CP-SAT infeasibility** - Missing PCAT/DO/SM templates caused solver failure (documented in roadmap)

2. **Frontend export auth** - Still uses raw `fetch()` instead of axios (CRITICAL #1 in priority list)

3. **Code duplication** - async/sync preload services have identical logic

---

## Additional Commits (Post-Initial Review)

### `7cd3f4eb` refactor(rotation): rename activity_type to rotation_type
- **180 files changed, 1086 insertions, 1012 deletions**
- Complete rename of `activity_type` → `rotation_type` across entire codebase
- Alembic migration: `20260126_rename_rotation_type`
- Includes docs, tests, schemas, models, and all references
- **Note:** Priority list item #22 is now RESOLVED by this commit

### `97782b1b` fix(activity-solver): align SM only for sm_clinic
- Fixed Sports Medicine alignment constraint
- Before: Any activity for SM resident counted toward SM presence
- After: Only `sm_clinic` activity counts for alignment
- Added `_should_count_sm_resident_presence()` helper method
- Test coverage added

### `d9a3a0d2` docs(block10): record CP-SAT regen failure
- Documents Block 10 generation failure
- CP-SAT returned **INFEASIBLE**
- Created `BLOCK_REGEN_RUNBOOK.md` with pre-flight checks

---

## CRITICAL: Block 10 CP-SAT Infeasibility

**Status:** INFEASIBLE - solver cannot find valid schedule

**Root Cause (from `block10-cpsat-run-20260126.md`):**
```
PCAT or DO templates not found - post-call constraint inactive
NF or PC templates not found - Night Float post-call constraint inactive
CP-SAT solver status: INFEASIBLE
```

**Missing Templates:**
| Template | Count | Impact |
|----------|-------|--------|
| PCAT | 0 | Post-call constraint inactive |
| DO | 0 | Post-call constraint inactive |
| SM | 0 | Sports Medicine alignment broken |

**Result:**
- Only 202 preloads remain (out of expected ~1500 assignments)
- 0 call assignments generated
- 750 empty slots in export

---

## Uncommitted Work In Progress

Found uncommitted changes that appear to be fixes for the infeasibility:

### `post_call.py` - Template Lookup Fix
```python
# Accept AM/PM suffix variants (e.g., PCAT-AM, DO-PM) for post-call templates.
if target in {"PCAT", "DO"}:
    for t in context.templates:
        if name.startswith(target) or abbrev.startswith(target):
            return t.id
```

### `engine.py` - Constraint Disabling for Half-Day Blocks
```python
# Disables constraints that cause infeasibility:
self.constraint_manager.disable("OnePersonPerBlock")
self.constraint_manager.disable("1in7Rule")
self.constraint_manager.disable("80HourRule")
self.constraint_manager.disable("MaxPhysiciansInClinic")
self.constraint_manager.disable("WednesdayAMInternOnly")
self.constraint_manager.disable("ProtectedSlot")
```

**⚠️ CONCERN:** Disabling `1in7Rule` and `80HourRule` removes ACGME compliance constraints. These should only be disabled if the half-day solver truly cannot affect those rules (e.g., if they're enforced elsewhere).

---

## Recommendation

**Before merge:**
1. ✅ Verify `rotation_type` rename migration runs cleanly
2. ⚠️ Seed PCAT/DO/SM templates in database
3. ⚠️ Review constraint disabling in `engine.py` - is disabling ACGME rules safe?
4. Re-run Block 10 generation after template seeding
5. Commit the WIP changes (`post_call.py`, `engine.py`) after review

**Post-merge:**
- Extract duplicated preload pattern logic (follow-up PR)
- Document which constraints are disabled and why

The preload infrastructure is well-designed and properly tested. The OKI pattern assumption (same as Hilo) should be validated with program staff.

---

## Logging Failure Recommendations

The Block 10 infeasibility was difficult to diagnose because failures were logged at INFO level without actionable context. Recommendations:

### 1. Template Lookup Failures → WARNING with Context

**Current:**
```python
logger.info("PCAT or DO templates not found - post-call constraint inactive")
```

**Recommended:**
```python
logger.warning(
    "PCAT/DO templates not found - post-call constraint INACTIVE. "
    "Searched for abbreviations: ['PCAT', 'DO']. "
    "Available templates: %s. "
    "Run: SELECT abbreviation FROM rotation_templates WHERE abbreviation IN ('PCAT', 'DO')",
    [t.abbreviation for t in context.templates[:10]]  # First 10 for brevity
)
```

### 2. Solver INFEASIBLE → ERROR with Constraint Summary

**Current:**
```python
logger.info(f"CP-SAT solver status: {status}")
```

**Recommended:**
```python
if status == cp_model.INFEASIBLE:
    logger.error(
        "CP-SAT solver INFEASIBLE for block %d AY%d. "
        "Active constraints: %s. "
        "Disabled constraints: %s. "
        "Preloads: %d, Slots to fill: %d. "
        "Check: (1) Missing templates, (2) Over-constrained preloads, (3) Insufficient residents",
        block_number,
        academic_year,
        self.constraint_manager.active_constraints(),
        self.constraint_manager.disabled_constraints(),
        preload_count,
        total_slots - preload_count,
    )
```

### 3. Constraint Disabling → WARNING Always

**Current:**
```python
self.constraint_manager.disable("1in7Rule")
logger.info("Disabled 1in7Rule...")
```

**Recommended:**
```python
self.constraint_manager.disable("1in7Rule")
logger.warning(
    "ACGME constraint '1in7Rule' DISABLED for half-day solver. "
    "Reason: No time-off templates in context. "
    "Compliance must be enforced elsewhere or templates must be added."
)
```

### 4. Pre-flight Check Failures → Structured Output

Add a pre-flight validation step that logs all missing prerequisites:

```python
def _log_preflight_status(self, context: SchedulingContext) -> None:
    """Log preflight check results for debugging."""
    required_templates = {"PCAT", "DO", "NF", "SM"}
    found = {t.abbreviation for t in context.templates if t.abbreviation}
    missing = required_templates - found

    if missing:
        logger.warning(
            "PREFLIGHT: Missing templates: %s. "
            "Generation may fail or produce incomplete results.",
            sorted(missing)
        )

    if not context.residents:
        logger.error("PREFLIGHT: No residents in context - cannot generate schedule")

    if not context.call_slots:
        logger.warning("PREFLIGHT: No call slots defined - call assignments will be empty")
```

### 5. Export Failures → Include Row Mapping Debug

```python
if person_name not in row_mapping:
    logger.error(
        "EXPORT FAILED: No row mapping for '%s'. "
        "Available mappings: %s. "
        "Check: (1) Person exists in DB, (2) Name format matches (First Last vs Last, First)",
        person_name,
        list(row_mapping.keys())[:5]  # First 5 for brevity
    )
    raise ExportError(f"Missing row mapping for {person_name}")
```

### Summary Table

| Scenario | Current Level | Recommended Level | Key Addition |
|----------|---------------|-------------------|--------------|
| Template not found | INFO | WARNING | List available templates |
| Solver INFEASIBLE | INFO | ERROR | Active/disabled constraints |
| Constraint disabled | INFO | WARNING | Reason + compliance note |
| Missing preflight | (none) | WARNING/ERROR | Structured checklist |
| Export row missing | WARNING | ERROR + raise | Available mappings |

### Implementation Priority

1. **P0:** Solver INFEASIBLE → ERROR with context (most impactful)
2. **P1:** Template lookup → WARNING with available templates
3. **P2:** Constraint disabling → WARNING with reason
4. **P3:** Preflight validation (new function)
5. **P3:** Export row mapping debug
